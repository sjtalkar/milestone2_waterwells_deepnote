import os
import pickle
import requests
import concurrent.futures
import zipfile
import time
import numpy as np
import pandas as pd

from typing import Tuple
from datetime import datetime
from io import BytesIO
from tqdm import tqdm
from requests import RequestException


def download_and_extract_zip_file(url: str, extract_dir: str):
    """
    This function downloads a zip file and extracts it to the specified directory.

    :param url: the URL of the zip file to download
    :param extract_dir: the directory where to extract the zip file
    """
    # Download the dataset content
    zipfile_content = requests.get(url).content
    os.makedirs(extract_dir, exist_ok=True)
    # extract the zip files directly from the content
    with zipfile.ZipFile(BytesIO(zipfile_content)) as zf:
        # For each members of the archive
        for member in zf.infolist():
            # If it's a directory, continue
            if member.filename[-1] == "/": continue
            # Else write its content to the dataset root folder
            with open(os.path.join(extract_dir, os.path.basename(member.filename)),
                      "wb") as outfile:
                outfile.write(zf.read(member))


def download_population_raw_data(input_datafile: str = "../assets/inputs/population/population.csv",
                                 tract_geofile: str = "../assets/inputs/population/tracts_map/tl_2019_06_tract.shp"):
    """
    This functions downloads the raw data from the Census Bureau.

    :param input_datafile: the file where to store the yearly population estimates
    :param tract_geofile: the file were to store the Census Tracts geometries
    """
    print("Data not found locally.")
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
    # The population estimates for 2021 is not available from the ACS estimates API yet.
    # All other years population estimates are downloaded from the ACS estimates API. But that API does not provide
    # Tract LAND_AREA information so we use it from the 2021 PDB data.
    print("Downloading Planning Database Block Tracts land area data. Please wait...")
    url = "https://api.census.gov/data/2021/pdb/tract?get=LAND_AREA&for=tract:*&in=county:*&in=state:06" \
          f"&key={token}"
    area_data = requests.get(url).json()
    area_df = pd.DataFrame(area_data[1:], columns=area_data[0])
    area_df["TRACT_ID"] = area_df["state"] + area_df["county"] + area_df["tract"]
    area_df = area_df[["TRACT_ID", "LAND_AREA"]]
    # Download
    for year in range(2014, 2021):
        print(f"Downloading American Community Survey {year} population estimates data. Please wait...")
        url = f"https://api.census.gov/data/{year}/acs/acs5?get=B01003_001E&=&for=tract:*&in=county:*" \
              f"&in=state:06&key={token}"
        year_data = requests.get(url).json()
        year_df = pd.DataFrame(year_data[1:], columns=year_data[0])
        year_df["YEAR"] = int(year)
        year_df["TRACT_ID"] = year_df["state"] + year_df["county"] + year_df["tract"]
        year_df.rename(columns={"B01003_001E": "TOTAL_POPULATION"}, inplace=True)
        year_df = year_df.merge(area_df, on="TRACT_ID")
        year_df = year_df[["TRACT_ID", "YEAR", "TOTAL_POPULATION", "LAND_AREA"]]
        population_df = pd.concat([population_df, year_df], axis=0)
    population_df.to_csv(input_datafile, index=False)
    print("Downloading the geospatial data of the population census Tracts. Please wait...")
    tract_url = "https://www2.census.gov/geo/tiger/TIGER2019/TRACT/tl_2019_06_tract.zip"
    download_and_extract_zip_file(url=tract_url, extract_dir=os.path.dirname(tract_geofile))
    print("Downloads complete.")


