# California Well Completion Report Dataset

## Description

This Well Completion Report dataset represents an index of records from the California Department of Water Resources' (DWR) Online System for Well Completion Reports (OSWCR). 
 Limited spatial resolution: The majority of well completion reports have been spatially registered to the center of the 1x1 mile Public Land Survey System section that the well is located in.
 Water well completion reports or "well logs" include information about well including the construction, location, yield, geology, and depth. 

## Source
- https://data.cnra.ca.gov/dataset/well-completion-reports

## How to download ?
The public dataset site offers [Data API access](https://data.cnra.ca.gov/api/1/util/snippet/api_info.html?resource_id=8da7b93b-4e69-495d-9caa-335691a1896b) along with examples that show how to retrieve filtered
data. For instance, it provides the following example for Python.

```Python
import json
import urllib.request
url = 'https://data.cnra.ca.gov/api/3/action/datastore_search?resource_id=8da7b93b-4e69-495d-9caa-335691a1896b&limit=5&q=title:jones'  
fileobj = urllib.request.urlopen(url)
response_dict = json.loads(fileobj.read())
print(response_dict)
```

A deep study of well construction and aquifers had to be conducted to understand the features. The understanding has been distilled below and features are explained.


## Features of interest
<<<<<<< HEAD

The columns specified here are as per original dataset name:
[Explanation of geologic terms](https://mbmggwic.mtech.edu/sqlserver/v11/help/welldesign.asp)
![welldiagram](/work/milestone2_waterwells_deepnote/doc/images/welldiagram.png)
> **Aquifer**: An aquifer is a geologic unit (sand and gravel, sandstone, limestone, or other rock) that will yield usable amounts of water to a well or spring.

> **Perforations**: All wells are open to the aquifer so that water can enter the well. Well completions vary from "open hole" in consolidated rock that does not need a casing, 
> to "open bottom" where the only way for the water to enter the well is through the end of the casing. However, many wells have some sort of well screen installed or perforations cut into 
> the casing through which water can enter. The openings must be correctly sized so that water will enter, but sand and other aquifer materials do not.

> **Static water level**: The static water level is the distance from the land surface (or the measuring point) to the water in the well under non-pumping (static) conditions. Static water levels can be
> influenced by climatic conditions and pumping of nearby wells and are often measured repeatedly to 
> gain information about how aquifers react to climatic change and development.

> **Total depth**: The total depth of the well is the distance from land surface to the bottom.

> **Casing**: Steel or plastic pipe placed in the borehole to keep it from collapsing. The casing is sealed to the borehole wall near the land surface with the annular seal.

> **Ground Surface Elevation** Measuring the depth to groundwater below the ground surface is more informative if the elevation of the ground surface is known. 
> This can either be measured by surveying from a benchmark of a known elevation to a reference point on the well or estimated from topographic maps. The elevation of the groundwater surface 
> then can be calculated by subtracting the depth to groundwater from the ground surface elevation. Then, comparisons of groundwater elevations can be made between monitoring well locations and
> the direction and gradient of groundwater flow can be determined. 

> **Typical well depth** Domestic wells are generally shallow, limited to the top 50 to 100 feet of the Alluvial aquifer system. Agricultural wells are usually deeper than domestic wells, 
> commonly 200 to 400 feet deep or deeper. The well casing of agricultural wells is often perforated at various depths transmitting water from more than one aquifer system (i.e. the Alluvial
> aquifer system and the Tuscan or Tehama Aquifer systems depending where the well is located).

> **Pumping water level**: The pumping water level is the distance from the land surface (or measuring point) to the water in the well while it is pumping. The time that the pumping water level was
> measured is usually recorded also. For example, "The pumping water level was 85 feet below land surface, 1 hour after pumping began."

> **Drawdown** : The drawdown in a well is the difference between the pumping water level and the static (non-pumping) water level. Drawdown begins when the pump is turned on and increases until the well
> reaches "steady state" sometime later. Therefore, drawdown measurements are usually reported along with the amount of time that has elapsed since pumping began. For example, 
> "The drawdown was 10 feet, 1 hour after pumping began."

> **Yield**: The amount of water measured in **gallons per minute** a well will produce when pumped.


| Feature Name               	| Description                                                                                                                                           	|
|----------------------------	|-------------------------------------------------------------------------------------------------------------------------------------------------------	|
| DECIMALLATITUDE            	| Latitudinal position of the well                                                                                                                      	|
| DECIMALLONGITUDE           	| Longitudinal position of the well                                                                                                                     	|
| TOWNSHIP                   	| Township in which well is located (see PLSS documentation for definition of Range)                                                                    	|
| RANGE                      	| Range in which well is located (see PLSS documentation for definition of Range)                                                                       	|
| SECTION                    	| Section which well is located (see PLSS documentation for definition of Section)                                                                      	|
| WELLLOCATION               	| Address of location, typically postal                                                                                                                 	|
| CITY                       	| Well location city                                                                                                                                    	|
| COUNTYNAME                 	| Well location county                                                                                                                                  	|
| BOTTOMOFPERFORATEDINTERVAL 	| Bottom of the screen/perforation that is the opening to the aquifer                                                                                   	|
| TOPOFPERFORATEDINTERVAL    	| Top of the screen/perforation that is the opening to the aquifer                                                                                      	|
| GROUNDSURFACEELEVATION     	| See definition above                                                                                                                                  	|
| STATICWATERLEVEL           	| The static water level is the distance from the land surface (or the measuring point) to the water in the well under non-pumping (static) conditions. 	|
| RECORDTYPE                 	| This indicates if the well completion report is for a new construction, modification or repair.                                                       	|
| PLANNEDUSEFORMERUSE        	| Usage description from which we retrieve mention of Agricultural. Domestic, Public and Industrial use                                                 	|
| WCRNUMBER                  	| Unique well identifier                                                                                                                                	|
| TOTALDRILLDEPTH            	| Drilled depth of well                                                                                                                                 	|
| TOTALCOMPLETEDDEPTH        	| Completed depth of well                                                                                                                               	|
| DATEWORKENDED              	| Date of completion of well construction                                                                                                               	|
| CASINGDIAMETER             	| See definition above                                                                                                                                  	|
| TOTALDRAWDOWN             	| See definition above                                                                                                                                  	|
| WELLYIELD                 	| Amount of water yielded (See definition above)                                                                                                            |
| WELLYIELDUNITOFMEASURE       	| Yield unit of measure (See definition above)                                                                                                              |


## Mapping at the TRS level

The strategy in the project is:
     - Create a GeoDataFrame when starting from a regular DataFrame that has latitudinal and longitudinal coordinates. In the well completion reports, we have columns for latitude and longitude.
     - A GeoDataFrame needs a shapely object.
     - We use geopandas points_from_xy() to transform Longitude and Latitude into a list of shapely.Point objects and set it as a geometry while creating the GeoDataFrame.
	 - Once we have a GeoDataframe with the points in the coordinate reference system, we spatially join to the California PLSS GeoJSON to map to the closest TownshipRange using sjoin method in geopandas.


## Potential issues
### Description
Stated Known issues: 
- Missing and duplicate records
- Missing values (either missing on original Well Completion Report, or not key entered into database)
- Incorrect values (e.g. incorrect Latitude, Longitude, Record Type, Planned Use, Total Completed Depth) 

### How did we remediate the issues?
Data cleaning of the dataset involves the following:
- If the missing values is a feature of interest, then the record is dropped. Hence we do not allow for missing latitude, longitude, completed well depth and date of completion.
- Latitude and Longitude records in some cases contain "/". These records do not yield the right location and hence dropped.
- Extract domain of usage such as agriculture, domestic and industrail from descriptive description of usage.
- Remove erroneous entries such as well completion depth indicated to be less that 20 feet (see typical well depth above)
- Remove erroneous entries where text is provided instead of a number for well completion depth
- Filter to new well completion reports
