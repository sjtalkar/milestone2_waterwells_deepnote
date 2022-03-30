# The WsGeoDataset Class
## Why develop our library?
Even though the data they contain are different, in this project we are dealing with mainly two types of datasets
sharing many common characteristics:
* _spatial datasets_, like soils, crops, vegetation,etc. where the data are already represented as land surface area
* _point measurement datasets_, like precipitations, groundwater, etc. where a feature is measured in a particular 
location (e.g. weather stations).

To perform analysis at the [Township-Range level](doc/assets/plss_sanjoaquin_riverbasin.md), land surface areas
in _spatial datasets_ must be [overlay with Township-Ranges boundaries to extract the features](doc/etl/township_overlay.md)
. In _point measurement datasets_ the area values are estimated using [Voronoi diagrams](doc/etl/from_point_to_region_values.md)
and the the Township-Ranges boundaries overaly on top.

In order to:
* avoid code duplication,
* centralize the code for easier maintenance,
* benefit in each datasets ETL process of common tasks, while still allowing for custom dataset retrieval procedures and 
ETL processes,
* increase jupyter notebook readability by offloading the ETL code to libraries,

we created our own library of dataset ETL classes.

## The library structure
```
.
├── /lib
│   ├── wsdataset.py         contains the parent `WsGeoDataset` with all the common functions
│   ├── crops.py             contains the `CropsDataset` class for the [Crops dataset](doc/assets/crops.md) ETL
│   ├── groundwater.py       contains the `GroundwaterDataset` class for the [ground water dataset](doc/assets/groundwater.md) ETL
│   ├── population.py        contains the `PopulationDataset` class for the [population dataset](doc/assets/population.md) ETL
│   ├── precipitation.py     contains the `PrecipitationDataset` class for the [precipitation dataset](doc/assets/precipitation.md) ETL
│   ├── reservoir.py         contains the `ReservoirDataset` class for the [water reservoir dataset](doc/assets/reservoir.md) ETL
│   ├── shortage.py          contains the `ShortageDataset` class for the [water shortage dataset](doc/assets/shortage.md) ETL
│   ├── soils.py             contains the `SoilsDataset` class for the [soils dataset](doc/assets/soils.md) ETL
│   ├── vegetation.py        contains the `VegetationDataset` class for the [vegetation dataset](doc/assets/vegetation.md) ETL
│   ├── wellcompletion.py    contains the `WellCompletionReportsDataset` class for the [well completion reports dataset](doc/assets/well_completion_reports.md) ETL
```

## The Class attributes
* `map_df` - The main Geopandas dataframe holding the geospatial geometries and the feature data
* `data_df` - When geometries and data come from 2 different datasets, the `data_df` is meant to hold the feature data 
before being merged into the geometry in the `map_df`
* `sjv_township_range_df` - The GeoPandas dataframe holding the cleaned-up San Joaquin Valley PLSS geometries
* `sjv_boundaries` - The GeoPandas dataframe holding only 1 big geometry of the outer boundaries of
`sjv_township_range_df`. When we have data for the whole California state, this is used to filter only the data within 
the San Joaquin Valley
* `ca_counties_df` - The GeoPandas dataframe holds the geometries of all the counties in the state of California
* `ca_boundaries` - The GeoPandas dataframe holding only 1 big geometry of the outer boundaries of the state of 
California
* `output_df` - The Pandas dataframe holding the data after final transformation without the geometries, ready to be 
* merged with other datasets and is the one written in a CSV file in the `/assets/outputs` folder

## The main functions