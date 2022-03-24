import numpy as np
import pandas as pd
import altair as alt
import geopandas as gpd

from typing import List
from lib.wsdatasets import WsGeoDataset

class GroundwaterDataset(WsGeoDataset):
    """This class loads, processes and exports the Well Completion Reports dataset"""
    def __init__(self,
                 input_geofiles: List[str] = [],
                 input_datafile: str = "../assets/inputs/groundwater/groundwater.csv"):
        WsGeoDataset.__init__(self, input_geofiles=input_geofiles, input_datafile=input_datafile,
                              merging_keys=["SITE_CODE", "SITE_CODE"])
        # Initializes the Geospatial map_df dataset based on the LATITUDE & LONGITUDE features of the
        # groundwater_stations dataset
        groundwaterstations_df = pd.read_csv(r"../assets/inputs/groundwater/groundwater_stations.csv")
        self.map_df = gpd.GeoDataFrame(
            groundwaterstations_df,
            geometry=gpd.points_from_xy(
                groundwaterstations_df.LONGITUDE,
                groundwaterstations_df.LATITUDE
            ))
        #Set the coordinate reference system so that we now have the projection axis
        self.map_df = self.map_df.set_crs('epsg:4326')

    def preprocess_data_df(self, features_to_keep: List[str] = ['SITE_CODE', 'GSE_GWE', 'YEAR']):
        """This function keeps the GSE_GWE feature for the spring months.

        :param features_to_keep: the list of features (columns) to keep.
        """
        # create simple year and month columns
        self.data_df['MSMT_DATE'] = pd.to_datetime(self.data_df.MSMT_DATE)
        self.data_df['YEAR'] = self.data_df['MSMT_DATE'].dt.year
        self.data_df['MONTH'] = self.data_df['MSMT_DATE'].dt.month
        # Retain only those records that have Groundwater measurements
        self.data_df = self.data_df[~self.data_df['GSE_GWE'].isnull()] # 2325741
        # drop the rows that have incorrect measurements that of 0 or less
        self.data_df = self.data_df[self.data_df['GSE_GWE'] > 0]
        # filter for just the spring measurements
        spring_months = [1,2,3,4]
        self.data_df = self.data_df[self.data_df['MONTH'].isin(spring_months)]
        # Keep only the necessary features
        self.data_df = self.data_df[features_to_keep]

    def preprocess_map_df(self):
        """This function keeps only the SITE_CODE, COUNTY and geometry features in the original geospatial data."""
        self.map_df = self.map_df[['SITE_CODE','COUNTY_NAME','geometry']]

    def draw_mising_data_chart(self):
        """
            This function charts the percentage missing data in the data file read in

                MOVE TO BASE CLASS?
        """

        df = self.output_df
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
