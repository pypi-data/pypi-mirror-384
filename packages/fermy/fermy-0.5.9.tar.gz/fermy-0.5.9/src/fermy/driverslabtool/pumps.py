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

from labjack import ljm  # To solve it: python -m pip install labjack-ljm
import datetime
import math


class PompWatMarlo:
    """Class that connect and drive a Watson Marlow pump 120U plus head 114DV connect to
    a computer through a labjack T7
    connection DAC0:pin 2 GND:pin10 AIN0:pin9 GND:pin3
    link 4-20mA pin 1--11
    """
    def __init__(self):
        """Initialisation"""
        self.setpoint = 0
        self.rpm = 0
        self.connection = False
        self.info = None
        self.time = datetime.datetime.now()
        self.vdc_input = 0
        self.tensionread = 0
        #Calibration
        self.tachyA = 0.025
        self.tachyB = 0.0065
        self.rpmmax = 200
        self.rpmvdcA = 41.754
        self.rpmvdcB = -50.805
        self.limvdcsup = 3.75
        self.rpmvdcAsup = -27.73
        self.rpmvdcBsup = +253.84
        self.rpmvdcCsup = -456.79
    
    def __str__(self):
        """Define printing method print(object)"""
        return f"Pompe connection = {self.connection}\nlast read: {self.time} : {self.rpm}\nsetpoint {self.setpoint}"
        
    def polysecdeg_inv(self, y, a, b, c):
        """Quadratic function (y = a*x**2 + b*x + c ) solved with method of Completing the Squares
        Vertex = point of swapping domain Vertex(h,k)
        h from x
        k from y
        """
        s1 = -(b/(2*a))-math.sqrt(y/a-c/a+(b/(2*a))**2)
        s2 = (-b/(2*a))+math.sqrt(y/a-c/a+(b/(2*a))**2)
        h = -b/(2*a)
        k = c-a*(b/(2*a))**2
        if y < k:
            return s1
        elif y==k:
            return h
        else:
            return s2
    
    def rpmtovdc(self, rpm):
        """Convert RPM setpoint to VDC
        With safty VDC max = 5.0V et VDCmin = 0.0V
        RPM = VDC*rpmvdcA + rpmvdcB
        or
        RPM = rpmvdcAsup*VDC**2 + rpmvdcBsup*VDC + rpmvdcCsup
        """
        if rpm == 0:
            VDC = 0
        else:
            if ((rpm-self.rpmvdcB)/self.rpmvdcA) <= self.limvdcsup:
                VDC = (rpm-self.rpmvdcB)/self.rpmvdcA
                #print("lin")
            else:
                k = (self.rpmvdcCsup-self.rpmvdcAsup*(self.rpmvdcBsup/(2*self.rpmvdcAsup))**2)
                print(f"not linear part, near pump maximum communication capacity close to {int(k)} rpm\n")
                if rpm > k: #RPM > k
                    print("Warning Maximum pump communication capacity !\n")
                    VDC = -self.rpmvdcBsup/(2*self.rpmvdcAsup)  # VDC = h
                else:
                    VDC = self.polysecdeg_inv(rpm, self.rpmvdcAsup, self.rpmvdcBsup, self.rpmvdcCsup)
            if VDC > 5:
                VDC = 5
            if VDC <0:
                VDC = 0
        return VDC
        
    def tachyread(self, vdc):
        """Convrpmert read vdc to rpm value
        with RPMmax = 200
            self.tachyA = 0.025
            self.tachyB = 0.0066
        VDC = tachyA*RPM + tachyB
        RPM = (VDC-tachyB)/tachyA
        """
        rpm_tachy = (vdc-self.tachyB)/ self.tachyA
        return rpm_tachy
        
    def startcom(self):
        """Srat connection with the labjack
        """
        if self.connection == False:
            self.handle = ljm.openS("T7", "ANY", "ANY")
            self.info = ljm.getHandleInfo(self.handle)
            self.connection = True
            print(f"You play with the {self.info[1]} Labjack T{self.info[0]}")
        else:
            print("Already connected")

    def stopcom(self):
        """Stop connection
        """
        if self.connection == True:
            ljm.eWriteName(self.handle, "DAC0", 0)  #clear output
            ljm.close(self.handle)
            self.connection = False
        else:
            print("Not connected")
    
    def readrpm(self):
        """Give RPM from vdc read in pin AIN0
        """
        if self.connection:
            self.rpm = self.tachyread(ljm.eReadName(self.handle, "AIN0"))
            self.time = datetime.datetime.now()
            return self.rpm, self.time
        else:
            print('Please first used .startcom()')
            
    def update(self):
        """send setpoint to pump
        """
        if self.connection:
            vdc_input = self.rpmtovdc(self.setpoint)
            LJMError = ljm.eWriteName(self.handle, "DAC0", vdc_input)  # put 3V into DAC0 output
            if LJMError:
                print(f"Error n°{LJMError}")
        else:
            print('Please first used .startcom()')
            
    def updatev(self, newsetpoint):
        """send setpoint to pump with spe setpoint
        """
        if self.connection:
            self.setpoint = newsetpoint
            vdc_input = self.rpmtovdc(self.setpoint)
            LJMError = ljm.eWriteName(self.handle, "DAC0", vdc_input)  # put V into DAC0 output
            if LJMError:
                print(f"Error n°{LJMError}")
        else:
            print('Please first used .startcom()')

    def updatetension(self, tension):
        """send setpoint to pump with setpoint in tension
        """
        if self.connection:
            vdc_input = tension
            LJMError = ljm.eWriteName(self.handle, "DAC0", vdc_input)  # put 3V into DAC0 output
            if LJMError:
                print(f"Error n°{LJMError}")
        else:
            print('Please first used .startcom()')
            
    def readtension(self):
        """Give tension in pin AIN0
        """
        if self.connection:
            self.tensionread = ljm.eReadName(self.handle, "AIN0")
            return self.tensionread
        else:
            print('Please first used .startcom()')
            
            
    def changerpmmax(self, rpmmax):
        """Change conv VDC to rpm calib
        self.rpmvdcA = 20.161
        self.rpmvdcB = -0.9726
        """
        if rpmmax == 200:
            self.rpmvdcA = 41.754
            self.rpmvdcB = -50.805
            self.limvdcsup = 3.75
            self.rpmvdcAsup = -27.73
            self.rpmvdcBsup = +253.84
            self.rpmvdcCsup = -456.79
            self.rpmmax = 200
            self.tachyA = 5/rpmmax
            self.tachyB = 0.0065
        elif rpmmax == 100:
            self.rpmvdcA = 20.858
            self.rpmvdcB = -25.366
            self.limvdcsup = 3.75
            self.rpmvdcAsup = -12.641
            self.rpmvdcBsup = 116.66
            self.rpmvdcCsup = -207.07
            self.rpmmax = 100
            self.tachyA = 5/rpmmax
            self.tachyB = 0.0065
        elif rpmmax == 50:
            self.rpmvdcA = 10.441
            self.rpmvdcB = -12.729
            self.limvdcsup = 3.75
            self.rpmvdcAsup = -6.0165
            self.rpmvdcBsup = 56.116
            self.rpmvdcCsup = -99.569
            self.rpmmax = 50
            self.tachyA = 5/rpmmax
            self.tachyB = 0.0065
        elif rpmmax == 25:
            self.rpmvdcA = 5.2188
            self.rpmvdcB = -6.3899
            self.limvdcsup = 3.75
            self.rpmvdcAsup = -3.1334
            self.rpmvdcBsup = 28.877
            self.rpmvdcCsup = -51.131
            self.rpmmax = 25
            self.tachyA = 5/rpmmax
            self.tachyB = 0.0065
        else:
            print(f"{rpmmax}rpm MAX not avaiable\nPlease realise new calibration.\nWith help of .readtension/.readrpm.")
