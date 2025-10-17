"""
Created the 2022/10/04
v0.1 First version
v0.2 Bugfix with Epoch2 and fakedata name
v0.3 add Tecan reader 96 and 384
v0.4 add Logphase600 96 BioTek & add exclusion of rows with nan
v0.5 bug fix for method .applymap to .map in fuction readepochtwo ==> need Pandas > 2.1
v0.6 optimize readepochtwo to skip the end of the file by finding result instead of fixed value 
v0.7 add Fluostar Omega or Optima / add bug fix for Tecan when column missing
v0.8 add index name as "Time" for Fluostar and minor fix for convfluostartohours
v0.9 add maptoserie function
v1.0 add maptoserie with zero as method
v1.1 add Tecan 1536  and merge tecan function to one general function
v1.2 add new way for Tecan to found end of dataset
v1.3 upgrade read of function convfluostartohours 
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

__version__ = 1.3

import pandas as pd
from typing import List, Dict, Iterable, Tuple, Union
import math

class MTPError(Exception):
    def __init__(self, message):
        super().__init__(message)



class MTPReader():
    """Class that allow to read MTP data need filepath and readername
    """
    
    def __init__(self, filepath:str, readername:str):
        """Initialisation of reader
        """
        self.readername = readername
        self.plate = pd.DataFrame()
        self.filepath = filepath
        self.dicoreader = {"Epoch2" : self.readepochtwo,
                            "fakeMTP" : self.readfakemtp,
                            "Tecan" : self.readtecan,
                            "Logphase" : self.readlogphasesixhundr,
                            "Fluostar" : self.readfluostar
                            } # linker between MTP and reading function
    
    def convstringtohours(self, string: str) -> float:
        """"Function to transform a string like hours:minutes:seconds
        or aaa-mm-dd hh:mm:ss to a float of hours
        return float
        """
        if len(string.split(" ")) == 1:
            spliting = string.split(':')
            timefloat = float(spliting[0])+float(spliting[1])/60+float(spliting[2])/3600
        else:
            spliting = string.split(" ")
            timefloat = float(spliting[0].split('-')[2])*24
            timefloat = timefloat + float(spliting[1].split(':')[0])
            timefloat = timefloat + float(spliting[1].split(':')[1])/60
            timefloat = timefloat + float(spliting[1].split(':')[2])/3600
        return timefloat
    
    def convfluostartohours(self, string: str) -> float:
        """"Function to transform a string like hours:minutes
        or H h M min
        or M min
        to a float of hours
        return float
        """
        timefloat = 0.
        if "h" in string:
            spliting = string.split("h")
            for data in spliting:
                if "min" in data:
                    timefloat += float(data.strip(" min"))/60
                elif data.strip(" ") != "":
                    timefloat += float(data.strip(" "))
        elif "min" in string:
            timefloat += float(string.strip(" min"))/60
        elif ":" in string:
            spliting = string.split(":")
            if len(spliting) == 3:
                timefloat += float(spliting[0])
                timefloat += float(spliting[1])/60
                timefloat += float(spliting[2])/3600
        else:
            timefloat += 0.
        return timefloat
    
    def buildrenamer(self, inputdata:Union[None,List] = None,switch:int=0) -> Dict:
        """Function to build a MTP 96 well renamer
        return dico
        """
        dicorenamer = {}
        if inputdata != None:
            index = 0
            for line in ["A", "B", "C","D", "E", "F", "G", "H"]:
                for column in range(1,13):
                    dicorenamer[inputdata[index]] = f"{line}{column}"
                    index +=1
            return dicorenamer
        else:
            index = 0 + switch
            for line in ["A", "B", "C","D", "E", "F", "G", "H"]:
                for column in range(1,13):
                    dicorenamer[index] = f"{line}{column}"
                    index +=1
            return dicorenamer
    
    
    def readepochtwo(self) -> pd.DataFrame:
        """Function to return formated dataframe from reader Epoch
        index is time float in hours
        """
        
        rawtable = pd.read_excel(self.filepath, sheet_name=0)
        numline = int(rawtable[rawtable["Unnamed: 0"]=="Layout"].index.values) +2
        numfin = int(rawtable[rawtable["Unnamed: 0"]=="Results"].index.values)
        filefin = len(rawtable.index)+1
        endskipe = filefin-numfin
        
        del rawtable
        tabledata = pd.read_excel(self.filepath, sheet_name=0, index_col=None, skiprows=numline+13, skipfooter=endskipe, dtype={"Time":str}).iloc[:,1:]  #data robot
        tabledata["Time"] = tabledata["Time"].apply(self.convstringtohours)  # converrt time from hh:mm:ss to float
        tabledata.index = tabledata["Time"] - tabledata["Time"].iloc[0] # set index start from time 0.0 h
        tabledata.drop(["Time", "T° 600","T°598"], axis=1, inplace=True, errors = "ignore")  # Drop Time columns
        tabledata = tabledata.map(lambda data: data.strip("*") if isinstance(data, str) else data)  # clean *
        tabledata = tabledata.astype('float64')
        tabledata.dropna(axis=0, how="all", subset=tabledata.columns[2:], inplace=True)  # clear empty data
        tabledata.index.name = "Time"
        return tabledata
    
    def readtecan(self) -> pd.DataFrame:
        """Function to return formated dataframe from reader Tecan
        index is time float in hours
        """
        rawtable = pd.read_excel(self.filepath, sheet_name=0, usecols=[0,1])  # read only first two columns
        numlinedata = int(rawtable[rawtable.iloc[:,0] == "Cycle Nr."].index.values[0])
        #numlineenddata = int(rawtable[rawtable.iloc[:,0] == "End Time"].index.values[-1])
        #numlineendtoskip = rawtable.index.max() - numlineenddata + 2
        del rawtable
        tabledata = pd.read_excel(self.filepath, sheet_name=0, index_col=None, skiprows=numlinedata+1)#, skipfooter=numlineendtoskip)
        #tabledata.dropna(axis=0,how="any",subset="Temp. [°C]", inplace=True) # option 1 base on column "Temp [°C]"
        #detect end of data base first full N.A. raw option 2
        try:
            tabledata[tabledata.isna().all(axis=1) == True].index[0] # found N.A. raw if exist
        except:
            tabledata # do nothing if not
        else:
            endofdataindex = tabledata[tabledata.isna().all(axis=1) == True].index[0]
            tabledata = tabledata.iloc[:endofdataindex,:].copy() # skip raw after first only N.A. raw
        tabledata["Time"] = tabledata["Time [s]"]/3600 # conversion to hours
        tabledata.index = tabledata["Time"]  # set time as index
        tabledata.drop(["Time", "Temp. [°C]", "Time [s]","Cycle Nr."], axis=1, inplace=True, errors = "ignore")  # Drop Time columns
        return tabledata
    
    def readlogphasesixhundr(self) -> pd.DataFrame:
        """Function to return formated dataframe from Logphase600
        from BioTek Agilent
        index is time float in hours
        """
        with open(self.filepath,"r") as filetemp:
            lines = filetemp.readlines()
            indexfile = 0
        for line in lines:
            if "Time\t" in line:
                numline = indexfile
                # print(f"{indexfile} in ''{line}'")
            indexfile += 1
        tabledata = pd.read_csv(self.filepath, skiprows=numline, encoding='cp1252', sep="\t", skip_blank_lines=True, decimal=",")
        tabledata.index = tabledata["Time"].apply(self.convstringtohours)  # converrt time from hh:mm:ss to float
        tabledata.drop(["Time"], axis=1, inplace=True, errors = "ignore")  # Drop Time columns
        return tabledata
        
    def readfakemtp(self) -> pd.DataFrame:
        """Function to return a fake formated dataframe
        """
        # time 5 minutes steps in hours for 6 hours
        time = [time/60 for time in range(0, 60*6, 5)]
        lagtime = time[20]  # 1.66 h
        fakedataset = [0.01]*20+[0.01*math.exp(0.5*(time-lagtime)) for time in time[20:]]
        datadico = {}
        for line in ["A", "B", "C","D", "E", "F", "G", "H"]:
            for column in range(1,13):
                datadico[f"{line}{column}"] = fakedataset
        tabledata = pd.DataFrame(data= datadico, index=time)
        tabledata.index.name = "Time"
        return tabledata
    
    def readfluostar(self) -> pd.DataFrame:
        """Function to return formated dataframe from Fluostar Optima
        or Omega
        index is time float in hours
        """
        rawtable = pd.read_excel(self.filepath, sheet_name=0)
        wellindex = rawtable[rawtable.iloc[:,0] == "Well"].index.to_list()
        if len(wellindex) == 1:
            numlinedata = int(wellindex[0])
            numcoldata = 2
            stringtimesep = ":"
        elif wellindex == []:
            wellindex = rawtable[rawtable.iloc[:,0] == "Well\nRow"].index.to_list()
            if len(wellindex) == 1:
                numlinedata = int(wellindex[0])
                numcoldata = 3
                stringtimesep = ["h","min"]
            else:
                raise MTPError(f"Corrupted file {self.filepath}")
        del rawtable
        tabledata = pd.read_excel(self.filepath, sheet_name=0, skiprows=numlinedata+2).iloc[:,numcoldata:].T
        tabledata.index = tabledata.index.to_series().apply(str).apply(self.convfluostartohours)
        tabledata.rename(columns=self.buildrenamer(tabledata.columns.to_list()), inplace=True)
        tabledata.index.name = "Time"
        return tabledata
    
    def readMTP(self) -> pd.DataFrame:
        """Load a file and provide a formated DataFrame
        """
        #read the input file if the reader name is known 
        if self.readername in self.dicoreader.keys():
            try:
                self.plate = self.dicoreader[self.readername]()
            except Exception as err:
                raise MTPError(f"Wrong device '{self.readername}' or corrupted file")
        self.plate.dropna(axis=0, how="any", inplace=True) # clean row with missing data (useless)
        return self.plate
    
    def readerslist(self) -> List[str]:
        """Provide the names of readers avaible
        """
        listofreaders = list(self.dicoreader.keys())
        return listofreaders
        
    def __str__(self):
        return f"The MTP reader is set as {self.readername}\nThe path of data file is {self.filepath}\nOther avaible readers {list(self.dicoreader.keys())}"


def maptoserie(dataframe: pd.DataFrame, forcezero=False) -> pd.Series:
    """Read plate map 96 wellplate per well
    from a dataframe with numbe 1-12 as column name and letter A:F as index
    In a simple Excel File: pd.read_excel(path,index_col=0,header=0)
    return a pd.serie with coord (e.g. A10) as index and name of well as value
    forcezero = True >> A1 => A01
    """
    newindex = []
    newvalue = []
    for raw, cols in dataframe.iterrows():
        for col in cols.index:
            if forcezero:
                if col <10:
                    newindex.append(f"{raw}0{col}")
                    newvalue.append(cols[col])
                else:
                    newindex.append(f"{raw}{col}")
                    newvalue.append(cols[col])
            else:
                newindex.append(f"{raw}{col}")
                newvalue.append(cols[col])
    labelserie = pd.Series(data=newvalue,index=newindex)
    return labelserie

pd.core.base.PandasObject.maptoserie = maptoserie # monkey-patch the DataFrame class to add maptoserie method
