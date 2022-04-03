import requests
import pandas as pd
import geopandas as gpd

from bs4 import BeautifulSoup
from typing import List
from lib.wsdatasets import WsGeoDataset


class ReservoirDataset(WsGeoDataset):
    """This class loads, processes the precipitation dataset. The range of years for which the data is to be collected
    is captured in
    """
    def __init__(self, year_start: int = 2013, year_end: int = 2022):
        """ The initialization of the ReservoirDataset class automatically scrapes the weekly reservoir data
        for the state of California in the data_df dataframe and downloads the reservoir station location into the
        map_df dataframe.

        :param year_start: The year to start collecting the data from.
        :param year_end: The year to end collecting the data from.
        """
        # Initialize the parent class with the bare minimum, without loading any data from file (outside of the
        # San Joaquin Valley Township data) as the data are scraped from the web.
        WsGeoDataset.__init__(self, input_geofiles=[], merging_keys=["STATION_ID", "STATION_ID"])
        self.year_start = year_start
        self.year_end = year_end
        # Scrape the precipitation data and the precipitation geospatial data from the web
        self.data_df = self._scrape_weekly_reservoir_data()
        self.map_df = self._retrieve_stations_geospatial_data()

    def _scrape_weekly_reservoir_data(self):
        """
            This function loops through a set of years in a list
            It creates URLS at weekly intervals for reservoir data
            It creates one dataframe containing reservoir data at weekly level for years for which we have data
        """
        all_years_reservoir_data = pd.read_csv("../assets/outputs/weekly_reservoir_station_data.csv")
        if not all_years_reservoir_data.empty:
            all_years_reservoir_data['PCT_OF_CAPACITY'] = pd.to_numeric(all_years_reservoir_data['PCT_OF_CAPACITY'],
                                                                        errors='coerce')
            all_years_reservoir_data = (all_years_reservoir_data.groupby(
                                            ['Reservoir Name', 'STATION_ID', 'YEAR']
                                            ).agg(PCT_OF_CAPACITY=('PCT_OF_CAPACITY', 'mean')).reset_index())
            return all_years_reservoir_data

        for year_start_date in ["2013-01-01",  "2014-01-01", "2015-01-01", "2016-01-01", "2017-01-01", "2018-01-01",
                                "2019-01-01", "2020-01-01", "2021-01-01", "2022-01-01"]:

            # inclusive controls whether to include start and end that are on the boundary. The default, “both”,
            # includes boundary points on either end.
            date_list = pd.date_range(year_start_date, periods=53, freq='W')
            date_list = [week_date.strftime("%Y%m%d") for week_date in date_list if
                         pd.to_datetime(week_date).year == pd.to_datetime(year_start_date).year]
    
            # Create a dataframe for all dates of a year
            full_year_dataframe = pd.DataFrame()
            for one_date in date_list:
                url = f"https://cdec.water.ca.gov/reportapp/javareports?name=RES.{one_date}"
                # Make a GET request to fetch the raw HTML content
                html_content = requests.get(url).text
                # Parse the html content
                soup = BeautifulSoup(html_content, "lxml")
                reservoir_table = soup.find("table", attrs={"id": "RES", "class": "data"})
                if reservoir_table is None:
                    continue
                reservoir_table_header = reservoir_table.thead.find_all("th")  
                reservoir_table_header = [th.text.strip() for th in reservoir_table_header]
                reservoir_table_header = [elm.strip() for elm in reservoir_table_header[1:]]
                reservoir_table_rows = reservoir_table.find_all('tr', {'class': 'white'})
                all_rows_list = []
                for eachTableRow in reservoir_table_rows:
                    this_row = []
                    for td in eachTableRow.find_all("td"):
                        this_row.append(td.text.strip())

                    if this_row and len(this_row) > 1:
                        all_rows_list.append(this_row)

                # Form a data_table for the collection of weekly rows
                data_table = pd.DataFrame(all_rows_list)
                data_table['date'] = pd.to_datetime(f'{one_date}')
                data_table.columns = reservoir_table_header + ['date']
                # Form a yearly table
                if full_year_dataframe.empty:
                    full_year_dataframe = data_table
                else:
                    full_year_dataframe = pd.concat([full_year_dataframe, data_table], axis=0)
            if full_year_dataframe.empty:
                continue
            # Combine this years data with past years
            if all_years_reservoir_data.empty:
                all_years_reservoir_data = full_year_dataframe 
            else:
                all_years_reservoir_data = pd.concat([all_years_reservoir_data, full_year_dataframe], axis=0)
        all_years_reservoir_data.rename(columns={'% of Capacity': 'PCT_OF_CAPACITY'}, inplace=True)
        all_years_reservoir_data = all_years_reservoir_data[~all_years_reservoir_data['Reservoir Name'].
            str.contains('Total')].copy()
        # Add a year and month column
        all_years_reservoir_data['YEAR'] = all_years_reservoir_data.date.dt.year
        all_years_reservoir_data.rename(columns={'StaID': 'STATION_ID', 'Reservoir Name': 'RESERVOIR_NAME'},
                                        inplace=True)
        all_years_reservoir_data = (all_years_reservoir_data.groupby(
                                            ['STATION_ID', 'YEAR']
                                            ).agg(PCT_OF_CAPACITY=('PCT_OF_CAPACITY', 'mean')).reset_index())
        return all_years_reservoir_data

    def _get_reservoir_station_data(self):
        """
            This function retrieves the station location data for reservoirs through webscraping
        """
        # Make a GET request to fetch the raw HTML content
        html_content = requests.get("https://cdec.water.ca.gov/reportapp/javareports?name=DailyRes").text
        # Parse the html content
        soup = BeautifulSoup(html_content, "lxml")
        station_table = soup.find("table", attrs={"id": "DailyRes_LIST", "class": "data"})
        all_rows_list = []
        for eachRow in station_table.find_all("tr"):
            this_row = []
            for td in eachRow.find_all("td"):
                this_row.append(td.text.strip())

            if this_row and len(this_row) > 1:
                all_rows_list.append(this_row)
        station_table = pd.DataFrame(all_rows_list)
        station_table.columns = station_table.iloc[0, :]
        station_table = station_table.iloc[2:, :].copy()
        station_table.rename(columns={'ID': 'STATION_ID'}, inplace=True)
        station_table.drop(columns=['OPERATOR AGENCY'], inplace=True)
        return station_table
        
    def _save_precipitation_data(self, reservoir_station_df, granularity):
        """
            This function saves weekly and yearly level reservoir data in separate CSV files
        """
        if granularity == 'weekly':
            reservoir_station_df.to_csv(r"../assets/inputs/reservoir/weekly_reservoir_station_data.csv", index=False)
        else:
            reservoir_station_df.to_csv(r"../assets/inputs/reservoir/reservoir_station_data.csv", index=False)

    def _retrieve_stations_geospatial_data(self):
        """This function retrieves all the precipitation stations geospatial data. It scraps the web for precipitation
        data at daily and monthly level and extracts the latitude and longitude of all stations and returns it in a
        Geospatial dataframe.

        :return: The geospatial dataframe containing the latitude and longitude of all weather stations in California
        """
        station_table = self._get_reservoir_station_data()
        all_stations_geodf = gpd.GeoDataFrame(
            station_table,
            geometry=gpd.points_from_xy(
                station_table.LONGITUDE,
                station_table.LATITUDE
            ),
            crs="epsg:4326")
        return all_stations_geodf

    def preprocess_map_df(self, features_to_keep: List[str]):
        """This function keeps only the features in the features_to_keep list from the original geospatial data.

        :param features_to_keep: the list of features (columns) to keep."""
        self.map_df = self.map_df[features_to_keep].drop_duplicates()
        
    
    