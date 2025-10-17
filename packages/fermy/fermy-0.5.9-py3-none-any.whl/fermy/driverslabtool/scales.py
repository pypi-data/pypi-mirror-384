"""
Created the 2020/03/16
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

import serial
import datetime


class BalanceEntris:
    """Class that connect and drive a balance Sartorius Entris or Entris II
    from COM port
    To find it #python -m serial.tools.list_ports
    """
    def __init__(self, portcom, baudrate=9600, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN,stopbits=serial.STOPBITS_ONE): #notre méthode de construction
        """Initialisation from port COM"""
        self.portcom = portcom
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.time = datetime.datetime.now()
        self.mass = 0.0
        self.rawmass = b""
        self.connection = False
        self.tarevalue = 0
        
    def __str__(self):
        """Define printing method print(object)"""
        return f"Balance connection = {self.connection}\nlast read: {self.time} : {self.mass}"
    def startcom(self):
        """Srat connection with the balance
        """
        if self.connection == False:
            self.ser = serial.Serial(self.portcom, baudrate=self.baudrate, bytesize=self.bytesize, parity=self.parity, stopbits=self.stopbits)
            self.connection = True
        else:
            print("Already connected")
        
    def stopcom(self):
        """Stop connection
        """
        try:
            self.ser.close()
        except Exception as err:
            print("Not connected")
        else:
            self.ser.close()
            self.connection = False
        
    def rawmasstovalue(self, rawmass):
        """Simple function to convert byte to float
        """
        strmass = str(rawmass)
        gindex = strmass.find("g")
        if gindex == -1:
            gindexunstable = strmass.find(".")
            if gindexunstable == -1:
                print(f"reading issue com {strmass}")
            else:
                print("unstable weight")
                strmassshort = strmass[gindexunstable-4:gindexunstable+3]
        else:
            strmassshort = strmass[gindex-8:gindex]
        try:
            float(strmassshort)
        except:
            print(f"issue float conv {strmass}")
            mass = self.mass
            return mass
        else:
            mass = float(strmassshort)
            if strmass.find("+")==-1:
                if strmass.find("-")==-1:
                    return mass
                else:
                    return -mass
            else:
                return mass
        
    def weight(self):
        """return the mass and date
        """
        if self.connection:
            self.ser.write(b"P\r\n")
            self.rawmass = self.ser.readline() # line = ser.readline() or self.ser.read(16)   # read a '\n' terminated line or read(100)
            self.mass = self.rawmasstovalue(self.rawmass)
            self.time = datetime.datetime.now()
            return self.mass, self.time
        else:
            print('Please first used .startcom()')
    
    def tare(self):
        """Set tare of the balance
        """
        if self.connection:
            self.ser.write(b" P\r\n")
            self.rawmass = self.ser.readline()
            self.tarevalue = self.rawmasstovalue(self.rawmass)
            self.ser.write(b" T\r\n")
            print(f"Tare done with {self.tarevalue}g")
        else:
            print('Please first used .startcom()')
