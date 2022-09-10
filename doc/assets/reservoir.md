# [The Reservoir and Reservoir Station Datasets](https://cdec.water.ca.gov/reservoir.html)

## Description
We will be using reservoir data as further indication or lack thereof of groundwater replenishment. A water reservoir 
is an artificial pond, formed in a river valley or other basin by a barrier or dam and having controlled or 
uncontrolled outlets. The rising of surface water level has some impact on the groundwater level in adjacent areas.

## Source
This dataset was scraped from the California Data Exchange Center (CDEC) website.The primary function of CDEC is to 
facilitate the collection, storage, and exchange of hydrologic
and climate information to support real-time flood management and water supply needs in California. It is an agency 
within California Department of Water Resources which protects,
conserves, develops, and manages much of California's water supply. 

## How to download?
The `ReservoirDataset` class in the `/lib/reservoir.py` custom library is designed to load the reservoir stations data
and geospatial information from the local `/assets/inputs/reservoir/` folder. If they are not found the data
are downloaded from an AWS S3 bucket (which is publicly available) where we provide some prepackaged datasets. Please
refer to the [How to Download the Datasets?](doc/assets/download.md) documentation for more details.

### Original web scrapping
Web scraping was employed to scrape data over multiple years. The data is only available from April 2018 through 2022 
and it is published at the weekly level for all reservoir stations in the state. These stations may or may not be the 
same as those that monitor precipitation.

The data are downloaded using Python's requests package. The HTML is then parsed using BeautifulSoup. As an example, 
the attributes of the HTML table that contains precipitation data is identified and passed to the 'find' method of the 
constructed BeautifulSoup class.

```Python
# Parse the html content
soup = BeautifulSoup(html_content, "lxml")
reservoir_table = soup.find("table", attrs={"id":"RES", "class": "data"}) 
```

Analysis of the table structure is performed to further identify the specific rows and columns to be retrieved through 
parsing. 
* In the code below for instance, we first identify the table header and save the column names in a list. We make sure 
to trim off excess space. 
* We then collect all the data rows in the table and loop through the list
* Within each row, we then extract the data in the cell of each row

```Python
reservoir_table_header = reservoir_table.thead.find_all("th")  
reservoir_table_header = [th.text for th in reservoir_table_header]
reservoir_table_header = [elm.strip() for elm in reservoir_table_header[1:]]
reservoir_table_rows = reservoir_table.find_all('tr', {'class': 'white'})
all_rows_list = []
for eachTableRow in reservoir_table_rows:
    this_row = []
    for td in eachTableRow.find_all("td"):
        this_row.append(td.text.strip())

    if this_row and len(this_row) > 1:
        all_rows_list.append(this_row)
```

We can then create a dataframe out of the list of data rows and the column headers using pandas. The reservoir station 
location information was similarly scraped with the page url used to retrieve the raw HTML.

Please refer to the
[How to Download the Datasets? - Web Scrapping](doc/assets/download.mdweb-scraping) documentation if you want to run
the web scrapping code yourself.

## Features of interest
The reservoir data is collected for each year at a weekly level and for each reservoir recording station for its 
location. The average percentage of storage capacity over the year for every station is then computed.

We have the station's latitude and longitude available to us. We use the strategy described in the 
[California Well Completion Report Dataset documentation](/doc/well_completion_reports.md) and 
[California Groundwater Dataset and Stations documentation](/doc/groundwater.md) to convert the latitude and longitude 
to point geometry and then through spatial join into Township-Range. The merging of the datasets can then be performed 
through the Township-Range.

The features extracted from the web scrapping (and stored into `/assets/inputs/reservoir/` folder) are:

| Feature Name     | Description                                                    |
|------------------|----------------------------------------------------------------|
| PCT_OF_CAPACITY  | The average percentage of storage capacity for a station       |
| geometry         | containing the latitude and longitude of the reservoir station |

## Mapping at the Township-Range level
The strategy in the project is:
- Create a GeoDataFrame when starting from a regular DataFrame that has latitudinal and longitudinal coordinates. Each 
reservoir report should have a viable latitude and longitude that can be converted to points. If not, the record is 
dropped from the dataset.
- We use geopandas `points_from_xy()` to transform longitude and latitude into a list of shapely. Point objects and set
it as a geometry while creating the GeoDataFrame.
- Once we have a GeoDataframe with the points in the coordinate reference system, we spatially join to the California 
PLSS GeoJSON to map to the closest Township-Range using `sjoin` method in geopandas.

## Potential issues
None identified.