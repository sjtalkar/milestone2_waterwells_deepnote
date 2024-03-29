# [California Groundwater Measurements Dataset and Stations](https://data.cnra.ca.gov/dataset/periodic-groundwater-level-measurements)

## Description
Groundwater, which is found in aquifers below the surface of the earth, is one of our most important natural resources. 
Groundwater provides drinking water for a large portion of California, nay, the nation's population. It also supplies 
business and industries and is used extensively  for irrigation. California depends on groundwater for a major portion 
of its annual water supply, particularly during times of drought. This reliance on groundwater has resulted in overdraft
and unsustainable groundwater usage in many of California’s basins, particularly so in the San Joaquin River basin.

![What is groundwater](../images/groundwater.png)

### What is groundwater?
__Groundwater__ is water that exists underground in saturated zones beneath the land surface. The upper surface of the 
saturated zone is called the __water table__. Groundwater is a part of the natural water cycle. Some part of the 
precipitation that lands on the ground surface infiltrates into the subsurface. The part that continues downward 
through the soil until it reaches rock material that is saturated is __groundwater recharge__. Water in the saturated 
groundwater system moves slowly and may eventually discharge into  streams, lakes, and oceans. An __aquifer__ is a body 
of rock and/or sediment that holds this groundwater.

The water level in an aquifer that supplies water to a well does not always remain the same. Factors affecting 
groundwater levels that are studied in this project include:
 1. Droughts
 2. Seasonal variations in precipitation
 3. Reservoir levels
 4. Pumping for human needs such as domestic, agriculture and industrial
 
If water is pumped at a faster rate than an aquifer is recharged by precipitation or other sources
of recharge, water levels drop. This can happen during drought, due to the extreme deficit of rain.

**Long-term water-level data** are fundamental to the resolution of many of the most complex problems dealing with 
groundwater availability and sustainability.  Significant periods of time - years to decades - typically are required 
to collect water-level data needed to assess the effects of climate variability, to monitor the effects of regional 
aquifer development, or to obtain data sufficient for analysis of water-level trends.

