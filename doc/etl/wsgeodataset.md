# The WsGeoDataset Class
## Why Develop our own Library?
Even though the data they contain are different, in this project we are dealing with mainly two types of datasets
sharing many common characteristics:
* _spatial datasets_, like soils, crops, vegetation,etc. where the data are already represented as land surface areas
* _point measurement datasets_, like precipitations, groundwater, etc. where a feature is measured in a particular 
location (e.g. weather stations).

To perform analysis at the [Township-Range level](doc/assets/plss_sanjoaquin_riverbasin.md), land surface areas
in _spatial datasets_ must be [overlay with Township-Ranges boundaries to extract the features](doc/etl/township_overlay.md)
. In _point measurement datasets_ the area values are estimated using [Voronoi diagrams](doc/etl/from_point_to_region_values.md)
and the  Township-Ranges boundaries overlay on top.

In order to:
* avoid code duplication,
* centralize the code for easier maintenance,
* ensure consistency of common ETL processes,
* benefit in each dataset ETL process of common tasks, while still allowing for custom dataset retrieval procedures and 
ETL processes,
* increase jupyter notebook readability by offloading the ETL code to libraries,

we created our own library of dataset ETL classes.

## The Library Structure
```
.
├── /lib
│   ├── wsdataset.py        contains the parent `WsGeoDataset` with all the common functions
│   ├── crops.py            contains the `CropsDataset` class for the Crops dataset ETL
│   ├── groundwater.py      contains the `GroundwaterDataset` class for the ground water dataset ETL
│   ├── population.py       contains the `PopulationDataset` class for the population dataset ETL
│   ├── precipitation.py    contains the `PrecipitationDataset` class for the precipitation dataset ETL
│   ├── reservoir.py        contains the `ReservoirDataset` class for the water reservoir dataset ETL
│   ├── shortage.py         contains the `ShortageDataset` class for the water shortage dataset ETL
│   ├── soils.py            contains the `SoilsDataset` class for the soils dataset ETL
│   ├── vegetation.py       contains the `VegetationDataset` class for the vegetation dataset ETL
│   ├── wellcompletion.py   contains the `WellCompletionReportsDataset` class for the well completion reports dataset ETL
│   ├── viz.py              contains visualization functions
│   ├── download.py         contains functions to download some of the raw original datasets
```

## The Class Attributes

| Attribute               | Description                                                                                                                                                                                                                  |
|:------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `map_df`                | The main Geopandas DataFrame holding the geospatial geometries and the feature data                                                                                                                                          |
| `data_df`               | When geometries and data come from 2 different datasets, the `data_df` is meant to hold the feature data before being merged into the geometry in the `map_df`                                                               |
| `sjv_township_range_df` | The GeoPandas DataFrame holding the [cleaned-up San Joaquin Valley PLSS geometries](doc/etl/squaring_townships.md), which is used to compute features at the Township-Range level                                            |
| `sjv_boundaries`        | The GeoPandas DataFrame holding only 1 big geometry of the outer boundaries of `sjv_township_range_df`. When we have data for the whole California state, this is used to filter only the data within the San Joaquin Valley |
| `ca_counties_df`        | The GeoPandas DataFrame holds the geometries of all the counties in the state of California. This is used for visualisation purposes                                                                                         |
| `ca_boundaries`         | The GeoPandas DataFrame holding only 1 big geometry of the outer boundaries of the state of California. This is used for visualisation purposes.                                                                             |
| `counties_and_trs_df`   | A combination of both Township-Range boundaries `sjv_township_range_df` and County boundaries `ca_counties_df`                                                                                                               |
| `output_df`             | The Pandas DataFrame holding the data after final transformation without the geometries, ready to be merged with other datasets and is the one written in a CSV file in the `/assets/outputs` folder                         |

## The Parent Class Main Functions
Here is a description of the main functions of the parent `WsGeoDataset()` class . Internal functions used to perform 
some of the computation are not described here. Please refer to the library and the functions DocStrings for details.

