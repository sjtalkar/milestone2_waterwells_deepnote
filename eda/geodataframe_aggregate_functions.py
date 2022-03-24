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

    # If the aggregation is on a categorical column, we do not need it to be a number
    if  agg_func != 'count': 
     df[col_to_aggr] = df[col_to_aggr].astype('float')

    #Find the  average `depth to groundwater elevation in feet below ground surface`. Normalize it for charting, across year and township range
    df[year_avg_column_name] = df.groupby([time_aggregate_column])[col_to_aggr].transform(agg_func)

    #After performing Pandas operations, convert into a gdf using stored geometry column
    df['geometry'] = df['geometry'].apply(wkt.loads)
    df = gpd.GeoDataFrame(df, crs='epsg:4326')

    return df

def get_dissolved_data (gdf,
                        dissolve_by_list: list,
                        col_to_agg :str,
                        agg_func :str):
    """ 
        Given a list of columns to dissolve by, the function dissolves
        a geodataframe  and finds the defined aggregate of the values in the col_to_agg column

        gdf                   : Geodataframe    
        dissolve_by_list      : list of geomtery columns to aggregate/dissolve by  
        col_to_agg            : Name of column to aggregate
        agg_func              : Mean or count
      

        Returns a geodataframe with aggregated values of col_to_agg in a column with the same name
    """
    #Dissolve only works on geodataframes and so include geometry in it. Also include the column to be aggregated
    df_list = ['geometry'] + dissolve_by_list + [col_to_agg]
    gdf = gdf[df_list].dissolve( by=dissolve_by_list, aggfunc=agg_func).reset_index()
    return gdf



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

        gdf                   : Geodataframe    
        geometry_col_list     : list of geomtery columns to aggregate by
        time_aggregate_column : name of time column to aggregate by
        year_agg_column_name  : Name of column that contains the computed yearly aggregate 
        col_to_agg            : Name of column to aggregate
        agg_func              : Mean or count
       

        Returns a geodataframe with normalized values of the col_to_agg. The normalized values are stored in a 
        column with name = col_to_agg_NORMALIZED
    """

    df_list = ['geometry'] +  geometry_col_list + [time_aggregate_column,year_agg_column_name, col_to_agg ]
    dissolve_list = geometry_col_list + [time_aggregate_column,year_agg_column_name ]

    gdf = gdf[df_list].dissolve( by=dissolve_list, aggfunc=agg_func).reset_index()
    gdf[f'{col_to_agg}_NORMALIZED']= gdf[col_to_agg]/gdf[year_agg_column_name]
    return gdf


def get_drought_year_chart():
    drought_df = pd.read_csv(r"../assets/outputs/california_weekly_drought_index.csv")
    drought_df.DATE  = pd.to_datetime(drought_df.DATE.str.replace("d_", ""))
    drought_df = drought_df[drought_df.DATE.dt.year > 2000][['DATE', 'D0', 'D1', 'D2', 'D3', 'D4']].copy()
    drought_year_chart = alt.Chart(drought_df.melt(
                            id_vars='DATE',
                            value_vars=['D1', 'D2','D3','D4'],
                            var_name='DROUGHT_LEVEL',
                            value_name='DROUGHT_AREA',

                            )
    ).mark_area(
        color="lightblue",
        interpolate='step-after',
        line=True
    ).encode(
        x='DATE:T',
        y='DROUGHT_AREA',
        color = 'DROUGHT_LEVEL',
        tooltip=['DATE','DROUGHT_LEVEL', 'DROUGHT_AREA']
    ).properties(
        width = 800, height=200
    )
    return drought_year_chart




def view_attribute_per_year(df, color_col='GSE_GWE_NORMALIZED', time_col = 'YEAR'):
    """
            This function charts out a geodataframe with a slider that controls the data in the dataframe by the position of the slider indicating a Year period
            The color of the values is scaled by the color_col in the dataframe
    
    """


    #Limit the time range so that the chart can be shown
    df = df[df[time_col] >= 2014]

    plss_gdf = gpd.read_file('../assets/plss_subbasin.geojson')
    plss_range = plss_gdf.dissolve(by='TownshipRange').reset_index()
    df_poly = plss_range.sjoin(df)
  
    min_year_num = df[time_col].min()
    max_year_num = df[time_col].max()
    slider = alt.binding_range(
        min=min_year_num,
        max=max_year_num,
        step=1,
        name="Year: ",
    )

    slider_selection = alt.selection_single(
        fields=[f"{time_col}"], bind=slider, name="Year:",
        init={f"{time_col}": 2014}
    )


    return alt.Chart(df_poly).mark_geoshape(
    ).encode( 
        color= alt.Color(f'{color_col}', scale=alt.Scale(scheme='purpleorange')),
        tooltip= list(df_poly.columns)
    ).transform_filter(
        slider_selection
    ).add_selection(
        slider_selection
    ).properties( 

        width=500,
        height=300
    )

   
def convert_point_polygons(gdf, dissolve_by_geometry :list ):
    """
         This function takes a geoframe with geometry containing points (these point were extracted from latitude and longitude)
         It spatially joins with the PLSS for San Joaquin River Basin and returns a dataframe with Polygon geomtery
    
        gdf: Geodataframe
        dissolve_by_geometry : Typically TownshipRange, can be county pr range as well

    """

    plss_gdf = gpd.read_file('../assets/plss_subbasin.geojson')
    plss_range = plss_gdf.dissolve(by=dissolve_by_geometry).reset_index()
    df_poly = plss_range.sjoin(gdf)

    return df_poly

