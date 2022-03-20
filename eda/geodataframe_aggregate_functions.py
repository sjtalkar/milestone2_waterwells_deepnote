## This file contains functions common to charting datasets where a slider picks a time period and normalized data is 
## shown in the figure

import json
import pprint
import numpy as np
import pandas as pd
import altair as alt
import geopandas as gpd
from shapely import wkt
import matplotlib.pyplot as plt

def get_yearly_data(    input_file: str, 
                        time_aggregate_column:str,
                        year_avg_column_name:str,
                        col_to_aggr :str,
                        agg_func:str,
                        time_value:str):
    """
        Dataframe must have a column = geometry

        input_file            : Name of file containing cleaned data
        time_aggregate_column : name of time column to aggregate by
        year_avg_column_name  : Name of column to assign yearly average in
        col_to_aggr           : Name of column to be aggregated
        agg_func              : Mean or count
        norm_column_name      : Name to assign the cormalized column
        time_value            : Value to filter time columns

        After normalizing the value, the dataframe returned is a geodataframe and

    """
    #Read the file as a simple Pandas dataframe and perform pandas operations such as transform
    df = gpd.read_file(input_file, ignore_geometry=True)

    df = df[df[time_aggregate_column] > time_value]
    df[time_aggregate_column] = df[time_aggregate_column].astype(float).astype(int)
    df[col_to_aggr] = df[col_to_aggr].astype('float')

    #Find the  average `depth to groundwater elevation in feet below ground surface`. Normalize it for charting, across year and township range
    df[year_avg_column_name] = df.groupby([time_aggregate_column])[col_to_aggr].transform(agg_func)

    #After performing Pandas operations, convert into a gdf using stored geometry column
    df['geometry'] = df['geometry'].apply(wkt.loads)
    df = gpd.GeoDataFrame(df, crs='epsg:4326')

    return df

def get_normalized_data (gdf,
                        geometry_col_list: list,
                        time_aggregate_column :str,
                        year_agg_column_name : str,
                        col_to_agg :str,
                        agg_func :str):
    """ 
        Given a list of columns that represent the base and Yearly value aggregate, the function dissolves
        a geodataframe containing 'TownshipRange', 'COUNTY','geometry',
                    by 'TownshipRange', 'COUNTY','geometry',
                    AND  YEAR and Yearly value 
        and finds the defined aggregate of the values in the col_to_agg column

        gdf                    : Geodataframe    
        geometry_col_list      : list of geomtery columns to aggregate by   
        time_aggregate_column : name of time column to aggregate by
        year_agg_column_name  : Name of column containing the yearly aggregate 
        agg_func              : Mean or count
        col_to_agg            : Name of column to aggregate


        Returns a geodataframe with normalized values of the col_to_agg
    """

    df_list = ['geometry'] +  geometry_col_list + [time_aggregate_column,year_agg_column_name, col_to_agg ]
    dissolve_list = geometry_col_list + [time_aggregate_column,year_agg_column_name ]

    gdf = gdf[df_list].dissolve( by=dissolve_list, aggfunc=agg_func).reset_index()
    gdf[f'{col_to_agg}_NORMALIZED']= gdf[col_to_agg]/gdf[year_agg_column_name]
    return gdf
