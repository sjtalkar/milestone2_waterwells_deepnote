import requests
import os
import pickle
import pandas as pd
import geopandas as gpd

from typing import List
from fiona.errors import DriverError
from lib.wsdatasets import WsGeoDataset


class PopulationDataset(WsGeoDataset):
    """This class loads, processes and exports the Population dataset"""
    def __init__(self, input_datafile: str = "../assets/inputs/population/population.csv",
                 tract_geofile: str = "../assets/inputs/population/tracts_map/tl_2019_06_tract.shp"):
        """Initialization of the Population dataset

        :param input_datafile: the file containing the population data
        :param tract_geofile: the file containing the shapefile of the population census Tracts
        """

        try:
            self._load_local_datasets(input_datafile, tract_geofile)
        except (FileNotFoundError, DriverError):
            self._download_datasets(input_datafile, tract_geofile)
            self._load_local_datasets(input_datafile, tract_geofile)

    def _load_local_datasets(self, input_datafile: str, tract_geofile: str):
        """This function loads the Population datasets from the local filesystem.

        :param input_datafile: the file containing the population data
        :param tract_geofile: the file containing the shapefile of the population census Tracts
        """
        print("Loading local datasets. Please wait...")
        WsGeoDataset.__init__(self, input_geofiles=[tract_geofile], input_datafile=input_datafile,
                              merging_keys=["TRACT_ID", "TRACT_ID"])
        print("Loading of datasets complete.")

    def _download_datasets(self, input_datafile: str, tract_geofile: str):
        """This function downloads the crops datasets from the web

        :param input_datafile: the file where to store the population data
        :param tract_geofile: the file where to store the shapefile of the population census Tracts
        """
        print(f"Data not found locally.")
        try:
            with open(r"../assets/inputs/population/census_api_token.pickle", "rb") as token_file:
                token = pickle.load(token_file)
        except FileNotFoundError:
            print("""ERROR: No API token pickle file found in ../assets/inputs/population/census_api_token.pickle.
            Please create a pickle file containing the Census API token.
            Go to https://api.census.gov/data/key_signup.html to receive your own API token.""")
            exit(1)
        os.makedirs(os.path.dirname(input_datafile), exist_ok=True)
        population_df = pd.DataFrame()
        # For the data for the years 2014 and 2016 we can't use wildcards for the counties, so we need to
        # loop through the counties in the San Joauin Valley and get the data for each county.
        sjv_county_codes = ["001", "005", "009", "013", "019", "029", "031", "039", "043", "047", "067", "069", "077",
                            "079", "099", "107", "109"]
        population_feature_mapping = {
            "2014": {"Tot_Population_ACS_10_14": "TOTAL_POPULATION"},
            "2016": {"Tot_Population_ACS_12_16": "TOTAL_POPULATION"},
            "2017": {"Tot_Population_ACS_13_17": "TOTAL_POPULATION"},
            "2018": {"Tot_Population_ACS_14_18": "TOTAL_POPULATION"},
            "2019": {"Tot_Population_ACS_15_19": "TOTAL_POPULATION"}
        }
        census_data_api_baseurl = {
            "2014": "https://api.census.gov/data/2016/pdb/tract?get=LAND_AREA,Tot_Population_ACS_10_14&for=tract:*",
            "2016": "https://api.census.gov/data/2018/pdb/tract?get=LAND_AREA,Tot_Population_ACS_12_16&for=tract:*"
        }
        for year in census_data_api_baseurl:
            print(f"Downloading American Community Survey {year} population estimates data. Please wait...")
            for county in sjv_county_codes:
                url = census_data_api_baseurl[year] + f"&in=county:{county}&in=state:06&key={token}"
                county_data = requests.get(url).json()
                county_df = pd.DataFrame(county_data[1:], columns=county_data[0])
                county_df["YEAR"] = int(year)
                county_df["TRACT_ID"] = county_df["state"] + county_df["county"] + county_df["tract"]
                county_df.rename(columns=population_feature_mapping[year], inplace=True)
                county_df = county_df[["TRACT_ID", "YEAR", "TOTAL_POPULATION", "LAND_AREA"]]
                population_df = pd.concat([population_df, county_df], axis=0)
        # For the other years we can use wildcards for the counties, so we can just get in one API call
        census_data_api_url = {
            "2017": "https://api.census.gov/data/2019/pdb/tract?get=LAND_AREA,Tot_Population_ACS_13_17&for=tract:*" \
                    f"&in=county:*&in=state:06&key={token}",
            "2018": "https://api.census.gov/data/2020/pdb/tract?get=LAND_AREA,Tot_Population_ACS_14_18&for=tract:*" \
                    f"&in=county:*&in=state:06&key={token}",
            "2019": "https://api.census.gov/data/2021/pdb/tract?get=LAND_AREA,Tot_Population_ACS_15_19&for=tract:*" \
                    f"&in=county:*&in=state:06&key={token}",
        }
        for year in census_data_api_url:
            print(f"Downloading American Community Survey {year} population estimates data. Please wait...")
            year_data = requests.get(census_data_api_url[year]).json()
            year_df = pd.DataFrame(year_data[1:], columns=year_data[0])
            year_df["YEAR"] = int(year)
            year_df["TRACT_ID"] = year_df["state"] + year_df["county"] + year_df["tract"]
            year_df.rename(columns=population_feature_mapping[year], inplace=True)
            year_df = year_df[["TRACT_ID", "YEAR", "TOTAL_POPULATION", "LAND_AREA"]]
            population_df = pd.concat([population_df, year_df], axis=0)
        population_df.to_csv(input_datafile, index=False)
        print("Downloading the geospatial data of the population census Tracts. Please wait...")
        tract_url = "https://www2.census.gov/geo/tiger/TIGER2019/TRACT/tl_2019_06_tract.zip"
        self._download_and_extract_zip_file(url=tract_url,
                                            extract_dir=os.path.dirname(tract_geofile))
        print("Downloads complete.")

    def preprocess_map_df(self, features_to_keep: List[str]):
        """This function preprocesses the geospatial Tract data

        :param features_to_keep: the list of features (columns) to keep.
        """
        self.map_df = gpd.clip(self.map_df, self.ca_boundaries.geometry[0])
        self.map_df["TRACT_ID"] = self.map_df["STATEFP"] + self.map_df["COUNTYFP"] + self.map_df["TRACTCE"]
        self.map_df = self.map_df[features_to_keep]

    def preprocess_data_df(self):
        """This function preprocesses the Soil data dataset by:
        * filling the map unit with soil taxonomy orders as NaN with the description in the "compname" column
        * merge the soil taxonomy order and hydrologic group as one SOIL_TYPE feature
        * use "max polling" on each map unit to assign it only the dominant SOIL_TYPE
        * extract only the columns: "mukey", "DOMINANT_SOIL_TYPE"
        """
        self.data_df["POPULATION_DENSITY"] = self.data_df["TOTAL_POPULATION"] / self.data_df["LAND_AREA"]
        self.data_df = self.data_df[["TRACT_ID", "POPULATION_DENSITY", "YEAR"]]
        self.data_df["TRACT_ID"] = self.data_df["TRACT_ID"].astype(str)
        self.data_df["TRACT_ID"] = "0" + self.data_df["TRACT_ID"]
        # Compute the 2015 population density as the mean between the 2014 and 2016 population density
        data_2015_df = self.data_df[self.data_df["YEAR"].isin([2014, 2016])].copy()
        data_2015_df.drop(columns=["YEAR"], inplace=True)
        data_2015_df.groupby("TRACT_ID").agg({"POPULATION_DENSITY": "mean"})
        data_2015_df["YEAR"] = 2015
        self.data_df = pd.concat([self.data_df, data_2015_df], axis=0)
        # Estimate the population density for the years > 2019
        for year in range(2020, 2022):
            pop_post_2019_df = self.data_df[self.data_df["YEAR"] == 2019].copy()
            pop_post_2019_df["YEAR"] = year
            self.data_df = pd.concat([self.data_df, pop_post_2019_df], axis=0)
        self.data_df.reset_index(inplace=True, drop=True)