def get_well_completion_latlon(well_datafile: str, start_year: int, end_year: int):
    dtype = {"": int,
             "DECIMALLATITUDE": str,
             "WORKFLOWSTATUS": str,
             "LLACCURACY": str,
             "PERMITDATE": str,
             "PUMPTESTLENGTH": float,
             "SECTION": str,
             "REGIONOFFICE": str,
             "DRILLINGMETHOD": str,
             "OTHEROBSERVATIONS": str,
             "WELLYIELDUNITOFMEASURE": str,
             "WELLLOCATION": str,
             "PERMITNUMBER": str,
             "TOTALDRAWDOWN": float,
             "VERTICALDATUM": str,
             "BOTTOMOFPERFORATEDINTERVAL": float,
             "GROUNDSURFACEELEVATION": float,
             "STATICWATERLEVEL": float,
             "RECORDTYPE": str,
             "DRILLERLICENSENUMBER": str,
             "FLUID": str,
             "TESTTYPE": str,
             "APN": str,
             "PLANNEDUSEFORMERUSE": str,
             "LOCALPERMITAGENCY": str,
             "TOPOFPERFORATEDINTERVAL": float,
             "WCRNUMBER": str,
             "TOTALDRILLDEPTH": float,
             "LEGACYLOGNUMBER": str,
             "ELEVATIONDETERMINATIONMETHOD": str,
             "ELEVATIONACCURACY": str,
             "DECIMALLONGITUDE": str,
             "METHODOFDETERMINATIONLL": str,
             "HORIZONTALDATUM": str,
             "TOWNSHIP": str,
             "DATEWORKENDED": str,
             "CITY": str,
             "TOTALCOMPLETEDDEPTH": float,
             "OWNERASSIGNEDWELLNUMBER": str,
             "COUNTYNAME": str,
             "RANGE": str,
             "BASELINEMERIDIAN": str,
             "RECEIVEDDATE": str,
             "DRILLERNAME": str,
             "WELLYIELD": float,
             "_id": int,
             "CASINGDIAMETER": float}
    try:
        print("Loading the Well Completion Reports data. Please wait...")
        wcr_df = pd.read_csv(well_datafile, dtype=dtype)
    except FileNotFoundError:
        print("Data not found locally.\nDownloading the well completion reports dataset first. Please wait...")
        welldata_url = "https://data.cnra.ca.gov/dataset/647afc02-8954-426d-aabd-eff418d2652c/resource/" \
                       "8da7b93b-4e69-495d-9caa-335691a1896b/download/wellcompletionreports.csv"
        file_content = requests.get(welldata_url).text
        os.makedirs(os.path.dirname(well_datafile), exist_ok=True)
        with open(well_datafile, "w") as f:
            f.write(file_content)
        print("Loading the Well Completion Reports data. Please wait...")
        wcr_df = pd.read_csv(well_datafile, dtype=dtype)

    # filter to only include new well completion since we predict on this
    wcr_df = wcr_df[wcr_df["RECORDTYPE"] == "WellCompletion/New/Production or Monitoring/NA"]
    # filter to only include agriculture, domestic, or public wells
    # Data issues Agriculture is also denoted by "AG"
    wcr_df.rename(columns={"PLANNEDUSEFORMERUSE": "USE"}, inplace=True)
    wcr_df["USE"] = wcr_df["USE"].fillna("")
    wcr_df["USE"] = wcr_df["USE"].str.lower()
    wcr_df["USE"] = (
        np.where(wcr_df["USE"].str.contains("agri|irrigation"),
                 "Agriculture",
                 np.where(wcr_df["USE"].str.contains("domestic"),
                          "Domestic",
                          np.where(wcr_df["USE"].str.contains("indus|commerc"),
                                   "Industrial",
                                   np.where(wcr_df["USE"].str.contains("public"),
                                            "Public",
                                            "Other")))))
    wcr_df = wcr_df[wcr_df["USE"].isin(["Agriculture", "Domestic", "Public", "Industrial"])]
    # Get only the data between the start year and end year
    wcr_df["DATEWORKENDED"] = pd.to_datetime(wcr_df["DATEWORKENDED"], errors="coerce")
    wcr_df["DATEWORKENDED"] = pd.to_datetime(wcr_df["DATEWORKENDED"], errors="coerce")
    wcr_df["DATEWORKENDED_CORRECTED"] = wcr_df["DATEWORKENDED"].apply(
        lambda x: x if x < datetime.now() else np.nan)
    wcr_df.dropna(subset=["DATEWORKENDED_CORRECTED"], inplace=True)
    wcr_df["DATE"] = pd.to_datetime(wcr_df.DATEWORKENDED_CORRECTED)
    wcr_df["YEAR"] = wcr_df["DATE"].dt.year
    wcr_df = wcr_df[(wcr_df["YEAR"] >= start_year) & (wcr_df["YEAR"] <= end_year)]
    # Cleanup the latitude and longitude columns
    wcr_df = wcr_df[["DECIMALLATITUDE", "DECIMALLONGITUDE"]]
    # There are latitudes and longitudes that are corrupt : 37/41/11.82/
    wcr_df = wcr_df[~wcr_df.DECIMALLATITUDE.str.contains(r"/", na=False)].copy()
    wcr_df = wcr_df[~wcr_df.DECIMALLONGITUDE.str.contains(r"/", na=False)].copy()
    wcr_df["DECIMALLATITUDE"] = wcr_df.DECIMALLATITUDE.astype("float")
    wcr_df["DECIMALLONGITUDE"] = wcr_df.DECIMALLONGITUDE.astype("float")
    # Correct incorrectly signed logitude and latiude Example :   120.54483 Longitude
    wcr_df["DECIMALLONGITUDE"] = np.where(wcr_df["DECIMALLONGITUDE"] > 0, -wcr_df["DECIMALLONGITUDE"],
                                          wcr_df["DECIMALLONGITUDE"])
    wcr_df["DECIMALLATITUDE"] = np.where(wcr_df["DECIMALLATITUDE"] < 0, -wcr_df["DECIMALLATITUDE"],
                                         wcr_df["DECIMALLATITUDE"])
    # About 5% of the dataframe has either latitude or longitude missing, we drop these
    wcr_df.dropna(subset=["DECIMALLATITUDE", "DECIMALLONGITUDE"], inplace=True)
    wcr_df.rename(columns={"DECIMALLATITUDE": "LATITUDE", "DECIMALLONGITUDE": "LONGITUDE"}, inplace=True)

    # Capture the unique latitudes and longitudes so that we send only as many API calls as necessary for unique values.
    # We can then join this dataframe to the original. This drops 75639 rows and we care left with 30348 rows
    wcr_df.drop_duplicates(inplace=True)
    return wcr_df