### List Functions by Operation
| Operation you want to perform                                                                                                                                                                                                                  | Function                                                                                               |
|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------|
| __[Process and Merge Datasets](#process-and-merge-datasets)__                                                                                                                                                                                  ||
| Pre-process the geospatial data                                                                                                                                                                                                                | [preprocess_map_df()](#libpreprocess_map_df)                                                           |
| Pre-process the features data before merging with geospatial data                                                                                                                                                                              | [preprocess_data_df()](#libpreprocess_data_df)                                                         |
| Merge geospatial data with feature data                                                                                                                                                                                                        | [merge_map_with_data()](#libwsdatasetsmerge_map_with_data)                                             |
| __[Geospatial Manipulation](#geospatial-manipulation)__                                                                                                                                                                                        ||
| Keep only the data in the San Joaquin Valley                                                                                                                                                                                                   | [keep_only_sjv_data()](#libwsdatasetskeep_only_sjv_data)                                               |
| Cut the dataset area geometries with the Township-Range boundaries                                                                                                                                                                             | [overlay_township_boundaries()](#libwsdatasetsoverlay_township_boundaries)                             |
| Estimate the measurement for an entire area based on measurements performed in specific locations (e.g. estimate the precipitations in a region based on measruements recorded in weather stations).                                           | [compute_areas_from_points()](#libwsdatasetscompute_areas_from_points)                                 |
| Take all the values of all the small areas within Township-Ranges to estimate the Township-Range values.                                                                                                                                       | [aggregate_areas_within_townships()](#libwsdatasetsaggregate_areas_within_townships)                   |
| Take all the values of all the points in Township-Ranges to estimate the Township-Range values. This is an internal function of the parent class. Child classes can use in their own functions to perform aggregations specific to their data. | [_get_aggregated_points_by_township()](#libwsdatasets_get_aggregated_points_by_township)               |
| Get normalized values of a feature in the geospatial dataset. This is generally done for visualization purposes in EDA Jupyter Notebooks.                                                                                                      | [return_yearly_normalized_township_feature()](#libwsdatasetsreturn_yearly_normalized_township_feature) |
| __[Data Output](#data-output)__                                                                                                                                                                                                                ||
| Copy the geospatial `map_df` GeoDataFrame into the `output_df` DataFrame, dropping the geospatial geometry information.                                                                                                                        | [prepare_output_from_map_df()](#libwsdatasetsprepare_output_from_map_df)                               |
| Drop some features before writing the result of the ETL process into a file                                                                                                                                                                    | [drop_features()](#libwsdatasetsdrop_features)                                                         |
| Store the result of the ETL process from the `output_df` DataFrame into a file                                                                                                                                                                 | [output_dataset_to_csv()](#libwsdatasetsoutput_dataset_to_csv)                                         |
### Process and Merge Datasets

#### lib.*.preprocess_map_df
Process the geospatial `map_df` DataFrame. The parent class just filters the necessary columns, each dataset specific class 
performs operations specific to the dataset

Refer to each dataset specific function DocString for more information.
#### lib.*.preprocess_data_df
When data (e.g. the Soils dataset) are split between their geospatial geometries and the features, this function process
the feature dataset `data_df` before merging it with the geospatial data

Refer to each dataset specific function DocString for more information.
#### lib.wsdatasets.merge_map_with_data
When data (e.g. the Soils dataset) are split between their geospatial geometries and the features, this function merges 
the two together. The merging is done based on the class `self.__merging_keys` attribute

*merge_map_with_data(how: str = "left", dropkeys: bool = False, dropna: bool = False)*

| Parameter                      | Description                                                                             |
|:-------------------------------|:----------------------------------------------------------------------------------------|
| __how:__ *str, optional*       | How to merge the data (e.g. "left", "right", "inner"). Default is *left*.               |
| __dropkeys:__ *bool, optional* | When *True* drops the map and data keys from the final map dataset. Default is *False*. |, optional* | how to merge the data (e.g. "left", "right", "inner"). Default is "left". |
| __dropna:__ *bool, optional*   | When *True* drops rows with missing values in the data dataset. Default is *False*.     |
### Geospatial Manipulation
#### lib.wsdatasets.keep_only_sjv_data
This function keeps only the `map_df` data in the San Joaquin Valley. 

*keep_only_sjv_data()*

| Parameter | Description |
|:----------|:------------|
| None      | -           |
#### lib.wsdatasets.overlay_township_boundaries
This function overlays the San Joaquin Valley Township-Range on top of the dataset `map_df` geospatial data. The result
overwrites the `map_df` attribute.

Please refer to the provided documentation 
[Overlaying San Joaquin Valley Township-Range Boundaries](doc/etl/township_overlay.md) for details about how the 
operation is performed.

*overlay_township_boundaries(set_precision: bool = False)*

| Parameter                          | Description                                                                                                                                                                                                                            |
|:-----------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| __set_precision:__ *str, optional* | When *True*, this sets the precision of the geometries to __1e-6__. This is done for some datasets with many small geometries to avoid `TopologyException: found non-noded intersection error from overlay` errors. Default is *False* |
#### lib.wsdatasets.compute_areas_from_points
This function takes geospatial points data (e.g. precipitation recorded in one location), and computes a Voronoi Diagram
to estimate area measurements based on point measurements. The operation is performed year by year. The result
overwrites the `map_df` attribute.

Please  refer to the provided documentation 
[Transforming Point Values into Township-Range Values](doc/etl/from_point_to_region_values.md) for details about how the 
operation is performed.

*compute_areas_from_points(boundary: str = "ca")*

| Parameter                     | Description                                                                                                                                                            |
|:------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| __boundary:__ *str, optional* | the envelope or boundary to use to compute the Voronoi Diagram. Acceptable values are *"ca"* for California and *"svj"* for the San Joaquin Valley. Default is *"ca"*. |
#### lib.wsdatasets.aggregate_areas_within_townships
After overlaying the Township-Range boundaries on top of the dataset, a Township-Range area can include multiple areas
each with their own value. This function essentially aggregates the values of the areas within the Township-Range 
boundaries, using the aggregation function passed as an argument. The result overwrites the `map_df` attribute.

*aggregate_areas_within_townships(group_by_features: List[str], aggfunc: str = "mean")*

| Parameter                                    | Description                                                                                                                   |
|:---------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------|
| __group_by_features:__ *List[str], required* | The features used to group by geometries to compute the aggregated value. Typical values will be *["TOWNSHIP_RANGE", "YEAR"]* |
| __aggfunc:__ *str, optional*                 | The aggregation function. Default is *mean*.                                                                                  |
#### lib.wsdatasets.return_yearly_normalized_township_feature
This function returns a Pandas DataFrame with the argument feature normalized using the normalisation function passed as
an argument.

*return_yearly_normalized_township_feature(feature_name: str, normalize_method: str = "minmax")*

| Parameter                             | Description                                                                                                                                                                                                                    |
|:--------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| __feature_name:__ *str, required*     | The feature to normalize.                                                                                                                                                                                                      |
| __normalize_method:__ *str, optional* | The method to use for normalization. Acceptable values are *minmax* for normalization using a min-max scaler, *std* for normalization using a standard scaler and *mean* for simple division by the mean. Default is *minmax*. |
| __Returns__                           |                                                                                                                                                                                                                                |
| a GeoPandas DataFrame                 ||

#### lib.wsdatasets._get_aggregated_points_by_township
This is an internal function which can be used in child classes to use geospatial point measurements and aggregate them
by Township-Range and year. E.g. If 3 measures where performed in different places of a Township-Range in a specific
year, and if the aggregation function is mean, the result will be the mean of the 3 measures.

*_get_aggregated_points_by_township(by: List[str], features_to_aggregate: List[str], aggfunc: str = "mean",
new_feature_suffix: str = None, fill_na_with_zero: bool = True)*

| Parameter                                        | Description                                                                                   |
|:-------------------------------------------------|:----------------------------------------------------------------------------------------------|
| __by:__ *List[str], required*                    | The list of columns to group the data by. Typical values will be *["TOWNSHIP_RANGE", "YEAR"]* |
| __features_to_aggregate:__ *List[str], required* | The list of features to aggregate.                                                            |
| __aggfunc:__ *str, optional*                     | The aggregation function. Default is *mean*.                                                  |
| __new_feature_suffix:__ *str, optional*          | The suffix to add to the new feature names. Default is *None*.                                |
| __fill_na_with_zero:__ *bool, optional*          | If *True*, fills NaN values with 0. Default is *True*.                                        |
| __Returns__                                      |                                                                                               |
| a GeoPandas DataFrame                            | The original features are dropped from the result Dataframe.                                  |
### Data Output
#### lib.wsdatasets.pivot_township_categorical_feature_for_output
This function prepares the `output_df` DataFrame by pivoting the geospatial DataFrame, using the values in the
`feature_name` parameter as the new feature columns and the land surface percentage the feature occupies in the
Township-Range as the cell values.

Please refer to the provided documentation 
[Overlaying San Joaquin Valley Township-Range Boundaries](doc/etl/township_overlay.md) for an example of pivoting the
categorical features of the geospatial dataset after overlying the Township-Range boundaries.

*pivot_township_categorical_feature_for_output(feature_name: str, feature_prefix: str = "")*

| Parameter                           | Description                                                         |
|:------------------------------------|:--------------------------------------------------------------------|
| __feature_name:__ *str, required*   | The categorical feature to use as columns in the pivoted DataFrame. |
| __feature_prefix:__ *str, optional* | A prefix to add to the new feature name.                            |

#### lib.wsdatasets.prepare_output_from_map_df
This function prepares the result of the ETL to be written to file by copying the `map_df` DataFrame to the `output_df` 
DataFrame and dropping the geospatial geometry column. A list of columns to drop can also be passed.

*prepare_output_from_map_df(unwanted_features: List[str] = None)*

| Parameter                                    | Description                                                  |
|:---------------------------------------------|:-------------------------------------------------------------|
| __unwanted_features:__ *List[str], optional* | The list of the specific columns to drop from the DataFrame. |
#### lib.wsdatasets.drop_features
This function is used to drop features from the `output_df` DataFrame before saving it to a file. Please refer to the 
documentation [Dropping Rare Township Features](doc/etl/drop_rare_features.md) for more details.

*drop_features(drop_rate: float = 0.0, unwanted_features: List[str] = None)*

| Parameter                                    | Description                                                                                                            |
|:---------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------|
| __drop_rate:__ *float, optional*             | Any feature which does not appear more than the drop_rate in any of the Township-Range for every year will be dropped. |
| __unwanted_features:__ *List[str], optional* | The list of the specific columns to drop from the DataFrame.                                                           |

#### lib.wsdatasets.output_dataset_to_csv
This function writes the self.output_df DataFrame into a CSV file.

*output_dataset_to_csv(output_filename: str)*

| Parameter                            | Description           |
|:-------------------------------------|:----------------------|
| __output_filename:__ *str, required* | The name of the file. |