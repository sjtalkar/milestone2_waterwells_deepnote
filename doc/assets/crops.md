# [California Statewide Crop Mapping Datasets](https://data.cnra.ca.gov/dataset/statewide-crop-mapping)
## Description
These datasets represent the 2014, 2016 and 2018 _'main season agricultural land use, wetlands, and urban boundaries 
for all 58 counties in California.'_

According to the OECD (Organisation for Economic Co-operation and Development), 
> Agriculture production is highly dependent on water and increasingly subject to water risks. It is also the largest 
> using sector and a major polluter of water. Improving agriculture’s water management is therefore essential to a 
> sustainable and productive agro-food sector.

As agriculture practices have such an impact on water usage and resources, we decided to include in our analysis
the datasets of the crop mapping for the state of California. For this analysis we are only using the crop
mapping datasets as a predicate feature for water shortage. The impact of agriculture on water quality is
outside the scope of this analysis.
## Source
The datasets are provided by the [__California Natural Resources Agency__](https://resources.ca.gov/) and were 
_'originally prepared by Land IQ, LLC and provided to the California Department of Water Resources (DWR) and other 
resource agencies involved in work and planning efforts across the state for current land use information.'_

2014 dataset citation information:
* Originator: Joel Kimmelshue, Land IQ, LLC, Owner
* Publication Date: 08-05-2017
* Title: i15_Crop_Mapping_2014
* Edition: 2017.05.08
* Geospatial Data Presentation Form: vector digital data
* Other Citation Details: CDWR (2017). 2014 California Statewide Agricultural Land Use , California Department of Water 
* Resources, website: [https://gis.water.ca.gov/app/CADWRLandUseViewer/](https://gis.water.ca.gov/app/CADWRLandUseViewer/)

2016 dataset citation information:
* Originator: Joel Kimmelshue, Land IQ, LLC, Owner (Originator), Land IQ, LLC, Owner (Originator), Owner
* Publication Date: 22-11-2019
* Title: i15_Crop_Mapping_2016
* Edition: 2019.11.22
* Geospatial Data Presentation Form: vector digital data
* Other Citation Details: CDWR (2019). 2016 California Statewide Agricultural Land Use , California Department of Water 
* Resources, website: [https://gis.water.ca.gov/app/CADWRLandUseViewer/](https://gis.water.ca.gov/app/CADWRLandUseViewer/)

2018 dataset citation information:
* Organization's name: Joel Kimmelshue, Land IQ, LLC, Owner (Originator), Land IQ, LLC, Owner (Originator), Owner
* Publication Date: 08-02-2021
* Title: i15_Crop_Mapping_2018
* Edition: 2021.02.08
* Presentation Formats: digital map
* FGDC Geospatial Presentation Format: vector digital data
* Other Citation Details: 
  * CDWR Land Use Viewer: [https://gis.water.ca.gov/app/CADWRLandUseViewer/](https://gis.water.ca.gov/app/CADWRLandUseViewer/) 
  * Statewide Crop Mapping on California Natural Resources Agency (CRNA) Open Data Portal: 
  [https://data.cnra.ca.gov/dataset/statewide-crop-mapping](https://data.cnra.ca.gov/dataset/statewide-crop-mapping). 
  * SGMA Data Viewer: [https://sgma.water.ca.gov/webgis/?appid=SGMADataViewer#waterbudget](https://sgma.water.ca.gov/webgis/?appid=SGMADataViewer#waterbudget)
## How to download?
The `CropsDataset` class in the `/lib/crops.py` custom library is designed to load the crops geospatial datasets from 
the local `/assets/inputs/crops/` folder. If files are not found, the data are automatically downloaded from the 
[Statewide Crop Mapping](https://data.cnra.ca.gov/dataset/statewide-crop-mapping) page, when running the 
`/eda/crops.ipynb` notebook. The custom crop name-to-type mapping JSON file is likewise automatically downloaded from 
[a dedicated GitHub repository](https://github.com/mlnrt/milestone2_waterwells_data) where we provide additional files.
Please refer to the [How to Download the Datasets?](doc/assets/download.md) documentation for more details.

The datasets used for this analysis are the _Statewide Crop Mapping GIS Shapefiles_ datasets for the years 2014, 2016, 
2018. All the files can be directly downloaded from the 
[Statewide Crop Mapping](https://data.cnra.ca.gov/dataset/statewide-crop-mapping) page.

The documentation of each dataset and the fields within is described in a PDF file included within the download of the
shapefiles.
## Features of interest
For this analysis we use the detailed crop type (e.g., `Apples`, `Apricots`, `Cherries`, instead of the `Deciduous 
fruits and nuts` class). This increases the number of features but we can't expect the crop type `30 - Lettuce or Leafy 
Grean` and `16 - Flowers, nursery & Christmas tree farms`, both in the `T` class, to consume the same amount of water.

Thus, the features extracted from the original dataset are

| Feature Name | Description                                                                                                     |
|--------------|-----------------------------------------------------------------------------------------------------------------|
| Crop2014     | the July crop type in the 2014 dataset.                                                                         |
| CROPTYP2     | the summer crop type in the 2016 and 2018 datasets                                                              |
| geometry     | containing the polygon shapes of each crop field. The polygon coordinates must be converted to EPSG:4326 format |


### Why Use Only the Summer Data?
Aquifers water level are usually measured in spring when they are at their maximum levels due to water recharge from
snowpack melting and precipitations. On the contrary the main crop growing season is the summer months and is as such
the season having the biggest impact on water usage. For this analysis we thus limit ourselves to the summer crops data.

### Discarding Some Crops Classes
Some Crops classes are manually discarded during the ETL processing, including land areas classified as:
* "X - Not Classified"
* "U - Urban"
* "NR - Native Riparian" which are not crops but existing water banks vegetation (we have another dataset for existing
vegetation)

These classes do not describe actual crops and instead of having such additional features, we consider it equivalent for
a Township fully covered by urban area, to have a value of zero for all crop types than having an "urban" feature set to 
100%.
 
### Unused interesting features
The 2016 and 2018 have other interesting features like:
* `IRR_TYP1PA` - which indicates if the land is irrigated or not for the crop farming
* `IRR_TYP2PA` - which provides details on the type of irrigation performed on a specific farming land.

Unfortunately, those data are available only for the 2016 and 2018 datasets so these fields have thus been 
ignored at this stage.
## Mapping at the Township-Range level
Please refer to this documentation [Overlaying San Joaquin Valley Township Boundaries](doc/etl/township_overlay.md)
## Potential issues
### Description
1. The 2014 and 2016-2018 datasets organize data differently
  * The 2014 dataset list all the crops individually by class names (e.g. `D ¦ Deciduous fruits and nuts`) in the 
`DWR_Standa` column and name (e.g. `Strawberries`, `Tomatoes`, `Grapes`... ) in the `Crop2014` dataset while the 
2016-2018 organize the crops by class codes (e.g. `D` for `Deciduous fruits and nuts`) and subclasses (e.g. `D1` for 
`Apples`, `D2` for `Apricots`, etc). 
  * The 2014 dataset only list one crop type per area, while the 2016-2018 datasets list one crop type per season when 
available with `CROPTYP1` column corresponding to spring crops, `CROPTYP2` to summer crops, etc.
2. Compared to other datasets we do not have a dataset per year.
3. The crop classification in R,R,F,P,T... classes has little to do with the amount of water required to grow a
specific crop. E.g. `T3 - Beans`, `T16 - Flowers, nursery & Christmas tree farms`, `T30 - Lettuce or Leafy Greens`, 
`T31 - Potato or Sweet potato` are all in the same class `T`. But obviously the impact of growing trees, lettuces or 
potatoes is not the same in terms of water consumption. 
### How did we remediate the issues?
The above issues were remediated as follow:
1. In the 2016 and 2018 datasets we used the summer crops types (the `CROPTYP2` column).
2. Having only data for 3 years over the analysis survey, we assume little year-to-year variation in crop farming and 
extended the data for the missing years (2015, 2017, ~2019) with the data from the previous years 
(i.e. we assume that 2015 crops = 2014 crops). We understand that farming practices like crop rotation would challenge
these assumptions.
3. We use the crop type instead of the cross class. It increases the number of features but hopefully will increase
precision downstream.
4. Imputing values is performed in a scikit-learn function transformer that forward fills the crops values from the 
years it is available to the next year(s). For instance, 2014 value is used for 2015, 2016 value for 2017 and so on.
