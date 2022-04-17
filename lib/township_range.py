import geopandas as gpd
import pandas as pd
from lib.wsdatasets import WsGeoDataset


class TownshipRanges(WsGeoDataset):
    """
    This class loads, processes and exports the Township-Ranges areas
    """
    def __init__(self):
        WsGeoDataset.__init__(self, input_geofiles=[])
        self.map_df = self.sjv_township_range_df.copy()

    def get_counties_in_sjv(self):
        """This function returns the geospatial shapes of the counties clipped by the San Joaquin Valley border"""
        return gpd.clip(self.ca_counties_df, self.sjv_boundaries)

    def compute_township_area(self):
        """This function computes the area of each Township-Range in the dataset"""
        self.map_df = self.map_df.to_crs(epsg=3347)
        self.map_df["AREA"] = self.map_df.area
        self.map_df = self.map_df.to_crs(epsg=4326)

    def add_years_to_dataset(self):
        """This function adds the 2014-2021 years to the dataset"""
        self.map_df["YEAR"] = 2014
        for year in range(2015, 2022):
            year_df = self.map_df[self.map_df.YEAR == 2014].copy()
            year_df["YEAR"] = year
            self.map_df = pd.concat([self.map_df, year_df], axis=0)
