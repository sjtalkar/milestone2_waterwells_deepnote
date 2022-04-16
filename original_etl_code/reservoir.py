import json
import pygeos
import datetime
import requests

import numpy as np
import pandas as pd
import geopandas as gpd

from bs4 import BeautifulSoup

from typing import List, Tuple, Dict
from lib.wsdatasets import WsGeoDataset


class ReservoirDataset:
    """
        This class loads the reservoir dataset

        The range of years for which the data is to be collected  is captured in 

        year_start : e.g. '2013-01-01'
        year_end : e.g. '2023-01-01' This is one year beyond the range
        output_file_directory : directory to store both weekly and yearly granularity file e.g. = /work/milestone2_waterwells_deepnote/assets/inputs/reservoir

    """
    def __init__(self, year_start, year_end, output_file_directory):
        self.year_start = year_start
        self.year_end = year_end
        self.output_file_directory = output_file_directory
            
            
    def scrape_weekly_reservoir_data(self):
        """
            This function loops through a set of years in a list
            It creates URLS at weekly intervals for reservoir data
            It creates one dataframe containing reservoir data at weekly level for years for which we have data
        """
        #period = pd.to_datetime(self.year_end).year - pd.to_datetime(self.year_start).year
        #year_list = pd.date_range(self.year_start, periods = period , freq='YS')
        #for year_start_date in year_list:

        all_years_reservoir_data = pd.DataFrame()
        
        for year_start_date in [ "2013-01-01",  "2014-01-01", "2015-01-01", "2016-01-01", "2017-01-01", "2018-01-01", "2019-01-01", "2020-01-01", "2021-01-01", "2022-01-01"]:

            #inclusive controls whether to include start and end that are on the boundary. The default, “both”, includes boundary points on either end.
            date_list = pd.date_range(year_start_date, periods=53, freq='W')
            date_list = [week_date.strftime("%Y%m%d") for week_date in date_list if pd.to_datetime(week_date).year ==  pd.to_datetime(year_start_date).year]
    
            #Create a dataframe for all dates of a year
            full_year_dataframe = pd.DataFrame()
            for one_date in date_list:
                url=f"https://cdec.water.ca.gov/reportapp/javareports?name=RES.{one_date}"


                # Make a GET request to fetch the raw HTML content
                html_content = requests.get(url).text

                # Parse the html content
                soup = BeautifulSoup(html_content, "lxml")

                reservoir_table = soup.find("table", attrs={"id":"RES", "class": "data"})
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

                #Form a data_table for the collection of weekly rows        
                data_table = pd.DataFrame(all_rows_list )
                data_table['date'] = pd.to_datetime(f'{one_date}')
                data_table.columns = reservoir_table_header + ['date']
        
                #Form a yearly table
                if full_year_dataframe.empty:
                        full_year_dataframe = data_table
                else:
                        full_year_dataframe = full_year_dataframe.append(data_table)

            if full_year_dataframe.empty:
                continue

            #Combine this years data with past years
            if all_years_reservoir_data.empty:
                all_years_reservoir_data = full_year_dataframe 
            else:
                all_years_reservoir_data  = all_years_reservoir_data.append(full_year_dataframe)

        
        all_years_reservoir_data.rename(columns={'% of Capacity':'PCT_OF_CAPACITY'}, inplace=True)
        all_years_reservoir_data  = all_years_reservoir_data[~all_years_reservoir_data['Reservoir Name'].str.contains('Total')].copy()
        #Add a year and month column
        all_years_reservoir_data['YEAR']  = all_years_reservoir_data.date.dt.year
        all_years_reservoir_data['MONTH']  = all_years_reservoir_data.date.dt.month
        all_years_reservoir_data.rename(columns={'StaID': 'STATION_ID'}, inplace=True)

        self.all_years_reservoir_data = all_years_reservoir_data
        return all_years_reservoir_data



    def get_reservoir_station_data(self):
        """
            This function retrieves the station location data for reservoirs through webscraping
        """
        
        url=f"https://cdec.water.ca.gov/reportapp/javareports?name=DailyRes"

        # Make a GET request to fetch the raw HTML content
        html_content = requests.get(url).text

        # Parse the html content
        soup = BeautifulSoup(html_content, "lxml")

        station_table = soup.find("table", attrs={"id":"DailyRes_LIST", "class": "data"})

        all_rows_list = []
        for eachRow in station_table.find_all("tr"):
            this_row = []
            for  td in eachRow.find_all("td"):
                this_row.append(td.text.strip())

            if this_row and len(this_row) > 1:
                all_rows_list.append(this_row)
        station_table = pd.DataFrame(all_rows_list )
        station_table.columns = station_table.iloc[0,:]
        station_table =  station_table.iloc[2:,:].copy()
        station_table.rename(columns={'ID':'STATION_ID'}, inplace=True)
        station_table.drop(columns=['OPERATOR AGENCY'], inplace = True)

        self.station_table = station_table

        return station_table

        
    def save_precipitation_data(self, reservoir_station_df, granularity):
        """
            This function saves weekly and yearly level reservoir data in separate CSV files
        """
        if granularity == 'weekly':
            reservoir_station_df.to_csv(fr"{self.output_file_directory}/weekly_reservoir_station_data.csv", index=False)
        else:
            reservoir_station_df.to_csv(fr"{self.output_file_directory}/reservoir_station_data.csv", index=False)

    def retrieve_merge_reservoir_stations(self):
        """
            This function calls web scraping functions for weekly reservoir data and the stattion and merges the two
            It saves off the weekly data in a file
            It then merges the two dataframe to link stations to their locations
            It averages the reservoir percent of capacity storage to the yearly level
            It stores the file 
        """
        all_years_reservoir_data = self.all_years_reservoir_data 

        #Save off the weekly data as a check
        self.save_precipitation_data(all_years_reservoir_data, 'weekly')
        
        station_table = self.station_table

        reservoir_station_df = all_years_reservoir_data.merge(station_table, how='inner', on='STATION_ID')
        reservoir_station_df['PCT_OF_CAPACITY'] = pd.to_numeric(reservoir_station_df['PCT_OF_CAPACITY'], errors='coerce')
    
        reservoir_station_df = reservoir_station_df.groupby(['STATION_ID', 'YEAR', 'LATITUDE' , 'LONGITUDE', 'COUNTY']).agg(PCT_OF_CAPACITY=('PCT_OF_CAPACITY', 'mean')).reset_index()
        
        reservoir_station_df = reservoir_station_df[['STATION_ID','PCT_OF_CAPACITY', 'YEAR', 'LATITUDE' , 'LONGITUDE', 'COUNTY'] ].copy()
        self.reservoir_station_df = reservoir_station_df
        self.save_precipitation_data(reservoir_station_df, 'yearly')
        return reservoir_station_df   
    