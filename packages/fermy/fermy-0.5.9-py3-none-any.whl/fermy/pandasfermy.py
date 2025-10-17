"""
Created the 2021/10/08
v0.0 First version
v0.1 Update graph by line instead of scatter
v0.2 add multirenaming option
v0.3 naming fix from plotyfermy compatibility
v0.4 add time slice option to fanodygrowth function
v0.5 add method to average replicates
v0.6 bug fix for replicates
v0.7 add EGRA % max slope option / add max OD to fermgrowth
v0.8 replace groupeby axis = 1 per .T
==> next step add minimal DeltaBiomassProxy for fanodygrowth function
==> next step calcul max Proxxy at max slope
    if dfslope.min()<limite:
            indexODmaxslope = dfslope.loc[dataafterslope<=0.005].first_valid_index()
==> next step: add slope calculation method as pandas method

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

__version__ = 0.8


import pandas as pd
import numpy as np
from typing import List, Dict, Iterable, Tuple, Union
import os
import datetime
import argparse

from fermy.log import logger

def linearareaselection(data: pd.Series, percent: float=0.95) -> pd.Series:
    """"Function to return series that map best lineare area
    return the table wiht na or slope. slopes area where it is linear
    """
    maxslope = data.max() * percent
    return data.where(data>maxslope).dropna()

def EGRAdataselection(data: pd.Series, originaldataset: pd.DataFrame) -> pd.Series:
    """Function to return series that map with EGRA
    return orginialdataset filter by non na data values
    """
    EGRA = originaldataset[data.name].loc[data.dropna().index]  #select data from smooth data matching with EGRA
    return EGRA

def normalizedata(data: pd.Series, regardingmax:bool=True, percentofmax:float=0.05, numberofpointformin:int=5) -> pd.Series:
    """Function to normilized by the average value of first five points not null
    or if regardingmax = True: normilized by percentofmax of maximum value
    if data is low than normalized value put it at 1
    """
    if regardingmax:
        logger.info("By using max for normalization\n growth rate estimation will be more robust\nwhereas lag time will no more have meaning")
        #print("By using max for normalization\n growth rate estimation will be more robust\nwhereas lag time will no more have meaning")
        normalvalue = data.max() * percentofmax
        normalizeddata = data/normalvalue
    else:
        normalvalue = data.replace(to_replace=0, value=np.nan).dropna().iloc[:numberofpointformin].mean()
        normalizeddata = data/normalvalue
    normalizeddata = [1 if valeur < 1 else valeur for valeur in normalizeddata]  # if value <1 replace it by 1
    return normalizeddata

def reglin(valuesx: np.ndarray, valuesy: np.ndarray, slopeonly=False) -> Union[float, List[float]]:
    """Minimal linear regression with numpy. You can set slopeonly at True
    to return only slope else return both
    """
    slope, intercept = np.polyfit(valuesx, valuesy, 1)  # deg 1: ax+b
    if slopeonly:
        return slope
    else:
        return [float(slope), float(intercept)]

def calcslope(data: pd.Series, slopeonly=True) -> Union[float, List[float]]:
    """Function to compute slope from a Serie
    return slope or list with slope and intercept
    """
    data.dropna(inplace=True)
    slope = reglin(data.index.values, data.values, slopeonly=slopeonly)
    return slope

def localmax(data: pd.DataFrame) -> pd.Series:
    """Function to found local max of slopes
    """
    peak_df = data[(data.shift(1) < data) & (data.shift(-1) < data)]
    return peak_df


def multireg(data: pd.Series, windows: float=5)-> List[float]:
    """Function to list mu (slope) and lagtime (-intercepts/slope)
    return list of mu, list of lagtime and list of time to mu
    need series and index of slopes
    """
    indexlocalmax = (
            data
            .rolling(5, center=True).apply(calcslope)  # compute rolling slope
            .rolling(windows, center=True).mean()  # smooth to reduce local maximum number
            .to_frame()  # trick because local comput only on DF
            .apply(localmax)
            .dropna().index # Local max index
            )
    listmu = []
    lagtime = None
    firstlagtimeflag = True  #to know if it is the first lagtime
    for slopeindex in indexlocalmax:
        indexlist = []
        slopeindexnum = data.index.get_loc(slopeindex)
        for switchtnum in range(-2,3):
            indexlist.append(slopeindexnum+switchtnum)
        x, y = data.iloc[indexlist].index, data.iloc[indexlist].values
        listmu.append(round(reglin(x,y)[0],2))
        if firstlagtimeflag:
            lagtime = round(-reglin(x,y)[1]/reglin(x,y)[0],2)
            if lagtime:
                firstlagtimeflag = False  # Check if lagtime exist
    return [listmu, lagtime, [round(time, 2) for time in indexlocalmax.to_list()]]



def selectdatawithminidelta(data: pd.Series, deltathreshold: float) -> pd.Series:
    """"Function to return DataFrame that have at least deltathreshold
    by comparing min and max in column if not or an empty dataseries
    """
    if data.max()-data.min() > deltathreshold:
        return data
    else:
        return pd.Series(data=np.nan, index=data.index, name=data.name)



def fanodygrowth(data: pd.DataFrame, percentofmax:float=0.05, usemax:bool=False, timethreshold:Union[None, float]=None, deltathreshold:Union[None, float]=None , percentegra:float=0.95) -> pd.DataFrame:
    """Function to compute growth rate and lagtime
    It is based on a mix of two algorithms describes in the following:
    Toussaint et al. 2006 and Hall et al. 2014.
    
    Input:
    -----
    A DataFrame with only data considered as proxy of biomass can be used.
    DataFrame index has to be a float corresponding to
    a delta time (in hours) or pandas.DatetimeIndex
    
    Parameters:
    ----------
    usemax: allow users to choose between normalization methods:
            average of the first five points
            or 
            percentage of the maximal value of dataset
    
    percentofmax: allow users to change the percentage of
            maximal value used
    
    timethreshold: allow users to compute growth rate without
            considering data from time before
            the provided number of hours
    
    deltathreshold: allow users to exclude data without a minimal
                Biomass proxy delta between min and max of the column.
    
    percentegra: allow users to change the % used to select the
                relevent slope area (EGRA) variation of max slope
                by default 95% (0.95) of max slope
    
    Output:
    ------
    return a DataFrame with lagtime and growth rate
    """
    datatemp = data.copy()
    if isinstance(datatemp.index, pd.DatetimeIndex):
        # set index as derltatime in hours
        datatemp.index = datatemp.index-datatemp.index[0]  # cal detlatime
        datatemp.index = datatemp.index.total_seconds()/3600 #index in hour in decimal format
    elif datatemp.index.dtype == float:
        logger.info("We assumed a DataFrame with float in hours as index")
        #print("We assumed a DataFrame with float in hours as index")
    else:
        logger.info("We assumed a DataFrame with float in hours as index")
        #print("Please provide a Dataframe with Datetime as index\n")
    
    if timethreshold:  # option to not use data before timethreshold time
        datatemp = datatemp.loc[datatemp.index >= timethreshold].copy()
        logger.info(f"Data for time before {timethreshold}h does not use for calculation due to user request, so lagtime maybe be wrong.")
        #print(f"Data for time before {timethreshold}h does not use for calculation due to user request, so lagtime maybe be wrong.")
    
    if deltathreshold:
        # Discare data without a minimal delta max - min in column
        datatemp = datatemp.apply(selectdatawithminidelta, args=[deltathreshold]).dropna(axis=1, how="all")
    
    #Legacy algo from table data with decimal deltatime in index and gowth proxy in columns help to Pandas pipe
    #clean data set
    datasmooth = (
        datatemp
        .apply(normalizedata, args=(usemax, percentofmax))  # normalized data by first five point average
        .apply(np.log)  # ln(data/datamin)
        .rolling(window=9, center=True).mean()  # smooth ln(data) window of 9
    )
    
    #found index of slope max
    indexmax = (
    datasmooth
    .rolling(5, center=True).apply(calcslope)  # compute rolling slope
    .idxmax()
    )
    
    #Compute growthrate and lagtime
    fanody = (
        datasmooth
        .rolling(5, center=True).apply(calcslope)  # compute rolling slope
        .apply(linearareaselection, percent=percentegra) # selection of relevent slope area as % variation of max slope EGRA
        .apply(EGRAdataselection, args=(datasmooth,))  # selection of relevent data from smotth table to compute µ
        .apply(calcslope, args=(False,)).T  # compute Slope and Intercept and transposed
        .rename(columns = {0:"maximal_growth_rate_per_h", 1 : "lagtime_h"})  # renaming
        .assign(lagtime_h = lambda df: -df["lagtime_h"]/df["maximal_growth_rate_per_h"])  #compute lagtime (basted on intercept already and wrongly named lagtime)
        .assign(maximal_growth_rate_time_h = indexmax)  #add time of mumax
        .assign(maximal_od = datatemp.max())  # max od of original dataframe
        .round(2)  #round at two decimals
            )
    
    return fanody


def fanodymultiauxic(data:pd.DataFrame, windows:float=5, percentofmax: float=0.05, usemax:bool=False) -> pd.DataFrame:
    """Function to compute growths rates and lagtimes for multiauxies
    It is based on a mix of two algorithms describes in the following:
    Toussaint et al. 2006 and Hall et al. 2014.
    Whereas growth rates are found with local max computation.
    
    Input:
    -----
    A DataFrame with only data considered as proxy of biomass can be used.
    DataFrame index has to be a float corresponding to
    a delta time (in hours) or pandas.DatetimeIndex
    
    Parameters:
    ----------
    usemax: allow users by use chose between normalization methods:
            average of the first five points
            or 
            percentage of the maximal value of dataset
    percentofmax: allow users to change the percentage of maximal value used
    
    Output:
    ------
    return a DataFrame with lagtimes and growth rates
    """
    datatemp = data.copy()
    if isinstance(datatemp.index, pd.DatetimeIndex):
        # set index as derltatime in hours
        datatemp.index = datatemp.index-datatemp.index[0]  # cal detlatime
        datatemp.index = datatemp.index.total_seconds()/3600 #index in hour in decimal format
    elif datatemp.index.dtype == float:
        logger.info("We assumed a DataFrame with float in hours as index")
        #print("We assumed a DataFrame with float in hours as index")
    else:
        logger.info("Please provide a Dataframe with Datetime as index\n")
        #print("Please provide a Dataframe with Datetime as index\n")
    #FanODy algo from table data with decimal deltatime in index and gowth proxy in columns help to Pandas pipe
    #clean data set
    datasmooth = (
        datatemp
        .apply(normalizedata, args=(usemax, percentofmax))  # normalized data by first five point average
        .apply(np.log)  # ln(data/datamin)
        .rolling(window=9, center=True).mean()  # smooth ln(data) window of 9
    )
    
    #compute growthrate and lagtimes for multiauxic growth
    fanodymulti =(
                datasmooth.apply(multireg, args=(windows,)).T # compute Slopes and Intercepts and transposed
                .rename(columns = {0:"maximal_growth_rate_per_h", 1 : "lagtime_h", 2 : "maximal_growth_rate_time_h"})  # renaming
                )
                
                
    return fanodymulti


def builddicorename(DFdata : pd.DataFrame, dicorenamingrullsuserdef: Dict) -> Dict:
    """Function to build a specific rename dicotionary for DataFrame columns names
    input: DFdata a Pandas DataFrame
            dicorull with key as new column name and values differents values possibly present in
            the dataframe
    output: the dictionary to achieve dataframe.rename(columns=builddicorename(dataframe, dicorenamingrullsuserdef), inplace=True)
    """
    columnlist = DFdata.columns.tolist()
    listvalues = list(dicorenamingrullsuserdef.values())
    listkeys = list(dicorenamingrullsuserdef.keys())
    dicorename = {}
    for columname in columnlist:
        for index, values in enumerate(listvalues):
            if columname in values:
                dicorename[columname] = listkeys[index]
    return dicorename

def customedrenamefunction(DFdata:pd.DataFrame, dicorenamingrullsuserdef:Dict, inplace:bool=False) -> pd.DataFrame:
    """Function to rename from a dictionary in forme {"newname" : (possibleoldname1, possibleoldname2)}
    and rename columns in a DataFrame like possiblename1 ==> new name.
    
    Input:
    -----
    DataFrame
    Dictionary with key as new column name and
    values list of values possibly used in the Dataframe as columns
    
    Output:
    ------
    return a DataFrame with new columns names
    """
    outDF = DFdata.rename(columns=builddicorename(DFdata, dicorenamingrullsuserdef), inplace=inplace)
    return outDF

def meanreplicates(dataframe:pd.DataFrame, sepchar:str):
    """Function to average data from a pandas DataFrame grouping by left part of column name
    after splitting by a defined separated character (sepchar)
    Input:
    -----
    DataFrame
    The character that separate base name to sample identification
    
    Output:
    ------
    return a DataFrame with averaged data per base name
    
    """
    listofsamplebasename = [column.split(sepchar)[0] for column in dataframe.columns]
    listofsamplename = dataframe.columns.to_list()
    if len(listofsamplebasename) == len(listofsamplename):
        mapping = dict(zip(listofsamplename, listofsamplebasename))
        return dataframe.T.groupby(by=mapping).mean().T
    else:
        return dataframe


pd.core.base.PandasObject.fermgrowth = fanodygrowth # monkey-patch the DataFrame class to add growth rate calculation
pd.core.base.PandasObject.multirename = customedrenamefunction # monkey-patch the DataFrame class to add multiranaming function
pd.core.base.PandasObject.fermmultiaux = fanodymultiauxic # monkey-patch the DataFrame class to add multiphasic growth rates calculation
pd.core.base.PandasObject.replicates = meanreplicates # monkey-patch the DataFrame class to add capacity to average by replicates identified by column names


if __name__ == '__main__':
    """here argparser code"""
    parser = argparse.ArgumentParser(description = "Pandasfermy add to Pandas method to compute analysis on fermentation data", 
    epilog="For Help or more information please contact Nicolas Hardy")
    
    parser.add_argument("filepath", metavar = "Root of data", type = str, help = "File with fermentation data first column have to be time")
    parser.add_argument("-p","--percent", dest="percentofmax", type = float, default = 0.05, help = "Percentage of the maximal value considered as relevant by default it is egal to 0.05 (for 5 percent)")
    parser.add_argument("-m","--min", action='store_false', dest="usemax", help = "Option to use mininaml value for nomalization (like legacy algorithm ) instead of maximal value percentage")
    
    args = parser.parse_args()
    
    percentofmax = args.percentofmax
    filepath = args.filepath
    usemax = args.usemax
    """"code here"""
    #load data
    data = pd.read_excel(filepath, index_col=0)  #load data with Pandas index have to be datetime.datetime
    #use the pandasfermy
    print(usemax)
    print(f"percent of max value for nomalization will be {percentofmax*100}%")
    fanody = data.fermgrowth(percentofmax=percentofmax ,usemax=usemax)
    multiaux = data.fermmultiaux(windows=5,percentofmax=percentofmax, usemax=usemax)
    print(fanody, multiaux)
    #Save data
    fanody.to_excel(os.path.splitext(filepath)[0]+f"{percentofmax}_out.xlsx")
    multiaux.to_excel(os.path.splitext(filepath)[0]+f"{percentofmax}_multiaux_out.xlsx")
