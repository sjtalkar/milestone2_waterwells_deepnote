# [The Soil Survey Dataset](https://www.nrcs.usda.gov/wps/portal/nrcs/detail/soils/survey/geo/?cid=nrcs142p2_053629)
## Description
This dataset contains the data for the state of California from the broad-based inventory of soils and non-soil areas of
the United States called 
[Digital General Soil Map of the United States (STATSGO2) Database](https://www.nrcs.usda.gov/wps/portal/nrcs/detail/soils/survey/geo/?cid=nrcs142p2_053629).
## Source
This dataset is provided by the U.S. Department of Agriculture, Natural Resources Conservation.

Information:
* Originator: U.S. Department of Agriculture, Natural Resources Conservation Service
* Publication Date: 04-10-2016
* Title: Digital General Soil Map of U.S.
* Geospatial Data Presentation Form: Tabular digital data and vector digital data
  * Publication Information:
    * Publication Place: Fort Worth, Texas
    * Publisher: U.S. Department of Agriculture, Natural Resources Conservation Service
  * Online_Linkage: [https://websoilsurvey-dev.dev.sc.egov.usda.gov/](https://websoilsurvey-dev.dev.sc.egov.usda.gov/)
## How to download ?
The `SoilsDataset` class in the `/lib/soils.py` custom library is designed to load the soil survey data and geospatial 
information from the local `/assets/inputs/soils/` folder. If files are not found the data are downloaded from 
[a dedicated Github repository](https://github.com/mlnrt/milestone2_waterwells_data) where we store just the
required file. Also, the survey data in the raw dataset are stored in a Microsoft Access database, making it difficult
to automate the loading of the data. To eas reproducibility, we thus provide in the GitHub repository the data used
in this analysis.

The raw dataset file __wss_gsmsoil_CA_\[2016-10-13\].zip__ can be downloaded from 
[the U.S. General Soil Map (STATSGO2) by state](https://nrcs.app.box.com/v/soils). It contains both:
* spatial shapefiles describing each map area 
* and a Microsoft Access table describing the soil type of each area. For simplicity, the data have been extracted 
* from the _Win-Pst - Input_ view in the Microsoft Access database as a CSV file, stored in the
`./assets/inputs/soils/soil_data.csv`.
## Features of interest
The features extracted from the original datasets are:
* from the soil table:

| Feature Name | Description                                                                                             |
|--------------|---------------------------------------------------------------------------------------------------------|
| mukey        | a key identifying a map unit in the soil survey dataset                                                 |
| taxorder     | the taxonomy order of the soil in a map unit area                                                       |
| hydgrp       | the hydrologic group of the soil order. The hydrologic groups are classified as A, B, C, D, B/D and C/D |
| comppct_r    | the percentage of the map unit surface covered by a soil type                                           |


* from the map dataset:

| Feature Name | Description                                                                                                                                             |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| mukey        | a key identifying a map unit in the soil survey dataset                                                                                                 |
| geometry     | ontaining the polygon shapes of each map survey area. In this map dataset one map unit identified by a `musym` key can contain multiple geometry shapes |


Note that through ETL, we combine the `taxorder` and `hydgrp` columns as one soil type and create a feature for each
map unit, keeping only the `dominant_soil_type` of that map unit.

We do not make use of the below features from the table of soil orders:

| Feature Name               | Description                                                                            |
|----------------------------|----------------------------------------------------------------------------------------|
| slope_l, slope_h | representing the map unit's low and high slope percentage |
| compname | the soil's component name |
| musym | the column which contains in both datasets a symbol identifying a map unit, because each map unit have a unique `musym` and `mukey` to identify it. So using either of the two is sufficient to identify a map unit |

### What are Soil Orders?
Soil Orders is the most general level of classification in the USDA system of Soil Taxonomy. Using this Order classes,
all the soils in the world can be assigned one of the 12 orders.

Soil orders are described as follow:
* `Entisols` - Little, if any horizon development
* `Inceptisols` - Beginning of horizon development
* `Aridisols` - Soils located in arid climates
* `Alfisols` - Deciduous forest soils
* `Ultisols` - Extensively weathered soils
* `Gelisols` - Soils containing permafrost
* `Andisols` - Soil formed in volcanic material
* `Mollisols` - Soft, grassland soils
* `Spodosols` - Acidic, coniferous forest soils
* `Oxisols` - Extremely weathered, tropical soils
* `Histosols` - Soils formed in organic material
* `Vertisols` - Shrinking and swelling clay soils
## Mapping at the Township-Range level
Please refer to this documentation [Overlaying San Joaquin Valley Township Boundaries](doc/etl/township_overlay.md)
## Potential issues
### Description
1. Some map units have `taxorder` with NaN values. This is the case for map units covering cities, lakes, beaches, etc.
Such data points also have a `hydgrp` as NaN.
2. In the soil order table, each map unit identified by the `mukey` feature has multiple land areas (rows) as it can 
contain multiple soil orders of different hydrologic group. In the map dataset, each map unit is also split into 
multiple land area polygons. However not only there are no key/id in both datasets to identify each land area, they 
simply do not match. One land area can be divided into 3 polygons in the map dataset and into 10 soil data points in the
soil orders table without any table key to match them.
3. Soil survey map unit boundaries do not match the boundaries of townships in the TRS land survey system that we are
using in this analysis.
4. The soil survey dataset only contains data from the 2016 soil survey.
5. 
### How did we remediate these issues?
1. Through ETL, data points in the soil dataset without `hydgrp` but with a value `taxorder` value, have their 
`soil_type` value set to the `taxorder` value and data points without a soil `taxorder` value have their `soil_type` 
value set to the `compname` value (e.g. Urban Land, Beaches, Glaciers, Dune land, etc.).
2. For each map unit in the soil dataset, we check based on the `comppct_r` value, which soil type (`taxorder` and 
`hydgrp`) is dominant in this map unit and assign it as the `dominant_soil_type` for this map unit. The soil dataset is 
then merged to the map dataset giving one `dominant_soil_type` per map unit.
3. To split the soil survey map per townships from the TRS land survey system we use the same method described in the 
documentation [Overlaying San Joaquin Valley Township Boundaries](doc/etl/township_overlay.md).
4. As we do not expect the soil type to change from year, the 2016 soil data are used for all the other years.
5. XXXXXXXXXXXXXXXX Write something smart