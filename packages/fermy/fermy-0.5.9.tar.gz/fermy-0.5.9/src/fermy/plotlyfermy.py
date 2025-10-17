"""
Created the 2021/10/13
v0.0 First version
v0.1 Add link with pandasfermy
v0.2 Add control chart graph
v0.3 Add powerfoce option to control chart and bug fix if no vialtion of rules
v0.4 update of function description
        for ccplot ==> no show if save path set / add option to unclean data violation
v0.5 Add multiy chart method and chart are no shown if save path set
v0.6 Add groupby option multiyaxis chart
v0.7 bug fix for more than two bioreactors dataset multiyplot grouped
v0.8 add colorby option to ccplot
v0.9 add option to comput for ccplot LCL and UCL and mean from a pd.serie
v1.0 add option to set x axis title
v1.1 change way to deal with path and add ccplot options
v1.2 bug fix for power of LQL HQL
v1.3 add capability to create an un-existing output file


To implement for multiy chart:
    * Simplify multiy chart help to yaxisn=dict(title="yaxisn title", anchor="free", overlaying="y", autoshift=True)
    * option to plot some colmns with dot instead line (input list of columns)
    datatodots:List[str]=[]

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
import plotly.express as px
import plotly.graph_objects as go  # only for multi y plot
import argparse
import numpy as np
from pathlib import Path

from fermy.log import logger

#layout
layoutdic = dict(modebar_add=["v1hovermode", "toggleSpikeLines"],
                    title='Fermentation data',
                    xaxis_title="Time (in hours)",
                    yaxis_title="Growth proxy",
                    font=dict(
                        family='Linux Libertine, Times New Roman',
                        size = 20,
                        color='#000'
                    ),
                    legend=dict(
                        title=dict(text="Bioreactors",side="top"),
                        x=0,
                        y=-0.2,
                        orientation="h",
                        font=dict(
                            family='Linux Libertine, Times New Roman',
                            size = 10,
                            color='#000'
                        ),
                        traceorder="normal"  # "normal" or "grouped"
                    ),
                        updatemenus=[
                            dict(
                                buttons=list([
                                    dict(label="Linear",  
                                        method="relayout", 
                                        args=[{"yaxis.type": "linear", "yaxis.title" : f"Growth proxy"}]),
                                    dict(label="Log", 
                                        method="relayout", 
                                        args=[{"yaxis.type": "log", "yaxis.title" : f"ln(Growth proxy)"}])
                                  ]),
                                x=0.5,
                                y=1.5,
                                  ),
                                  {'type': 'buttons',
                    "showactive":True,
                    "x" : 0.6,
                    "y" : 1.5,
                    'buttons': [{'label': 'Legend',
                                'method': 'relayout',
                                'args': ['showlegend', True],
                                'args2': ['showlegend', False]}],
                    }
                                  
                                  
                                  ]
                )



class ParseKwargs(argparse.Action):
    """Class to add deal with dict as arg in argparse
    """
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, dict())
        for value in values:
            key, value = value.split('=')
            getattr(namespace, self.dest)[key] = value



def basicplot(data: pd.DataFrame, path:str=""):
    """Plot all columns of a Dataframe as Y and index for x
    """
    fig = px.line(data, x=data.index, y=data.columns, markers=True)
    fig.update_layout(layoutdic, template="simple_white")
    if path != "":
        path = Path(path)
        if path.is_dir():
            pathout = path.joinpath("sfgraph.html")
            fig.write_html(pathout)
        elif path.is_file():
            pathout = path.parents[0].joinpath(f"{path.stem}_sfgraph.html")
            fig.write_html(pathout)
        else:
            fig.write_html(path)
    else:
        fig.show()

def defxaxislen(list_of_yaxis: List, yspace: float):
    """Give the value for the max xaxis range from the list of y axis linked to the number
    """
    lenlistyaxis = len(list_of_yaxis)
    if lenlistyaxis > 2:
        xaxislen = (1-(lenlistyaxis-2)*yspace) #Range max for x depends on the yxais number exemple for 4 it is 0.9.
    else:
        xaxislen = 1
    return xaxislen


def multiyplot(data: pd.DataFrame, path:str="", yspace:float=0.05, sizep:int=16, groupby:Union[None,str]=None, xtitle:Union[None,str]=None):
    """Plot all columns of a Dataframe with multiY axis and index for x
    
    Input:
    -----
    DataFrame
    
    
    Parameters:
    ----------
    path: is provided the graph will be saved in this path
    
    yspace: allows users to custom space between yaxis
    
    sizep: allows users to custom font size
    
    groupby: used character to build group for plotting e.g. groupby="-" for pH-Biroeactor1 => group pH and subdataset bioreactor1
    
    xtitle: allows to custom x title
    
    Output:
    ------
    No output only graph
    """
    fig = go.Figure()  # creat an empty fig
    
    if groupby:
        #groupe construction dico
        headerslist = data.columns.tolist()
        headerslist.sort()  # sort list
        dicolistgroup ={}
        for header in headerslist:
            dicolistgroup[header] = header.split(groupby)[0]
        listofgroup = list(set(dicolistgroup.values()))
        listofgroup.sort()  # sort list
        rangemaxXaxis = defxaxislen(listofgroup, yspace) #variable size of x axis
        
        assert rangemaxXaxis>0, "too many columns please drop useless columns and/or reduce yspace paramter"
        
        fig.update_layout(xaxis=dict(domain = [0,rangemaxXaxis], #place en % des x
                        title=data.index.name,
                        title_standoff=0,
                        ),
                        title_text="Fermentation multiple y-axes",
                        template="simple_white",
                        legend=dict(x=0,
                                    y=-0.1,
                                    tracegroupgap = 0,
                                    orientation="h",
                                    font=dict(
                                        family='Times New Roman',
                                        size = sizep,
                                        color='#000')
                                    ),
                        font=dict(
                            family='Linux Libertine, Times New Roman',
                            size = sizep,
                            color='#000'
                        ),
                        modebar_add=["v1hovermode", "toggleSpikeLines"],
                        )
        indexgroup = 0
        legendgroup = None
        for column in data.columns.sort_values():
            if indexgroup == 0:
                if legendgroup == None:
                    legendgroup = dicolistgroup[column]
                    fig.add_trace(go.Scatter(x=[data.index[0]], y=[data[column][0]], name=legendgroup, marker=dict(color="Black", size=0.01), visible='legendonly', legendgroup=legendgroup, showlegend=True))  #Q&D no better solution today
                    fig.add_trace(go.Scatter(x=data.index, y=data[column], name=column, legendgroup=legendgroup, hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}", showlegend=False))
                    fig.layout["yaxis"] = dict(title=legendgroup, title_standoff=0, title_font={"size" : sizep*rangemaxXaxis})
                    
                elif legendgroup == dicolistgroup[column]:
                    fig.add_trace(go.Scatter(x=data.index, y=data[column], name=column, legendgroup=legendgroup, hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}", showlegend=False))  
                    fig.layout["yaxis"] = dict(title=legendgroup, title_standoff=0, title_font={"size" : sizep*rangemaxXaxis})
                else:
                    indexgroup+=1
                    legendgroup = dicolistgroup[column]
                    fig.add_trace(go.Scatter(x=[data.index[0]], y=[data[column][0]], name=legendgroup, marker=dict(color="Black", size=0.01), visible='legendonly', legendgroup=legendgroup, showlegend=True, yaxis=f"y{indexgroup+1}"))  #Q&D no better solution today
                    fig.add_trace(go.Scatter(x=data.index, y=data[column], name=column, yaxis=f"y{indexgroup+1}", legendgroup=legendgroup, hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}", showlegend=False))
                    fig.layout[f"yaxis{indexgroup+1}"] = dict(title=legendgroup, anchor="x", overlaying="y", side="right", position=1, title_standoff=0, title_font= {"size" : sizep*rangemaxXaxis})
                    
            elif indexgroup == 1:
                if legendgroup == dicolistgroup[column]:
                    fig.add_trace(go.Scatter(x=data.index, y=data[column], name=column, yaxis=f"y{indexgroup+1}", legendgroup=legendgroup, hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}", showlegend=False))
                    fig.layout[f"yaxis{indexgroup+1}"] = dict(title=legendgroup, anchor="x", overlaying="y", side="right", position=1, title_standoff=0, title_font= {"size" : sizep*rangemaxXaxis})
                else:
                    legendgroup = dicolistgroup[column]
                    indexgroup+=1
                    fig.add_trace(go.Scatter(x=[data.index[0]], y=[data[column][0]], name=legendgroup, marker=dict(color="Black", size=0.01), visible='legendonly', legendgroup=legendgroup, showlegend=True, yaxis=f"y{indexgroup+1}"))  #Q&D no better solution today
                    fig.add_trace(go.Scatter(x=data.index, y=data[column], name=column, yaxis=f"y{indexgroup+1}", legendgroup=legendgroup, hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}", showlegend=False))
                    fig.layout[f"yaxis{indexgroup+1}"] = dict(title=legendgroup, anchor="free", overlaying="y", side="right", position=rangemaxXaxis + yspace*(indexgroup-1), title_standoff=0, title_font={"size" : sizep*rangemaxXaxis})
            else:
                if legendgroup == dicolistgroup[column]:
                    fig.add_trace(go.Scatter(x=data.index, y=data[column], name=column, yaxis=f"y{indexgroup+1}",legendgroup=legendgroup, hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}", showlegend=False))
                    fig.layout[f"yaxis{indexgroup+1}"] = dict(title=legendgroup, anchor="free", overlaying="y", side="right", position=rangemaxXaxis + yspace*(indexgroup-1), title_standoff=0, title_font={"size" : sizep*rangemaxXaxis})
                else:
                    legendgroup = dicolistgroup[column]
                    indexgroup+=1
                    fig.add_trace(go.Scatter(x=[data.index[0]], y=[data[column][0]], name=legendgroup, marker=dict(color="Black", size=0.01), visible='legendonly', legendgroup=legendgroup, showlegend=True, yaxis=f"y{indexgroup+1}"))  #Q&D no better solution today
                    fig.add_trace(go.Scatter(x=data.index, y=data[column], name=column, yaxis=f"y{indexgroup+1}",legendgroup=legendgroup, hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}", showlegend=False))
                    fig.layout[f"yaxis{indexgroup+1}"] = dict(title=legendgroup, anchor="free", overlaying="y", side="right", position=rangemaxXaxis + yspace*(indexgroup-1), title_standoff=0, title_font={"size" : sizep*rangemaxXaxis})
    else:
        rangemaxXaxis = defxaxislen(data.columns, yspace) #variable size of x axis
        assert rangemaxXaxis>0, "too many columns please drop useless columns and/or reduce yspace paramter and/or used groupby option"
        fig.update_layout(xaxis=dict(domain = [0,rangemaxXaxis], #place en % des x
                        title=data.index.name,
                        title_standoff=0,
                        ),
                        title_text="Fermentation multiple y-axes",
                        template="simple_white",
                        legend=dict(x=0,
                                    y=-0.1,
                                    tracegroupgap = 0,
                                    orientation="h",
                                    font=dict(
                                        family='Times New Roman',
                                        size = sizep,
                                        color='#000')
                                    ),
                        font=dict(
                            family='Linux Libertine, Times New Roman',
                            size = sizep,
                            color='#000'
                        ),
                        modebar_add=["v1hovermode", "toggleSpikeLines"],
                        )
        for index, column in enumerate(data.columns):
            if index==0:
                fig.add_trace(go.Scatter(x=data.index, y=data[column], name=column, hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}"))
                fig.layout["yaxis"] = dict(title=column, title_standoff=0, title_font={"size" : sizep*rangemaxXaxis})
            elif index==1:
                fig.add_trace(go.Scatter(x=data.index, y=data[column], name=column, yaxis=f"y{index+1}", hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}"))
                fig.layout[f"yaxis{index+1}"] = dict(title=column, anchor="x", overlaying="y", side="right", position=1, title_standoff=0, title_font= {"size" : sizep*rangemaxXaxis})
            else:
                fig.add_trace(go.Scatter(x=data.index, y=data[column], name=column, yaxis=f"y{index+1}", hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}"))
                fig.layout[f"yaxis{index+1}"] = dict(title=column, anchor="free", overlaying="y", side="right", position=rangemaxXaxis + yspace*(index-1), title_standoff=0, title_font={"size" : sizep*rangemaxXaxis})
    if xtitle:
        fig.update_xaxes(title=xtitle)
    if path != "":
        path = Path(path)
        if path.is_file():
            pathout = pathout = path.parents[0].joinpath(f"{path.stem}_multiyfgraph.html")
            fig.write_html(pathout)
        elif path.is_dir():
            pathout = path.joinpath("multiyfgraph.html")
            fig.write_html(pathout)
        else:
            fig.write_html(path)
    else:
        fig.show()
    
def ccplot(data: pd.DataFrame, variableofinterest: str, path:str="", dicorename:Dict={}, forcepower:bool=False, addccviol:bool=False, colorby:Union[None,str]=None, outref:Union[None,pd.Series]=None, hql:Union[None,float]=None, lql:Union[None,float]=None, overinfo:Union[None,List[str]]=None) -> pd.DataFrame:
    """
    Function to compute and plot a simple (and pretty) Control Chart with Plotly express
    
    Input:
    -----
    Data will be columns values of the column named variableofinterest
    and index of the DataFrame as plot index
    
    Parameters:
    ----------
    path:str, default ""
    if provided the graph will be saved in this path
    
    dicorename: Dict, default {}
    allow users to custom names of axis with:
    {"old name" : "desired name", "old name2" : "desired name2"}
    
    forcepower: bool, default False
    allow users to force scientific notation 10^n for y axis
    and controls limits
    
    addccviol: bool, default False
    allow users to add a new column to original data with CC rules check-in 
    
    colorby: None or string
    allow users to color regarding column value
    
    outref: None or pd.Series
    use external data to compute ULC, LCL and mean
    
    hql: None or float
    High quality limit
    
    lql: None or float
    Low quality limitt
    
    overinfo: None or List
    List of dataframe column name
    Allow to plot additive information
    
    Output:
    ------
    return a DataFrame like data with only Control Chart violations data
    """
    if type(outref) == pd.Series:
        center = outref.mean()
        std = outref.std()
    elif type(outref) == pd.DataFrame:
        print("outref have to be a pd.Series here it is a Dataframe")
        if outref.shape[1] == 1:
            print('outref was converted to pd.Series')
            outrefinserie = outref[outref.columns[0]]
            center = outrefinserie.mean()
            std = outrefinserie.std()
        else:
            print("outref can be converted to pf.Series only if shape = (n,1)")
            return None
    else:
        #basic data to compute LCL, center and UCL on data
        center = data[variableofinterest].mean()
        std = data[variableofinterest].std()
    nbsigma = [1,2,3]
    #color values add column in dataframe if value not ok regarding CC rules
    conditions = [  (data[variableofinterest]>=center+std*3),  # Out-of-control rule 1 > +3 sigma
                    (data[variableofinterest]<=center-std*3), # Out-of-control rule 1 < -3 sigma
                    ((data[variableofinterest] < center) & # Out-of-control rule 2 Nine points in a row -3 sigma
                    (data[variableofinterest].shift(1) < center) &
                    (data[variableofinterest].shift(2) < center) &
                    (data[variableofinterest].shift(3) < center) &
                    (data[variableofinterest].shift(4) < center) &
                    (data[variableofinterest].shift(5) < center) &
                    (data[variableofinterest].shift(6) < center) &
                    (data[variableofinterest].shift(7) < center) &
                    (data[variableofinterest].shift(8) < center)),
                    ((data[variableofinterest] > center) & # Out-of-control rule 2 Nine points in a row +3 sigma
                    (data[variableofinterest].shift(1) > center) &
                    (data[variableofinterest].shift(2) > center) &
                    (data[variableofinterest].shift(3) > center) &
                    (data[variableofinterest].shift(4) > center) &
                    (data[variableofinterest].shift(5) > center) &
                    (data[variableofinterest].shift(6) > center) &
                    (data[variableofinterest].shift(7) > center) &
                    (data[variableofinterest].shift(8) > center)),
                    ((data[variableofinterest].shift(2) >=center+std*2) & # Out-of-control rule 5 Two out of three points in a row +2 sigma
                    (data[variableofinterest].shift(1) >=center+std*2) &
                    (data[variableofinterest] >=center)),
                    ((data[variableofinterest].shift(2) >=center+std*2) & # Out-of-control rule 5 Two out of three points in a row +2 sigma
                    (data[variableofinterest] >=center+std*2) &
                    (data[variableofinterest].shift(1) >=center)),
                    ((data[variableofinterest].shift(2) <=center-std*2) & # Out-of-control rule 5 Two out of three points in a row -2 sigma
                    (data[variableofinterest].shift(1) <=center-std*2) &
                    (data[variableofinterest] <=center)),
                    ((data[variableofinterest].shift(2) <=center-std*2) & # Out-of-control rule 5 Two out of three points in a row -2 sigma
                    (data[variableofinterest] <=center-std*2) &
                    (data[variableofinterest].shift(1) <=center)),
                    ] # create a list of our conditions
    print("\nOut-of-control rule 1: > +3 sigma or < -3 sigma\nOut-of-control rule 2: Nine points in a row -3 sigma or +3 simga\nOut-of-control rule 5: Two out of three points in a row +2 sigma or -2 sigma\n")
    values = ['Out-of-control rule 1', 'Out-of-control rule 1', 'Out-of-control rule 2', 'Out-of-control rule 2', 'Out-of-control rule 5', 'Out-of-control rule 5', 'Out-of-control rule 5', 'Out-of-control rule 5'] # create a list of the values we want to assign for each condition
    #creat a new column with control status
    data['CClimitctrl'] = np.select(conditions, values, default = "Under control")
    # difine color map to unlight out-of-control
    color_discrete_map = {'Out-of-control rule 1': 'rgb(255,0,0)', 'Under control': 'rgb(31,119,180)', 'Out-of-control rule 2': 'rgb(217,75,83)' , 'Out-of-control rule 5' : 'rgb(238,25,154)'}
    #plot Control chart
    if not colorby:
        fig = px.scatter(data, x=data.index, y=variableofinterest,
                            #size  = variableofinterest, # size as function of a column
                            color = data.CClimitctrl, # color as function of a column
                            color_discrete_map=color_discrete_map, # set color according to user define map
                            #symbol = variableofinterest, # symbol as function of a column
                            title=f"Control Chart",
                            range_y = [center-6*std,center+6*std], # set default limit for Y
                            labels = dicorename,
                            template="simple_white",  # set easy template
                            hover_data = overinfo
                        )
    else:
        fig = px.scatter(data, x=data.index, y=variableofinterest,
                            #size  = variableofinterest, # size as function of a column
                            color = data[colorby], # color as function of a column
                            #symbol = variableofinterest, # symbol as function of a column
                            title=f"Control Chart",
                            range_y = [center-6*std,center+6*std], # set default limit for Y
                            labels = dicorename,
                            template="simple_white",  # set easy template
                            hover_data = overinfo
                        )
    #Add LCL UCL pretty print
    fig.add_hline(y=center, line_dash="longdashdot", line_color="blue", line_width=1, opacity=1)  #set center
    
    if hql:
        fig.add_hline(y=hql, line_dash="dot", line_color="purple", line_width=1, opacity=1)  #set quality limit high
    if lql:
        fig.add_hline(y=lql, line_dash="dot", line_color="purple", line_width=1, opacity=1)  #set quality limit low
        
    for sigma in nbsigma:
        if sigma<3:
            fig.add_hline(y=center+sigma*std, line_dash="dash", line_color="red", line_width=1, opacity = sigma/3)  # UCL
            fig.add_hline(y=center-sigma*std, line_dash="dash", line_color="red", line_width=1, opacity = sigma/3)  # LCL
        else:
            fig.add_hline(y=center+sigma*std, line_dash="longdash", line_color="red", line_width=1, opacity = sigma/3)  # UCL
            fig.add_hline(y=center-sigma*std, line_dash="longdash", line_color="red", line_width=1, opacity = sigma/3)  # LCL

    if len(data['CClimitctrl'].unique())<=1:
        fig.update(layout_showlegend=False) #hide legend if all point under control
        batchwithissues = pd.DataFrame()
    else:
        batchwithissues = data.loc[data['CClimitctrl']!="Under control",:]
        fig.update_layout(legend =dict(title=dict(text="Control Chart Violations")))
        
    if forcepower:
        fig.update_yaxes(exponentformat="power")  # force 10^n notation
                # add anotation ULC / AVG / LCL
        #ULC
        fig.add_annotation(
                x=1,
                y=center+3*std,
                xref="paper",
                yref="y",
                text=f"UCL={round(center+3*std,1):0.2E}",
                showarrow = False,
                yshift=10
                )
        #LCL
        fig.add_annotation(
                x=1,
                y=center-3*std,
                xref="paper",
                yref="y",
                text=f"LCL={round(center-3*std,1):0.2E}",
                showarrow = False,
                yshift=10
                )
        #center
        fig.add_annotation(
                x=1,
                y=center,
                xref="paper",
                yref="y",
                text=f"Avg={round(center,1):0.2E}",
                showarrow = False,
                yshift=10
                )
        #hql lql
        if hql:
            fig.add_annotation(x=0,
            y=hql,
            xref="paper",
            yref="y",
            text=f"HQL={round(hql,1):0.2E}",
            showarrow = False,
            yshift=10)
        if lql:
            fig.add_annotation(x=0,
                            y=lql,
                            xref="paper",
                            yref="y",
                            text=f"LQL={round(lql,1):0.2E}",
                            showarrow = False,
                            yshift=-10)
    else:
        # add anotation ULC / AVG / LCL
        #ULC
        fig.add_annotation(
                x=1,
                y=center+3*std,
                xref="paper",
                yref="y",
                text=f"UCL={round(center+3*std,1)}",
                showarrow = False,
                yshift=10
                )
        #LCL
        fig.add_annotation(
                x=1,
                y=center-3*std,
                xref="paper",
                yref="y",
                text=f"LCL={round(center-3*std,1)}",
                showarrow = False,
                yshift=10
                )
        #center
        fig.add_annotation(
                x=1,
                y=center,
                xref="paper",
                yref="y",
                text=f"Avg={round(center,1)}",
                showarrow = False,
                yshift=10
                )
        #hql lql
        if hql:
            fig.add_annotation(x=0,
                        y=hql,
                        xref="paper",
                        yref="y",
                        text=f"HQL={round(hql,1)}",
                        showarrow = False,
                        yshift=10)
        if lql:
            fig.add_annotation(x=0,
                            y=lql, xref="paper",
                            yref="y",
                            text=f"LQL={round(lql,1)}",
                            showarrow = False,
                            yshift=-10)
        
        
    if path != "":
        path = Path(path)
        if path.is_file():
            pathout = pathout = path.parents[0].joinpath(f"{path.stem}_CCgraph.html")
            fig.write_html(pathout)
        elif path.is_dir():
            pathout = path.joinpath("CCgraph.html")
            fig.write_html(pathout)
        else:
            fig.write_html(path)
    else:
        fig.show()
    if not addccviol:
        data.drop(columns="CClimitctrl", inplace=True)  # clean data add to graph violation
    return batchwithissues

pd.core.base.PandasObject.fplotsimple = basicplot
pd.core.base.PandasObject.fccplot = ccplot
pd.core.base.PandasObject.fplotmultiy = multiyplot

if __name__ == '__main__':
    """here argparser code"""
    """"code here"""
