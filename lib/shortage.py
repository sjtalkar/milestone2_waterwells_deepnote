import os
import json
import pygeos
import numpy as np
import pandas as pd
import altair as alt
import geopandas as gpd

from datetime import datetime

from typing import List, Tuple, Dict
from lib.wsdatasets import WsGeoDataset

class ShortageDataset(WsGeoDataset):
    """This class loads, processes and exports the Well Completion Reports dataset"""
    def __init__(self,
                 input_geofiles: List[str] = ["../assets/inputs/common/plss_subbasin.geojson"],
                 input_datafile: str = "../assets/inputs/shortage/shortage.csv",
                 ):
        WsGeoDataset.__init__(self, input_datafile=input_datafile)
                              


    def _read_input_datafile(self, input_datafile: str, input_datafile_format: str = "csv") -> pd.DataFrame:
        """This functions loads additional data not provided together with the map data.

        :param input_datafile: the path to the file containing the additional data dataset
        :param input_datafile_format: the format of the input_datafile (e.g. "csv", "xlsx", etc.)
        :return: the pandas DataFrame containing the additional data to be merged with the map data
        """
        return pd.read_csv(input_datafile)

    def clean_shortage_reports(self):
        """
            This function cleans the dataframe to keep only featured columns and set the column name appropriately
        """
        
        shortage_df = self.data_df

        shortage_df =shortage_df [['Report Date', 'County', 'LATITUDE', 'LONGITUDE',   'Status', 'Shortage Type', 'Primary Usages']].copy()
        shortage_df = shortage_df.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
        shortage_df['Report Date'] = pd.to_datetime(shortage_df['Report Date']) 
        #convert case to upper case
        shortage_df.columns  = [col.upper().replace(' ', '_') for col in shortage_df] 

        # create simple year and month columns
        shortage_df['YEAR'] = pd.DatetimeIndex(shortage_df['REPORT_DATE']).year
        shortage_df['MONTH'] = pd.DatetimeIndex(shortage_df['REPORT_DATE']).month

        self.shortage_df = shortage_df
        return shortage_df
      

    def merge_data_plss(self):
        """  Create a GeoDataFrame when starting from a regular DataFrame that has latitudinal and longitudinal coordinates. In the well
              completion reports, we have columns for latitude and longitude.
            - A GeoDataFrame needs a shapely object.
            - We use geopandas points_from_xy() to transform Longitude and Latitude into a list of shapely.Point objects and set it as a 
              geometry while creating the GeoDataFrame.
            - Once we have a GeoDataframe with the points in the coordinate reference system, we spatially join to the California PLSS 
              GeoJSON to map to the closest TownshipRange using sjoin method in geopandas.
        
            MOVE TO BASE CLASS?
        """

        df = self.shortage_df

        # create wells geodataframe
        shortage_gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.LONGITUDE, df.LATITUDE))
        #Set the coordinate reference system (the projection that denote the axis for the points)
        shortage_gdf = shortage_gdf.set_crs('epsg:4326')

        # spatial join based on geometry
        shortage_plss = shortage_gdf.sjoin(self.map_df, how="left")

        # drop the ones that aren't in the san joaquin valley basin
        shortage_plss = shortage_plss.dropna(subset=['MTRS'])
        
        self.shortage_plss = shortage_plss
        shortage_plss.to_csv("../assets/outputs/shortage_clean.csv", index=False)
        return shortage_plss 


    def draw_mising_data_chart(self, df):
        """
            This function charts the percentage missing data in the data file read in

                MOVE TO BASE CLASS?
        """

        percent_missing = df.isnull().sum() / len(df)
        missing_value_df = pd.DataFrame({'column_name': df.columns,
                                        'percent_missing': percent_missing})
        missing_value_df.sort_values('percent_missing', ascending = False, inplace=True)

        sort_list = list(missing_value_df['column_name'])
        chart = alt.Chart(missing_value_df
                        ).mark_bar(
                            ).encode(
                        y =alt.Y("sum(percent_missing)", stack="normalize", axis=alt.Axis(format='%')),
                        x = alt.X('column_name:N', sort=sort_list),
                        color=alt.value("orange"),
                        tooltip = ['column_name', 'percent_missing']
                        )
        
        
        text = chart.transform_calculate(
            position = 'datum.percent_missing + 0.05 * datum.percent_missing / abs(datum.percent_missing)'
        ).mark_text(
            align='center', 
            fontSize=10,
            color='black'
        ).encode(
            y='position:Q',
            text=alt.Text('percent_missing:Q', format='.0%'),
        )
        return chart + text 