def get_elevation_from_latlon(lat: float, lon: float) -> float:
    """
    This function queries the National Map service to retrieve the elevation of a point based on its latitude and
    longitude.

    :param lat: latitude of the point
    :param lon: longitude of the point
    :return: elevation of the point
    """
    url = r"https://nationalmap.gov/epqs/pqs.php?"
    params = {
        "output": "json",
        "x": lon,
        "y": lat,
        "units": "Meters"
    }
    # Query the national map service
    result = requests.get(url, params=params).json()
    elevation = result["USGS_Elevation_Point_Query_Service"]["Elevation_Query"]["Elevation"]
    return elevation


def get_batch_elevation_from_latlon(df: pd.DataFrame, lat_column: str = "LATITUDE",
                                    lon_column: str = "LONGITUDE") -> pd.DataFrame:
    """
    This function uses 5 threads to download in parallel the elevation of a batch of points.

    :param df: the dataframe containing the latitude and longitude columns
    :param lat_column: the name of the latitude column
    :param lon_column: the name of the longitude column
    """
    # We use threading to load the data in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        elevations = list(tqdm(executor.map(get_elevation_from_latlon, list(df[lat_column]), list(df[lon_column])),
                               total=len(df)))
    # executor.map() returns the value sin the same order as the input so we can join the list to the dataframe
    df["elev_meters"] = elevations
    return df


def download_all_elevations(well_datafile: str = "./assets/inputs/wellcompletion/wellcompletion.csv",
                            elevation_basedir: str = "./assets/inputs/wellcompletion/elevation_data",
                            start_year: int = 2014, end_year: int = 2021,
                            batch_size: int = 1500, wait_between_batches: int = 5):
    """
    This function downloads the elevation of all wells in the well completion dataset.

    :param well_datafile: the name of the file containing the well completion data
    :param elevation_basedir: the base directory where the elevation data will be stored
    :param start_year: the first year to download the elevation data for
    :param end_year: the last year to download the elevation data for
    :param batch_size: the number of rows to query the service for at each iteration
    :param wait_between_batches: the number of minutes to wait between batches of queries to the National Map service.
    """
    def increase_batch_numbers(start_val: int, end_val: int, increment: int, max_val: int) -> Tuple[int, int]:
        """This is an internal function to increase the start and end row numbers of the batch"""
        start_val += increment
        end_val += increment
        if (end_val > max_val) and ((end_val - max_val) < increment):
            end_val = max_val
        return start_val, end_val

    os.makedirs(elevation_basedir, exist_ok=True)
    # We get the latitude and longitude of all wells completed between the start and end years for
    # agriculture, domestic, public or industrial use
    wcr_df = get_well_completion_latlon(well_datafile, start_year, end_year)
    # Initiate the batch start and end row values
    start_row = 0
    end_row = batch_size
    max_row = len(wcr_df)
    while end_row <= max_row:
        print(f"Downloading elevation data for {start_row} to {end_row} rows of {max_row} rows.")
        # We extracrt the first batch of rows from the dataframe
        df = wcr_df.iloc[start_row:end_row, :].copy()
        part_already_downloaded = False
        # Check for already downloaded batches
        # To avoid overloading the API service, we check if the batch has already been fully downloaded or not
        # The file must exist and contains 1500 rows. If it contains less than 1500 rows, we re-download it.
        try:
            existing_df = pd.read_csv(os.path.join(elevation_basedir, f"lat_long_elev_{start_row}.csv"))
            if len(existing_df) == batch_size:
                part_already_downloaded = True
                print(f"Skipping. Elevation data for {start_row} to {end_row} rows already fully downloaded.")
                start_row, end_row = increase_batch_numbers(start_row, end_row, batch_size, max_row)
        except FileNotFoundError:
            pass
        # If the batch of lat-lon hasn't been downloaded yet, download it and store the file
        if not part_already_downloaded:
            try:
                df = get_batch_elevation_from_latlon(df, lat_column='LATITUDE', lon_column='LONGITUDE')
                df.to_csv(os.path.join(elevation_basedir, f"lat_long_elev_{start_row}.csv"), index=False)
                start_row, end_row = increase_batch_numbers(start_row, end_row, batch_size, max_row)
            except RequestException:
                # We most probably got an error from the API because of the number of requests we made.
                # So we wait for a few minutes and try again.
                print(f"Error occurred. Waiting for {wait_between_batches} minutes before trying again.")
                time.sleep(wait_between_batches * 60)
    print("Downloads complete.")
