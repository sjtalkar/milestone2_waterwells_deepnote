import os
import numpy as np
import pandas as pd
import geopandas as gpd

from datetime import datetime
from typing import List
from lib.wsdatasets import WsGeoDataset


class ShortageReportsDataset(WsGeoDataset):
    """This class loads, processes and exports the Well Completion Reports dataset"""
    def __init__(self,
                 input_datafile: str = "../assets/inputs/shortage/shortage.csv",
                 ):
        WsGeoDataset.__init__(self, input_geofiles=[], input_datafile="")
        shortage_df = self._clean_shortage_reports(shortage_datafile=input_datafile)
        self.map_df = gpd.GeoDataFrame(
            shortage_df,
            geometry=gpd.points_from_xy(
                shortage_df.LONGITUDE,
                shortage_df.LATITUDE
            ))
        # Set the coordinate reference system so that we now have the projection axis
        self.map_df = self.map_df.set_crs("epsg:4326")
        
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


    def preprocess_map_df(self, features_to_keep: List[str], min_year: int = 2014):
        """This function keeps only the features in the features_to_keep list from the original geospatial data
        and from the year greater than or equal to min_year.

        :param features_to_keep: the list of features (columns) to keep.
        :param min_year: the minimum year to keep.
        """
        # Keep only the requested features
        self.map_df = self.map_df[features_to_keep]

    def compute_features_by_township(self, add_well_count: bool = True,
                                     add_well_usage_count: bool = False, count_feature: str = "REPORT_DATE",
                                     count_category_feature: str = "USE",
                                     fill_na_with_zero: bool = True):
        """This function computes the features in the features_to_compute list for each township

        :param features_to_average: the list of features to average.
        :param add_well_count: if True, a feature counting the number of wells per Township-Range is added.
        :param add_well_usage_count: if True, a feature counting the number of wells per usage type and Township-Range
        is added.
        :param count_feature: the feature to use for counting the number of wells in each Township-Range.
        :param count_category_feature: the feature to use for counting the number of wells per usage type.
        :param fill_na_with_zero: if True, the features with NaN data are filled with 0
        """
        self.keep_only_sjv_data()
        if add_well_count:
            # Get the well count by Township-Range and year
            township_features_df = self._get_aggregated_points_by_township(by=["TOWNSHIP_RANGE", "YEAR"],
                                                                          features_to_aggregate=[count_feature],
                                                                          aggfunc="count")
            township_features_df.rename(columns={count_feature: "WELL_COUNT"}, inplace=True)
        self.map_df = township_features_df


    def return_yearly_normalized_township_feature(self, feature_name: str, normalize_method: str = "sum"):
        """This function returns a dataframe with the feature values normalized by the "YEAR" column.

        :param feature_name: the name of the feature to normalize
        :return: a GeoDataFrame with an additional normalized feature column
        """
        self.map_df[f"YEARLY_{feature_name}"]= self.map_df.groupby('YEAR').transform(normalize_method)[feature_name]
        self.map_df[f"{feature_name}_NORMALIZED"] = self.map_df[feature_name] / self.map_df[f"YEARLY_{feature_name}"]
        
        return self.map_df