The analyis is performed against the backdrop of the 
[Sustainable Groundwater Management Act](https://water.ca.gov/programs/groundwater-management/sgma-groundwater-management) 
that was passed in 2014 in  California. SGMA requires locals agencies to form groundwater sustainability agencies (GSAs) 
for the high and medium priority basins.

## Source
We use 2 datasets provided by 
[The Department of Water Resources Periodic Groundwater Levels datasets](https://data.cnra.ca.gov/dataset/periodic-groundwater-level-measurements). 
* Long-term groundwater level measurements containing a time series measurement since 1900 
* The groundwater measurement stations information, containing the geolocation information

Datasets citation information:
* Organization: California Department of Water Resources
* Contact  Name: Water Data Library
* Title: Periodic Groundwater Level Measurements
* Resources, website: [https://data.cnra.ca.gov/dataset/periodic-groundwater-level-measurements](https://data.cnra.ca.gov/dataset/periodic-groundwater-level-measurements).

## How to download?
The `GroundwaterDataset` class in the `/lib/groundwater.py` custom library is designed to load the groundwater
measurements dataset and measurement stations geolocation datasets from the local  `/assets/inputs/groundwater/` folder.
If files are not found, both the measurements and the stations data are automatically downloaded from an AWS S3 bucket
(which is publicly available), when running the `/eda/groundwater.ipynb` notebook. Please refer to the 
[How to Download the Datasets?](doc/assets/download.md) documentation for more details.

### Original download
A set of methods to retrieve this large dataset through APIs were originally experimented with before picking the optimal 
solution. The raw data in CSV stored in Deepnote was retrieved using Python's requests library. No API key or secret is 
required for the call, but each call was limited to 4000 records (since the dataset is extremely large:  5,064,676, and 
counting, entries) and we loop to get additional data. The records are converted to JSON and then can easily be stored 
into a dataframe that is ultimately saved as a CSV file.

Data collection was performed in a community edition of Databricks that was connected to an Azure account. After storing
the file in Filestore, it was downloaded to an Azure VM and then uploaded to Deepnote running in a browser on the same 
VM.

```python
url = "https://data.cnra.ca.gov/api/3/action/datastore_search?resource_id=bfa9f262-24a1-45bd-8dc8-138bc8107266&limit=4000"
groundwater_data = requests.get(url).json()
all_groundwater_data = groundwater_data["result"]["records"]
while groundwater_data["result"]["records"]:
    groundwater_data = requests.get("https://data.cnra.ca.gov" + groundwater_data["result"]["_links"]["next"]).json()
    all_groundwater_data.extend(groundwater_data["result"]["records"])
groundwater_df = pd.DataFrame(all_groundwater_data)
groundwater_df.to_csv(input_datafile)
```

For API information, refer to the 
[Periodic Groundwater Level Measurements](https://data.cnra.ca.gov/dataset/periodic-groundwater-level-measurements)
page. Note that APIs allow for only 4,000 rows downloaded at a time.

### Other experimental retrieval strategies
##### Using Spark and Pandas dataframes in Databricks 
- The data was read using API calls from CNRA well water pages. The page links have an option for Data API with example 
usage. 
- The query strings were used in the request call in Python
- On an average about 5000 records were retrieved and the rest in chunks and placed into an extending list. At this 
point we have two options.
- We can convert the entire list to a dataframe and save as CSV in Databricks or Deepnote and use it OR the list can be 
converted,
- row by row into spark dataframe and saved as CSV.
- Pandas dataframe saved as CSV should be read back as Pandas DF.
- Spark dataframe saved as CSV should be read back as Spark dataframe or else you will encounter read error
- Dockerfile and init.py are set in Deepnote so that Spark can be used.

[Note: The file partitions are coalesced into one so that we can download one CSV file]
```python

groundwater_request_api = requests.get('https://data.cnra.ca.gov/api/3/action/datastore_search?resource_id=bfa9f262-24a1-45bd-8dc8-138bc8107266&limit=4000').json()
list_data_groundwater = groundwater_request_api['result']['records']
while groundwater_request_api['result']['records']:
    groundwater_request_api = requests.get('https://data.cnra.ca.gov'+groundwater_request_api['result']['_links']["next"]).json()
    list_data_groundwater.extend(groundwater_request_api['result']['records'])
    
df_groundwater = spark.createDataFrame(Row(**row) for row in list_data_groundwater)
df_groundwater.coalesce(1).write.format("com.databricks.spark.csv").option("header", "true").save("dbfs:/FileStore/WaterWell/groundwater.csv")    

```

## Features of interest
We are interested in the elevation of the groundwater surface, that can be calculated by subtracting the depth to 
groundwater from the ground surface elevation.

Water levels in many aquifers in the United States follow a natural cyclic pattern of seasonal fluctuation, typically 
rising during the winter and spring due to greater precipitation and recharge, then declining during the summer and 
fall owing to less recharge and greater evapotranspiration. Spring measurements generally occur before most of the 
irrigation season so static groundwater levels are usually measured in production wells. Because static levels are 
measured, elevation gradients between monitoring wells can be determined as well as groundwater flow direction within 
the aquifer systems. Spring time measurements also indicate the extent that the storage in the aquifer systems has 
recharged from winter precipitation. For more information, please read 
[Deciding When to Monitor Groundwater Levels](https://www.countyofcolusa.org/DocumentCenter/View/4260/Series1Article4-GroundwaterLevelMonitoring?bidId=#:~:text=The%20elevation%20of%20the%20groundwater,groundwater%20flow%20can%20be%20determined.&text=Figure%201.).

Hence, we filter for spring measurements of groundwater.

| Feature Name | Description                                                                                                           |
|--------------|-----------------------------------------------------------------------------------------------------------------------|
| GSE_GWE      | Ground Surface Elevation to Groundwater Water Elevation - Depth to groundwater elevation in feet below ground surface |

## Mapping at the TRS level
Please refer to this documentation [Overlaying San Joaquin Valley Township Boundaries](doc/etl/township_overlay.md)

## Potential issues
### Description
1. As shown in the `/eda/groundwater.ipynb` 8% of the measurements have missing `GSE_GWE` data, our feature of interest
### How did we remediate the issues?
1. Rows without `GSE_GWE` data are simply ignored
