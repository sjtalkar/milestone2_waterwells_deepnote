# [California Groundwater Dataset and Stations](https://cdec.water.ca.gov/)

## Description
![What is groundwater](https://github.com/sjtalkar/milestone2_waterwells_deepnote/blob/master/doc/images/groundwater.png)

Groundwater, which is found in aquifers below the surface of the earth, is one of our most important natural resources. 
Groundwater provides drinking water for a large portion of Califoria, nay, the nation's population. It also supplies business and industries, and is used extensively 
for irrigation. California depends on groundwater for a major portion of its annual water supply, particularly during times of drought.
This reliance on groundwater has resulted in overdraft and unsustainable groundwater usage in many of California’s basins, 
particularly so in the San Joaquin River basin.

## So what is groundwater?
Groundwater is water that exists underground in saturated zones beneath the land surface. The upper
surface of the saturated zone is called the water table. Groundwater is a part of the natural water 
cycle. Some part of the precipitation that lands on the ground surface infiltrates into the subsurface.
The part that continues downward through the soil until it reaches rock material that is saturated is groundwater
recharge. Water in the saturated groundwater system moves slowly and may eventually discharge into 
streams, lakes, and oceans. An aquifer is a body of rock and/or sediment that holds this groundwater.

The water level in an aquifer that supplies water to a well does not always remain the same. Factors affecting groundwater levels that are studied in this project include:
 1. Droughts
 2. Seasonal variations in precipitation
 3. Reservoir levels
 4. Pumping for human needs such as domestic, agriculture and industrial
 
If water is pumped at a faster rate than an aquifer is recharged by precipitation or other sources
of recharge, water levels drop. This can happen during drought, due to the extreme deficit of rain.

**Long-term water-level data** are fundamental to the resolution of many of the most complex problems dealing with groundwater availability and sustainability. 
Significant periods of time - years to decades - typically are required to collect water-level data needed to assess the effects of climate variability, 
to monitor the effects of regional aquifer development, or to obtain data sufficient for analysis of water-level trends.

[](https://water.ca.gov/programs/groundwater-management/sgma-groundwater-management)
The analyis is performed against the backdrop of the Sustainable Groundwater Management Act that was passed in 2014 in California. SGMA requires locals agencies 
to form groundwater sustainability agencies (GSAs) for the high and medium priority basins.

## Source
Long-term groundwater level measurements are publicly posted in [The Department of Water Resources Periodic Groundwater Levels datasets](https://data.cnra.ca.gov/dataset/periodic-groundwater-level-measurements)
This dataset is maintained in the DWR Enterprise Water Management database, and contains information specific to the location of **groundwater level monitoring wells**
 and **groundwater level measurements collected at these wells**.
 
The Stations resource identifies **well location coordinates** and other supplementary items about the well type.

The strategy in the project is:
- Create a GeoDataFrame when starting from a regular DataFrame that has latitudinal and longitudinal coordinates.
- A GeoDataFrame needs a shapely object.
-  We use geopandas points_from_xy() to transform Longitude and Latitude into a list of shapely.Point objects and set it as a geometry while creating the GeoDataFrame.

## How to download ?
[NOTE: Download, preview and Data API links](https://data.cnra.ca.gov/dataset/dd9b15f5-6d08-4d8c-bace-37dc761a9c08/resource/bfa9f262-24a1-45bd-8dc8-138bc8107266/download/measurements.csv)

A set of methods to retrieve this large dataset were experimented with before picking the optimal solution. The raw data in CSV stored in Deepnote was retrieved 
using Python's requests library. No API key or secret is required for the call, but each call was limited to 4000 records (since the dataset is extremely large:
5,064,676, and counting, entries) and we loop to get additional data. The records are converted to JSON and then can easily be stored into a dataframe that is 
ultimately saved as a CSV file.

Data collection was performed in a community edition of Databricks that was connected to an Azure account. After storing the file in Filestore, it was downloaded to an Azure VM
and then uploaded to Deepnote running in a browser on the same VM.

[NOTE: I faced challenges running the retrieval in Deepnote due to low memory] 

```python
groundwater_request_api = requests.get('https://data.cnra.ca.gov/api/3/action/datastore_search?resource_id=bfa9f262-24a1-45bd-8dc8-138bc8107266&limit=4000').json()
list_data_groundwater = groundwater_request_api['result']['records']
while groundwater_request_api['result']['records']:
    groundwater_request_api = requests.get('https://data.cnra.ca.gov'+groundwater_request_api['result']['_links']["next"]).json()
    list_data_groundwater.extend(groundwater_request_api['result']['records'])
    
    
pd_df_groundwaterwellcompletion = pd.DataFrame(list_data_groundwater)
pd_df_groundwater.to_csv('/dbfs/FileStore/groundwater.csv')

```

### Other experimental retrieval strategies

##### Using Spark and Pandas dataframes in Databricks 
- The data was read using API calls from CNRA well water pages. The page links have an option for Data API with example usage. 
- The query strings were used in the request call in Python
- On an average about 5000 records were retrieved and the rest in chunks and placed into an extending list. At this point we have two options.
-  We can convert the entire list to a dataframe and save as CSV in Databricks or Deepnote and use it OR the list can be converted,
-  row by row into spark dataframe and saved as CSV.
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

We are interested in the elevation of the groundwater surface, that can be calculated by subtracting the depth to groundwater from the ground surface elevation.

[DECIDING WHEN TO MONITOR GROUNDWATER LEVELS](https://www.countyofcolusa.org/DocumentCenter/View/4260/Series1Article4-GroundwaterLevelMonitoring?bidId=#:~:text=The%20elevation%20of%20the%20groundwater,groundwater%20flow%20can%20be%20determined.&text=Figure%201.)

Water levels in many aquifers in the United States follow a natural cyclic pattern of seasonal fluctuation,typically rising during the winter and spring due to greater precipitation and recharge, 
then declining during the summer and fall owing to less recharge and greater evapotranspiration. Spring measurements generally occur before most of the irrigation season so static groundwater levels are
usually measured in production wells.Because static levels are measured, elevation gradients between monitoring wells can be determined as well as groundwater flow direction within the aquifer systems.
Springtime measurements also indicate the extent that the storage in the aquifer systems has recharged from winter precipitation.

Hence, we filter for spring measurements of groundwater.

`GSE_GWE:`	Ground Surface Elevation to Groundwater Elevation -	 Depth to groundwater elevation in feet below ground surface.

## Mapping at the TRS level
Once we have a GeoDataframe with the points in the coordinate reference system, we spatially join to the California PLSS GeoJSON to map to the closest Township-Range using sjoin method in geopandas.

## Potential issues


