import json
import pygeos
import numpy as np
import pandas as pd
import altair as alt
import geopandas as gpd

from datetime import datetime

from typing import List, Tuple, Dict
from lib.wsdatasets import WsGeoDataset

class GroundwaterDataset(WsGeoDataset):
    """This class loads, processes and exports the Well Completion Reports dataset"""
    def __init__(self,
                 input_geofiles: List[str] = ["../assets/inputs/common/plss_subbasin.geojson"],
                 input_datafile: str = "../assets/inputs/groundwater/groundwater.csv",
                 ):
        WsGeoDataset.__init__(self, input_geofiles=input_geofiles, input_datafile=input_datafile)
                              


    def _read_input_datafile(self, input_datafile: str, input_datafile_format: str = "csv") -> pd.DataFrame:
        """This functions loads additional data not provided together with the map data.

        :param input_datafile: the path to the file containing the additional data dataset
        :param input_datafile_format: the format of the input_datafile (e.g. "csv", "xlsx", etc.)
        :return: the pandas DataFrame containing the additional data to be merged with the map data
        """
        return pd.read_csv(input_datafile)

    def clean_groundwater_data(self):
        groundwater_df = self.data_df.copy()
        groundwaterstations_df = pd.read_csv(r"../assets/inputs/groundwater/groundwater_stations.csv")
        
        groundwater_df.drop(columns=['Unnamed: 0', '_id', 'WLM_ORG_NAME', 'COOP_ORG_NAME', 'WLM_ACC_DESC', 'WLM_QA_DESC', 'WLM_DESC', 'MSMT_CMT', 'MONITORING_PROGRAM' ], inplace=True)
        groundwaterstations_df = groundwaterstations_df.loc[:,['SITE_CODE','LONGITUDE','LATITUDE','GSE','COUNTY_NAME','WELL_USE']].copy()

        # create simple year and month columns
        groundwater_df['MSMT_DATE'] = pd.to_datetime(groundwater_df.MSMT_DATE)
        groundwater_df['YEAR'] = groundwater_df['MSMT_DATE'].dt.year
        groundwater_df['MONTH'] = groundwater_df['MSMT_DATE'].dt.month

        # Retain only those records that have Groundwater measurements
        groundwater_df = groundwater_df[~groundwater_df['GSE_GWE'].isnull()] # 2325741 
 
        # filter for just the spring measurements
        spring_months = [1,2,3,4]
        spring_months_groundwater = groundwater_df[groundwater_df['MONTH'].isin(spring_months)].copy() 
        # merge with station data for location info
        spring_month_groundwater_location = spring_months_groundwater.merge(groundwaterstations_df, on='SITE_CODE')
        
        # drop the rows that have incorrect measurements that of 0 or less
        spring_month_groundwater_location = spring_month_groundwater_location[spring_month_groundwater_location['GSE_GWE'] > 0]

        self.spring_month_groundwater_location = spring_month_groundwater_location

        return spring_month_groundwater_location
      
    # def preprocess_map_df(self, features_to_keep: List[str] = ["YEAR", "CROP_TYPE", "geometry"],
    #                       get_crops_details: bool=False):
    #     """This function preprocesses the well completion reports dataset extracting 
    #         pertinent features. 

    #     :param features_to_keep: the list of features (columns) to keep.
    #     :param get_drops_details: whether to extract the crops data at the crop level instead of the crop class level.
    #     """
      

    def merge_data_plss(self):
        """  Create a GeoDataFrame when starting from a regular DataFrame that has latitudinal and longitudinal coordinates. In the well completion reports, we have columns for latitude and longitude.
            - A GeoDataFrame needs a shapely object.
            - We use geopandas points_from_xy() to transform Longitude and Latitude into a list of shapely.Point objects and set it as a geometry while creating the GeoDataFrame.
            - Once we have a GeoDataframe with the points in the coordinate reference system, we spatially join to the California PLSS GeoJSON to map to the closest TownshipRange using sjoin method in geopandas.
        
            MOVE TO BASE CLASS?
        """

        # Follow the routine to create a GeoDataFrame
        gdf_spring_groundwater = gpd.GeoDataFrame(
            self.spring_month_groundwater_location, 
            geometry=gpd.points_from_xy(
                self.spring_month_groundwater_location.LONGITUDE, 
                self.spring_month_groundwater_location.LATITUDE
            ))

        #Set the coordinate reference system so that we now have the projection axis
        gdf_spring_groundwater = gdf_spring_groundwater.set_crs('epsg:4326')

        # match up based on longitude/latitude
        spring_groundwater_plss = gdf_spring_groundwater.sjoin(self.map_df, how="left")
      
        # drop the ones that aren't in a subbasin trs
        spring_groundwater_plss = spring_groundwater_plss.dropna(subset=['MTRS'])

        # Group wells that had multiple spring measurements in some years and get the average of  'GSE_GWE'
        spring_groundwater_group = (spring_groundwater_plss[['SITE_CODE', 'LATITUDE', 'LONGITUDE', 'geometry', 'TownshipRange','COUNTY_NAME','YEAR', 'GSE_GWE']]
                                    .dissolve(by=['SITE_CODE', 'LATITUDE', 'LONGITUDE','TownshipRange','COUNTY_NAME','YEAR'], aggfunc='mean').reset_index()
        )
        self.spring_groundwater_plss = spring_groundwater_group
        spring_groundwater_group.to_csv("../assets/outputs/spring_groundwater_levels_clean.csv", index=False)
        return spring_groundwater_group 


    def draw_mising_data_chart(self):
        """
            This function charts the percentage missing data in the data file read in

                MOVE TO BASE CLASS?
        """

        df = self.spring_month_groundwater_location
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
