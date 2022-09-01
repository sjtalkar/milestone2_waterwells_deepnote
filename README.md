# California San Joaquin Valley Water Shortage
__Objective__: Predict San Joaquin Valley (CA) groundwater level
California's Sustainable Groundwater Management Act (SGMA) was passed in 2014 with the intention to address over 
pumping, halt chronic water-level declines and bring long-depleted aquifers into balance. Despite SGMA, a frenzy of 
well drilling has continued on large farms across the San Joaquin Valley, the state's largest and most lucrative 
agricultural zone. As a result, shallower wells supplying nearly a thousand family homes have gone dry in recent years.

Frequently, perniciously drought-inflicted California, depends on groundwater for a major portion of its annual water 
supply, particularly for agricultural and domestic usage. This project seeks to aid policy makers and natural resource 
management agencies preemptively identify areas prone to overdraft and bring groundwater basins into balanced levels of 
pumping and recharge.
Focused on the San Joaquin Valley, the objectives are:
* __Supervised Learning__: Predict the depth to groundwater elevation in feet below ground surface (GSE_GWE). This value 
portends shortage in a TownshipRange. Increase or decrease in GSE_GWE will then indicate if there will be more requests 
for well construction. This in turn will provide a quantitative metric for whether SGMA is functioning and areas to 
focus on for recharge.
* __Unsupervised Learning__: cluster areas into sustainable and unsustainable areas, anomaly detection

The geographical unit of analysis chosen for this project is the Township-Range level of the Public Land Survey System.

## Repository Structure
This repository is organized following the below folder structure:
* __assets__ - contains the datasets
  * __input__ contains the raw datasets downloaded from the internet and organized in sub-folders by topics (e.g. crops,
    precipitations, population, etc.)
  * __output__ contains the dataset resulting from the post-processing and merging of all the __input__ datasets. This
    dataset is the one used in the data analysis itself
  * __train_test__ contains the datasets used for training and testing the model
  * __models__ contains the artifacts of the trained models
* __eda__ - contains notebooks of the early exploratory data analysis and ETL. There is one notebook per dataset topic, e.g.
  * __crops.ipynb__ - fo the exploration of the crops dataset
  * __population.ipynb__ - for the exploration of the population density dataset
* __ml__ - contains the machine learning notebooks
* __lib__ - contains the code for the custom libraries developed to load, perform etl and output all the datasets
* __doc__ - contains the detailed documentation organized per category (see the Table of Contents below)

## Documentation Table of Contents
* Datasets
  * [Credits and List of Dataset Sources](doc/assets/credits.md)
  * [How to Download the Datasets?](doc/assets/download.md) 
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
* Machine Learning & Deep Learning
  * [Multi-Variate Multi Time-Series Predictions with LSTM](../doc/ml/multivariate_multi_timeseries.md)
  * [How to use the Deep Learning Notebooks?](../doc/ml/deeplearning.md)
  * [Explainability](../doc/ml/explainability_through_shapely.md)
