# Original Datasets Download
This project uses many datasets from various sources on many different topics:
* Agriculture land use
* Groundwater measurements
* Total population estimates
* Weather stations precipitation measurements
* Water reservoirs
* Water shortage reports
* Soils survey
* Existing vegetation
* Well completion reports

In addition to the above datasets, additional geospatial data were used:
* Public Land Survey System (PLSS) Township-Range-Section (TRS) geospatial data
* California Counties geospatial data
* Land elevation

Original datasets were downloaded using 3 different methods:
* Direct download from the original source URL (most of the datasets)
* Web pages scraping (e.g. Precipitation data from weather stations)
* APIs
## Automated Dataset Download
For each dataset a custom library has been created in the `/lib` folder with a class for each dataset. Initiating the 
class loads the local data files from the `/assets/inputs/<dataset name>/` folder and if they are not found, 
automatically downloads the data either from the original source or from 
[a dedicated GitHub repository](https://github.com/mlnrt/milestone2_waterwells_data) where we provide some data
pre-packaged. 

Running the Jupyter Notebooks in the `/eda` folder will automatically download the data for the datasets corresponding
to the datasets used in the notebook. There is thus no need to manually pre-download any of the datasets in order to
run any of the EDA Jupyter Notebooks.

By automating the download of the original datasets we aim at: 
* ensuring that the data are correctly downloaded,
* simplifying the process for anyone trying to use the project
* improving the reproducibility of the project and the results.
## Pre-packaged Data
Some datasets take time to download through internet pages web scrapping or API calls. For the same reasons as listed
above, and to limit the burden on API services, we provide a pre-packaged version of such the datasets in the 
[GitHub repository](https://github.com/mlnrt/milestone2_waterwells_data). 

Also, the soil survey dataset is a Microsoft Access database, making it complicated to automate the download. We thus,
manually extracted the data from the database and pre-packaged it.

This includes the following datasets:
* The 2014-2021 US Census Bureau American Community (ACS) 5-Year Estimates total population
* The soils survey data and geospatial data
* The elevation of all the wells in the well completion reports

In addition to the above datasets, we provide the following files in that GitHub repository which were manually created
by us for the project:
* A JSON mapping of all crop names to their respective type code
* A JSON mapping of all the existing vegetation type code to their names
## Downloading Original Datasets
### APIs
In the `/llib/download.py` custom library, we provide 2 functions to download some of the raw datasets instead of the 
pre-packaged ones:
* `download_population_raw_data()` to download the 2014-2021 US Census Bureau American Community (ACS) 5-Year Estimates 
total population
* `download_all_elevations()` to download the elevation of all the wells in the well completion reports

Taking the download of the ground surface elevation of all the wells in the well completion reports dataset, we used the
[The National Map - Elevation Point Query Service](https://nationalmap.gov/epqs/) API to collect the elevation of all 
the wells in the dataset, based on their latitude-longitude coordinates. The API call has the following format:

`https://nationalmap.gov/epqs/pqs.php?x=<longitude>&y=<latitude>&units=Meters&output=json`

There are 35,677 wells in the dataset. In order to speed up the download we:
* download the elevation in batches of 1,500 wells
* use multi-threading with 5 workers
* check if batches have already been downloaded and skip them if they have
* if the API throttles us, we wait for a few minutes and try again

To download the elevations, you can run the following Python code for the project root directory:
```python
import sys
sys.path.append(".")
from lib.download import download_all_elevations
download_all_elevations()
```

You will see the following output:

![Elevation data download output](../images/download_elevation.jpg)
### Web Scrapping
Some datasets like the precipitation data from weather stations were not downloaded directly or through APIs. THey were
downloaded using web scrapping of the web pages using the Python package `BeautifulSoup`. The URL used to collect the
data has the following format:

`https://cdec.water.ca.gov/reportapp/javareports?name=PRECIPMON.2016`

### Code details
Please refer to the documented code in the `/lib/download.py` file for the technical details on how some of the 
original datasets were downloaded:
* Land elevation of the Well Completion Reports
* American Community Survey (ACS) total population estimates


