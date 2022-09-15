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
  * __tuning__ contains a dataset of 33,345 trained LSTM models' hyperparameters and RMSE value
* __eda__ - contains notebooks of the early exploratory data analysis and ETL. There is one notebook per dataset topic, e.g.
  * __crops.ipynb__ - fo the exploration of the crops dataset
  * __population.ipynb__ - for the exploration of the population density dataset
* __ml__ - contains the machine learning notebooks
* __lib__ - contains the code for the custom libraries developed to load, perform etl and output all the datasets
* __doc__ - contains the detailed documentation organized per category (see the Table of Contents below)

## Python Environment
The project uses multiple libraries, some having tricky dependencies and requirements, especially on Windows. To
facilitate the setup of the environment, on top of the requirements.txt listing the version of packages used, we
recommend to run the below script to create a conda environment with all the required packages and their dependencies.
```
conda create -n sjv-groundwater -y python=3.9
conda activate sjv-groundwater
conda install -y jupyter
conda install -c conda-forge -y fiona==1.8.21 altair==4.2.0 beautifulsoup4==4.10.0 geopandas==0.10.2 pygeos==0.12.0 numpy==1.21.5 pandas==1.3.5 ipywidgets==7.7.0 lxml==4.8.0 mapclassify==2.4.3 matplotlib==3.5.2 pillow==9.1.0 plotly==4.4.1 requests==2.27.1 scikit-learn==0.24.2 tqdm==4.64.0 seaborn==0.11.2 xgboost==1.6.2 catboost==1.0.6 shap==0.41.0 
pip install gpdvega==0.1.1rc1 graphviz==0.19.2 
pip install tensorflow==2.9.1 keras-tuner==1.1.2
```
Note: Streamlit is not included in the above script as it is not required to run the notebooks. 

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
  * [Multi-Variate Multi Time-Series Predictions with LSTM](doc/ml/multivariate_multi_timeseries.md)
  * [How to use the Deep Learning Notebooks?](doc/ml/deeplearning.md)
  * [Explainability](doc/ml/explainability_through_shapely.md)
