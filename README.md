# California San Joaquin Valley Water Shortage

## Repository Structure
This repository is organized following the below folder structure:
* __assets__ - contains the datasets
  * __input__ contains the raw datasets downloaded from the internet and organized in sub-folders by topics (e.g. crops,
    precipitations, population, etc.)
  * __output__ contains the dataset resulting from the post-processing and merging of all the __input__ datasets. This
    dataset is the one used in the data analysis itself
* __eda__ - contains notebooks of the early exploratory data analysis. There is one notebook per dataset topic, e.g.
  * __crops.ipynb__ - fo the exploration of the crops dataset
  * __population.ipynb__ - for the exploration of the population density dataset
* __etl__ - contains notebooks showing the data preprocessing performed on each dataset. Like for the __eda__ folder,
  there is one notebook per dataset topic
* __lib__ - contains the code for the custom libraries developed to load, perform etl and output all the datasets
* __doc__ - contains the detailed documentation organized per category (see the Table of Contents below)

## Documentation Table of Contents
* Datasets
  * [The Crops Dataset](doc/assets/crops.md)
  * [The Groundwater Dataset](doc/assets/groundwater.md)
  * [The Population Dataset](doc/assets/population.md)
  * [The Precipitation Dataset](doc/assets/precipitation.md)
  * [The Water Reservoir Dataset](doc/assets/reservoir.md)
  * [The Water Shortage Reports Dataset](doc/assets/shortage.md)
  * [The Soils Dataset](doc/assets/soils.md)
  * [The Vegetation Dataset](doc/assets/vegetation.md)
  * [The Well Completion Reports Dataset](doc/assets/well_completion.md)
* Custom Libraries
  * [The WsGeoDataset Class](doc/etl/wsgeodataset.md)
* ETL operations
  * [Overlaying San Joaquin Valley Township-Range Boundaries](doc/etl/township_overlay.md)
  * [Squaring San Joaquin Valley Township-Ranges](doc/etl/squaring_townships.md)
  * [Dropping Rare Township Features](doc/etl/drop_rare_features.md)
  * [Transforming Point Values into Township-Range Values](doc/etl/from_point_to_region_values.md)