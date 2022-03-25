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
                        time_value:str,
                        drop_nulls=False):
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

   
    df = df[df[time_aggregate_column] >= time_value]
    df[time_aggregate_column] = df[time_aggregate_column].astype(float).astype(int)

    # If the aggregation is on a categorical column, we do not need it to be a number
    if  agg_func != 'count': 
     if drop_nulls:
        df.dropna(subset=[col_to_aggr], inplace=True)
        df = df[df[col_to_aggr] != ''].copy()
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


def merge_data_plss( input_file_name, output_file_name):
    """  
        - This function reads a input file, creates a dataframe that will have latitude and longitude 
        - It was created for precipitation and reservoir datasets that did not get merged with PLSS and so do not 
        - have a geometry column stored in the output.
        - For these dataframes, we end up with very few rows when joining with plss
        - Create a GeoDataFrame when starting from a regular DataFrame that has latitudinal and longitudinal coordinates. In the well completion reports, we have columns for latitude and longitude.
        - A GeoDataFrame needs a shapely object.
        - We use geopandas points_from_xy() to transform Longitude and Latitude into a list of shapely.Point objects and set it as a geometry while creating the GeoDataFrame.
        - Once we have a GeoDataframe with the points in the coordinate reference system, we spatially join to the California PLSS GeoJSON to map to the closest TownshipRange using sjoin method in geopandas.
    
    """
    df = pd.read_csv(input_file_name)

    plss_gdf = gpd.read_file('../assets/plss_subbasin.geojson')
    plss_range = plss_gdf.dissolve(by='TownshipRange').reset_index()
    
    # create wells geodataframe
    df_gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.LONGITUDE, df.LATITUDE))
    #Set the coordinate reference system (the projection that denote the axis for the points)
    df_gdf = df_gdf.set_crs('epsg:4326')

    # spatial join based on geometry
    df_plss = df_gdf.sjoin(plss_range, how="left")

    # drop the ones that aren't in the san joaquin valley basin
    df_plss = df_plss.dropna(subset=['MTRS'])
    
    df_plss.to_csv(output_file_name, index=False)
    return df_plss    