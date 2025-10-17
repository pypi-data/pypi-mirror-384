"""
Created the 2021/10/08
v0.0 First version

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

print("Drivers loaded. You can use fermy.driverslabtool.pumps \
or fermy.driverslabtool.scale or fermy.driverslabtool.probs or fermy.driverslabtool.MTP to access to it.")
from . import probes
from . import pumps
from . import scales
#from . import MTP
from . import errorslabtools
