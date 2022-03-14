# [California Groundwater Dataset and ](https://cdec.water.ca.gov/)

## Description
Groundwater, which is found in aquifers below the surface of the earth, is one of our most important natural resources. 
Groundwater provides drinking water for a large portion of Califoria, nay, the nation's population, supplies business and industries, and is used extensively 
for irrigation. California depends on groundwater for a major portion of its annual water supply, particularly during times of drought.
This reliance on groundwater has resulted in overdraft and unsustainable groundwater usage in many of California’s basins, 
partcularly so in the San Joaquin River basin which is our area of interest.

The water level in an aquifer that supplies water to a well does not always remain the same. Factors affecting groundwater levels that are studied in this project include:
 1. Droughts
 2. Seasonal variations in precipitation
 3. Reservoir levels
 4. Pumping for human needs such as domestic, agriculture and industrial
 
 If a water is pumped at a faster rate than an aquifer is recharged by precipitation or other sources of recharge, water levels can drop. 
 This can happen during drought, due to the extreme deficit of rain.

**Long-term water-level data** are fundamental to the resolution of many of the most complex problems dealing with groundwater availability and sustainability. 
Significant periods of time - years to decades - typically are required to collect water-level data needed to assess the effects of climate variability, 
to monitor the effects of regional aquifer development, or to obtain data sufficient for analysis of water-level trends.

[](https://water.ca.gov/programs/groundwater-management/sgma-groundwater-management)
The analyis is performed under the backdrop of the Sustainable Groundwater Management Act that was passed in 2014 in California. SGMA requires locals agencies 
to form groundwater sustainability agencies (GSAs) for the high and medium priority basins.


## Source

Data retrieved in Databricks both as pandas dataftame and Spark dataframe convverted to CSV.
In the case of Spark files, the parquet files were coalesced into one file and saved into the CSV
SOURCE LINKS
- https://data.ca.gov/dataset/household-water-supply-shortage-reporting-system-data


## How to download ?

##### DATABRICKS AND DEEPNOTE
- The data was read using API calls from CNRA well water pages. The page links have an option for Data API with exmaple usage. The query strings were used in the request call in Python
- On an average about 5000 records were retrieved and the rest in chunks and placed into an extending list. At this point we have two options. We can convert the entire list to a dataframe and save as CSV in Databricks or Deepnote and use it OR the list can be converted, row by row into spark dataframe and saved as CSV.
- Pandas dataframe saved as CSV should be read back as Pandas DF.
- Spark dataframe saved as CSV should be read back as Spark dataframe or else you will encounter read error
- Dockerfile and init.py are set in Deepnote so that Spark can be used.

The datasets used for this analysis are the _Statewide Crop Mapping GIS Shapefiles_ datasets for the years 2014, 2016,
2018.
All the files can be directly downloaded from the [Statewide Crop Mapping](https://data.cnra.ca.gov/dataset/statewide-crop-mapping) page.

The documentation of each dataset and fields within is described in a PDF file included within the download of the
shapefiles.
## Features of interest
For this analysis we limit ourselves to the main class of crops (e.g. `Deciduous fruits and nuts`, `Vineyard`, etc),
without going the sublass details of each crop (e.g. `Apples`, `Apricots`, `Cherries`, etc for the `Deciduous fruits 
and nuts` class). This means that we are assuming that each crop in a class have the same agricultural impact on
water usage and resources. This assumption obviously does not hold but is made in order to simplify the analysis.

Thus the features extracted from the original dataset are:
* `DWR_Standa` - the July crop class in the 2014 dataset. We keep only the first letter of the column which corresponds
to the class code (e.g. "V | VINEYARD") and corresponds to the class codes used in the 2016 and 2018 datasets 
* `CLASS2` - the summer crops in the 2016 and 2018 datasets.
* `geometry` - containing the polygon shapes of each crop field. The polygon coordinates must be converted to 
EPSG:4326 format. 
* 
The 2016 and 2018 have other interesting features like:
* `IRR_TYP1PA` - which indicates if the land is irrigated or not for the crop farming
* `IRR_TYP2PA` - which provides details on the type of irragation performed on a specific farming land.

Unfortunately those data are available only for the 2016 and 2018 datasets. It feels very complicated to augment the
2014 dataset with irrigation status from past years as a crop/farming land in 2014 might not necessary cover the
same land area and might be used for a different crop with a different irrigation system. These fields have thus been 
ignored at this stage.

Aquifers water level are usually measured in spring when they are at their maximum levels due to water recharge from
snowpack melting and precipitations. On the contrary the main crop growing season is the summer months and is as such
the season having the biggest impact on water usage. For this analysis we thus limit ourselves to the summer crops data.
## Mapping at the TRS level
Please refer to this documentation [Overlaying San Joaquin Valley Township Boundaries](../doc/etl/township_overlay.md)
## Potential issues
### Description
1. The 2014 and 2016-2018 datasets organize data differently
  * The 2014 dataset list all the crops individually by class names (e.g. `D ¦ Deciduous fruits and nuts`) in the 
`DWR_Standa` column and name (e.g. `Strawberries`, `Tomatoes`, `Grapes`... ) in the `Crop2014` dataset while the 
2016-2018 organize the crops by class codes (e.g. `D` for `Deciduous fruits and nuts`) and subclasses (e.g. `D1` for 
`Apples`, `D2` for `Apricots`, etc). 
  * The 2014 dataset only list one crop type per area, while the 2016-2018 datasets list one crop type per season when 
available with `CLASS1` column corresponding to spring crops, `CLASS2` to summer crops, etc.
2. Compared to other datasets we do not have a dataset per year.
3. The crops classification in R,R,F,P,T... classes has little to do with the amount of water required to grow a
specific crop. E.g. `Beans`, `Flowers, nursery & Christmas tree farms`, `Lettuce or Leafy Greens`, `Potato or Sweet 
potato` are all in the same class `T`. But obviously the impact of growing trees, lettuces or potatoes is not the same
in terms of water consumption. 
### How did we remediate the issues?
The above issues were remediated as follow:
1. In the 2016 and 2018 datasets we limited ourselves to the summer crops class (the `CLASS2` column).
2. Having only data for 3 years over the analysis survey, we assume little year-to-year variation in crop farming and 
extended the data for the missing years (2015, 2017, ~2019) with the data from the previous years 
(i.e. we assume that 2015 crops = 2014 crops). We understand that farming practices like crop rotation would challenge
these assumptions.
3. This problem has been ignored at this stage
