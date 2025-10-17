"""
Created the 2023/01/05
v0.1 First version
v0.4 increase robuness of TimeDeltapH function & make calculation
v0.5 upgrade in interpolationofCINACdata function on true pH values instead of theorical one
v0.6 add pH kinetic dedicated plot & interpolation update to follow Pandas
v0.7 add option for naming pH kinetic dedicated plot
v0.8 fix bug pHatTime mother function

NExt time add: method .inter & .cinacplot to read me

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
from typing import List, Dict, Iterable, Tuple, Union
import numpy as np
import plotly.express as px # for plot purpose
from pathlib import Path # deal with Path

#plot function
def plotph(df, path:str="",strname:str=""):
    """Plot all columns of a Dataframe as Y and index for x
    for pH data with index
    """
    fig = px.line(df,
        x=df.index,
        y=df.columns,
        title=f"pH data vs time {strname}",
        template="simple_white").update_layout(yaxis_title=f"pH in u.pH",
                                                xaxis_title=f"Time",
                                                yaxis_range=[3,8],
                                                modebar_add=["v1hovermode", "toggleSpikeLines"]
                                                )
    if path != "":
        path = Path(path)
        if path.is_dir():
            if strname == "":
                pathout = path.joinpath("pHgraph.html")
            else:
                pathout = path.joinpath(f"{strname}_pHgraph.html")
            fig.write_html(pathout)
        elif path.is_file():
            if strname == "":
                pathout = path.parents[0].joinpath(f"{path.stem}_pHgraph.html")
            else:
                pathout = path.parents[0].joinpath(f"{strname}_pHgraph.html")
            fig.write_html(pathout)
        else:
            fig.write_html(path)
    else:
        fig.show()


#pretreatment functions
def interpolationofCINACdata(seriepH:pd.Series,unitinput:str="m",resolsec:int=30):
    """.apply(interpolationofCINACdata,args=("m",30))
    unit of time in input dataset = h for hours or m for minutes
    """
    seriepH.index = pd.to_timedelta(seriepH.index,unit=unitinput)
    interpoledseriepH = seriepH.resample(f"{resolsec}s").mean().interpolate(methode="linear")
    
    if unitinput == "m":
        interpoledseriepH.index = interpoledseriepH.index.seconds/60 + interpoledseriepH.index.days*24*60
    elif unitinput == "h":
        interpoledseriepH.index = interpoledseriepH.index.seconds/3600 + interpoledseriepH.index.days*24
    else:
        print('Wrong unitinput have to be in ["h","m"]')
        
    return interpoledseriepH

#mother functions
def TimetopH(seriepH:pd.Series, pHtarget:float):
    """.apply(TimetopH,args=(newpHtarget,))
    """
    timetopH = seriepH.loc[(seriepH<=pHtarget)].first_valid_index()
    if timetopH:
        return timetopH
    else:
        return np.nan

def pHatTime(seriepH:pd.Series, Time:float):
    """.apply(pHatTime,args=(timetarget,))
    """
    pHattime = seriepH.iloc[seriepH.index.get_indexer([Time], method='nearest').item()]
    return pHattime
    
def TimeDeltapH(seriepH:pd.Series, pHini:float, pHfin:float, taux:bool=False):
    """Find time for delta pH between pHini and pHfin return it in minutes
    .apply(TimeDeltapH,args=(pHini,pHfin,taux))
    """
    tdeltapHdeb = None
    tdeltapHfin = None
    if not seriepH.loc[(seriepH>=pHini)].empty:
        if not seriepH.loc[(seriepH<=pHfin)].empty:
            tdeltapHdeb = seriepH.loc[(seriepH<=pHini) & (seriepH>=pHfin)].first_valid_index()
            tdeltapHfin = seriepH.loc[(seriepH<=pHini) & (seriepH>=pHfin)].last_valid_index()
            if tdeltapHdeb is not None:
                if tdeltapHfin is not None:
                    deltaTpH = tdeltapHfin-tdeltapHdeb # deltaTph in munutes
                else:
                    deltaTpH = np.nan
            else:
                deltaTpH = np.nan
        else:
            deltaTpH = np.nan
    else:
        deltaTpH = np.nan
    if taux:
        if deltaTpH != np.nan:
            if deltaTpH !=0:
                if tdeltapHfin != None:
                    pHfinreal = seriepH[tdeltapHfin]  # replace pHfin by real value
                    if tdeltapHdeb != None:
                        pHinireal = seriepH[tdeltapHdeb]  # replace pHini by real value
                        taux = (pHfinreal-pHinireal)/(deltaTpH)
                    else:
                        taux = np.nan
                else:
                    taux = np.nan
            else:
                taux = np.nan
        else:
            taux = np.nan
        return taux
    else:
        return deltaTpH

def Ta(seriepH:pd.Series, timepHini:int = 15, deltapH:float=0.08):
    """.apply(ta,args=(timepHini,deltapH))
    """
    indexphstart = seriepH.loc[seriepH.index <= timepHini].last_valid_index()
    if indexphstart != None:
        pHinical = seriepH[indexphstart]
    else:
        pHinical = np.nan
    pHfinTa = pHinical-deltapH
    Ta = seriepH.loc[(seriepH<=pHfinTa)].first_valid_index()
    if Ta != None:
        return Ta
    else:
        return np.nan

listofmotherfunction = [TimetopH,pHatTime,TimeDeltapH,Ta]

#children functions
#deltaTpH6.3-6.0
def deltaTpH6360(seriepH:pd.Series):
    return TimeDeltapH(seriepH,6.3,6)
#Ta 0.08

#already done

#TDpH0.3
def TDpH03(seriepH:pd.Series):
    return TimeDeltapH(seriepH,seriepH.iloc[0],seriepH.iloc[0]-0.3)

#TDpH0.6
def TDpH06(seriepH:pd.Series):
    return TimeDeltapH(seriepH,seriepH.iloc[0],seriepH.iloc[0]-0.6)

#and TpH5.2
def TpH52(seriepH:pd.Series):
    return TimetopH(seriepH,5.2)

#slope between pH6 and 5
def slopebetweenpH6and5(seriepH:pd.Series):
    return TimeDeltapH(seriepH,6,5,True)


#contruction of table
#A new function can be atted to the .cinac() method by appending new function this list
mycinactable = [deltaTpH6360,Ta,TDpH03,TDpH06,TpH52,slopebetweenpH6and5]  # list of children function

def cinaccal(data:pd.DataFrame):
    """Function to create CINAC descriptors table
    """
    return data.agg(mycinactable)

def interpolcinac(data:pd.DataFrame,unitinput:str="m", resolsec:int=30):
    """Function to interpolate CINAC data (time serie)
    unit of time in input dataset = h for hours or m for minutes
    resolsec = interpolation step in seconds
    """
    return data.apply(interpolationofCINACdata, args=(unitinput,resolsec))

pd.core.base.PandasObject.cinac = cinaccal # monkey-patch the DataFrame class to add CINAC like calculation
pd.core.base.PandasObject.inter = interpolcinac # monkey-patch the DataFrame class to add interpolation  
pd.core.base.PandasObject.plotph = plotph # monkey-patch the DataFrame class to add plotph option
