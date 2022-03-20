import requests
import urllib
import pandas as pd
import time


# USGS Elevation Point Query Service
url = r'https://nationalmap.gov/epqs/pqs.php?'

def elevation_function(df, lat_column, lon_column):
    """Query service using lat, lon. add the elevation values as a new column."""
    elevations = []
    for lat, lon in zip(df[lat_column], df[lon_column]):

        # define rest query params
        params = {
            'output': 'json',
            'x': lon,
            'y': lat,
            'units': 'Meters'
        }

        # format query string and return query value
        result = requests.get((url + urllib.parse.urlencode(params)))
        elevations.append(result.json()['USGS_Elevation_Point_Query_Service']['Elevation_Query']['Elevation'])

    df['elev_meters'] = elevations
    return df


def get_elevation_from_latlong():
    well_completion_clean_df = pd.read_csv("../assets/outputs/well_completion_clean.csv")
    
    ### Capture the unique latitudes and longitudes so that we send only as many API calls as necessary for unique values. We can then join this datafrae to the original
    lat_long_df  = well_completion_clean_df.iloc[:, 0:2].drop_duplicates() # This drops 75639 rows and we care left with 30348 rows

    start_row_loc = 0
    end_row_loc = 1000
    #Place a timer, if not your requests will fail
    wait_minutes = 15
    df = lat_long_df.iloc[start_row_loc:end_row_loc, :].copy()
    while end_row_loc < len(lat_long_df)
        try:
            elevation_function(df, 'LATITUDE', 'LONGITUDE')
            df.head()
            df.to_csv(f"../assets/outputs/elevation_api_results/lat_long_elev_{start_row_loc}.csv")
            start_row_loc += 1000
            end_row_loc += 1000 
            #time.sleep(wait_minutes*60)
        except:
            time.sleep(wait_minutes*60)
            wait_minutes += wait_minutes
    
    # Get the last straggling rows