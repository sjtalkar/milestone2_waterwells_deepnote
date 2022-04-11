import os
import requests
import pandas as pd
import geopandas as gpd

from datetime import datetime
from typing import List
from lib.wsdatasets import WsGeoDataset


class ShortageReportsDataset(WsGeoDataset):
    """This class loads, processes and exports the Water Shortage Reports dataset"""
    def __init__(self, input_datafile: str = "../assets/inputs/shortage/shortage.csv"):
        WsGeoDataset.__init__(self, input_geofiles=[])
        try:
            self._load_local_datasets(input_datafile)
        except FileNotFoundError:
            self._load_local_datasets(input_datafile)
            self._download_datasets(input_datafile)

    def _load_local_datasets(self, input_datafile: str):
        """This function loads the datasets from the local filesystem

        :param input_datafile: the path to the local data file
        """
        print("Loading local datasets. Please wait...")
        WsGeoDataset.__init__(self, input_geofiles=[], input_datafile=input_measurements_file,
                              merging_keys=["SITE_CODE", "SITE_CODE"])
        shortage_df = self._clean_shortage_reports(shortage_datafile=input_datafile)
        self.map_df = gpd.GeoDataFrame(
            shortage_df,
            geometry=gpd.points_from_xy(
                shortage_df.LONGITUDE,
                shortage_df.LATITUDE
            ))
        # Set the coordinate reference system so that we now have the projection axis
        self.map_df = self.map_df.set_crs("epsg:4326")
        print("Loading of datasets complete.")

    def _download_datasets(self, input_datafile: str):
        """This function downloads the datasets from the web

        :param input_datafile: the path and name of the file where to store the data"""
        print("Data not found locally.\nDownloading the water shortage reports dataset. Please wait...")
        os.makedirs(os.path.dirname(input_datafile), exist_ok=True)
        shortage_url = "https://data.cnra.ca.gov/dataset/2cf184d1-2d34-46cc-8bb0-1dec86b6caf6/resource/e1fd9f48-a613-4567-8042-3d2e064d77c8/download/householdwatersupplyshortagereportingsystemdata.csv"
        shortage_content = requests.get(shortage_url).text
        with open(input_datafile, "w", encoding="utf-8") as f:
            f.write(shortage_content)
        print("Downloads complete.")
        
    def _clean_shortage_reports(self, shortage_datafile:str):
        """
            This function cleans the dataframe to keep only featured columns and set the column name appropriately
        """
        
        shortage_df = pd.read_csv(shortage_datafile)

        shortage_df =shortage_df [['Report Date', 'County', 'LATITUDE', 'LONGITUDE', 'Status', 'Shortage Type', 'Primary Usages']].copy()
        shortage_df = shortage_df.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
        shortage_df['Report Date'] = pd.to_datetime(shortage_df['Report Date']) 
        #convert case to upper case
        shortage_df.columns  = [col.upper().replace(' ', '_') for col in shortage_df] 

        # create simple year and month columns
        shortage_df['YEAR'] = pd.DatetimeIndex(shortage_df['REPORT_DATE']).year
        shortage_df['MONTH'] = pd.DatetimeIndex(shortage_df['REPORT_DATE']).month
        ## Now that year and month have been extracted, the report date can serve to identify the well
        shortage_df['REPORT_DATE'] = "SHORTAGE_REPORTED_" + shortage_df['REPORT_DATE'].astype('str')
        shortage_df.rename(columns={"PRIMARY_USAGES":'USE'})
        return shortage_df

    def compute_features_by_township(self, count_feature: str = "REPORT_DATE"):
        """This function computes the features in the features_to_compute list for each township

        :param count_feature: the feature to use for counting the number of shortage reports in each Township-Range.
        """
        self.keep_only_sjv_data()
        # Get the water shortage reports count by Township-Range and year
        township_features_df = self._get_aggregated_points_by_township(by=["TOWNSHIP_RANGE", "YEAR"],
                                                                      features_to_aggregate=[count_feature],
                                                                      aggfunc="count")
        township_features_df.rename(columns={count_feature: "SHORTAGE_COUNT"}, inplace=True)
        self.map_df = township_features_df
