"""
Created the 2022/09/28
v0.1 First version
@author: Nicolas Hardy

This file is part of Fermy.

    Fermy is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Fermy is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Fermy.  If not, see <https://www.gnu.org/licenses/>.
"""
__version__ = 0.1

import minimalmodbus
import datetime
from typing import List, Dict, Iterable, Tuple, Union
from . import errorslabtools


class M80:
    """Class that connect and drive a Mettler Toledo sensor mount
    transmitter connected to a PC with an USB/RS485 convertor
    Material.
    M80-SM transmietter 30530566
    5-pin data cable 2m 52300379
    USB/Rs485 e.g. SB485 Papouch Term485 On and SW4 On
    24V power supply e.g. MeanWell DR-15-24
    
    Wiring
    Open calbe end = function = connected to
    Brown = 24 VDC+ = positive output pin of the power supply
    black = 24 VDC- = negative output pin of the power supply
    blue = RS485- (B) = RxTx- pin of USB converter
    white = Rs485+ (A) = RxTx+ pin of USB converter
    gray = groud = groud pin of USB converter
    yellow = shield = connection to earth (power supply)
    
    from COM port information it is possible to find it with "pyserial" tool #python -m serial.tools.list_ports
    """
    def __init__(self, portcom, deviceaddress, baudrate: int=38400, bytesize: int=8,
                parity:str=minimalmodbus.serial.PARITY_NONE,
                stopbits:int=1, timeout: float=0.1): #Our construction method
        """Initialisation from port COM"""
        self.portcom = portcom
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self.deviceaddress = deviceaddress
        self.connection = False
        self.instrument = None
        self.time = datetime.datetime.now()
        self.M1 = None
        self.M2 = None
        self.M3 = None
        self.M4 = None

    def stopcom(self):
        """Stop connection
        """
        try:
            self.instrument.serial.close() # stop the communication
        except Exception as err:
            raise errorslabtools.CommunicationError("Not connected\nPlease connect an instrument first with .startcom()")
        else:
            self.instrument.serial.close() # stop the communication
            self.connection = False
            print("Disconnection")
            
    def startcom(self):
        """Srat connection with the balance
        """
        if self.connection == False:
            try:
                self.instrument = minimalmodbus.Instrument(self.portcom, self.deviceaddress, mode="rtu")  # port name, slave address (in decimal) 49 for TQS4
            except IOError: # or Exception as err: ?
                raise errorslabtools.CommunicationError(f"No device answer probably due to a wrong port name ({self.portcom}).")
            else:
                self.instrument.serial.baudrate = self.baudrate
                self.instrument.serial.bytesize = self.bytesize
                self.instrument.serial.parity   = self.parity
                self.instrument.serial.stopbits = self.stopbits
                self.instrument.serial.timeout  = self.timeout        # in seconds
                self.instrument.clear_buffers_before_each_transaction = True
                self.connection = True
            self.testaddress()
        else:
            print("Already connected")

    def __str__(self) -> str:
        """Define printing method print(object)"""
        return f"M80 connection = {self.connection}\nM80 device address {self.deviceaddress} \
        \nlast read: {self.time}\nLast values {self.M1, self.M2, self.M3, self.M4}"
    
    def testaddress(self) -> bool:
        """Method to test if a device is connected
        at the requested address
        """
        if type(self.instrument) == minimalmodbus.Instrument:
            try:
                comok = self.instrument.read_register(0)
            except IOError: # or Exception as err: ?
                raise errorslabtools.CommunicationError(f"No device answer probably due to a wrong slave address {self.deviceaddress}")
            else:
                comok = self.instrument.read_register(0)
                if comok == 0:
                    print(f"A device is avaible with address {self.deviceaddress}")
                    return True
                else:
                    print("Please connect an instrument first with .startcom()")
    
    def read(self)-> Dict:
        """read all channels of the connected probe with reading datetime
        and return a Dict with  {"time","M1", "M2", "M3", "M4"}
        """
        if self.connection:
            self.time = datetime.datetime.now()
            try:
                self.M1 = self.instrument.read_float(100) # read mesurment M1 for me pH (Cf. doc p28)
                self.M2 = self.instrument.read_float(102) # read mesurment M2 for me °C
                self.M3 = self.instrument.read_float(104) # read mesurment M3 for me Volts (pH)
                self.M4 = self.instrument.read_float(106) # read mesurment M4 for me ORP (V)
            except IOError:
                raise errorslabtools.CommunicationError("No able to read the prob please check connection.")
            else:
                print(f"time: {self.time}\nM1: {self.M1}\nM2: {self.M2}\nM3: {self.M3}\nM4: {self.M4}\n")
                return {"time": self.time,
                        "M1" : self.M1,
                        "M2" : self.M2,
                        "M3" : self.M3,
                        "M4" : self.M4,
                        }
        else:
            print('Please first used .startcom()') 
            return {}
