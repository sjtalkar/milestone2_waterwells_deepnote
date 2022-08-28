# [The Precipitation Dataset](https://cdec.water.ca.gov/reportapp/javareports?name=PRECIPMON")
## Description
Well Water shortage directly relates to insufficient groundwater, but groundwater begins as precipitation - the rain or 
snow that falls to the ground. The water that fully saturates pores or cracks in soils and rocks is termed as 
groundwater. It is **replenished by precipitation** and, depending on the local climate and geology, is unevenly 
distributed  in both quantity and quality. When rain falls or snow melts, some of the water evaporates, some is 
transpired by plants, some flows overland and collects in streams, and some infiltrates into the pores or cracks of the 
soil and rocks. The first water that enters the soil replaces water that has been evaporated or used by plants during a 
preceding dry period. After the water requirements  for plant and soil are satisfied, any excess water will infiltrate 
to the water table--the top of the zone below which the openings in rocks are saturated. Below the 
[water table](https://pubs.usgs.gov/gip/gw/how_a.html), all the openings in  the rocks are full of water that moves 
through the aquifer to streams, springs, or wells from which water is being withdrawn.

## Source
This dataset was scraped from the California Data Exchange Center (CDEC) website. The primary function of CDEC is to 
facilitate the collection, storage, and exchange of hydrologic and climate information to support real-time flood 
management and water supply needs in California. It is an agency within California Department of Water Resources 
which protects, conserves, develops, and manages much of California's water supply.

## How to download?
The `PrecipitationDataset` class in the `/lib/precipitation.py` custom library is designed to load the weather stations
data and geospatial information from the local `/assets/inputs/precipitation/` folder. If they are not found the data
are downloaded from [a dedicated GitHub repository](https://github.com/mlnrt/milestone2_waterwells_data) where we
provide some prepackaged datasets. Please refer to the 
[How to Download the Datasets?](doc/assets/download.md) documentation for more details.

### Original web scrapping
Web scraping was originally employed to scrape data over multiple years from 2013 through 2022. 

The data are downloaded using Python's requests package. The HTML is then parsed using BeautifulSoup. As an example, 
the attributes of the HTML table that contains precipitation data is identified and passed to the 'find' method of the 
constructed BeautifulSoup class.

```python
# Parse the html content
soup = BeautifulSoup(html_content, "lxml")
precipitation_table = soup.find("table", attrs={"id":"data", "class": "data"})  
```

Analysis of the table structure is performed to further identify the specific rows and columns to be retrieved through 
parsing. 
- In the code below for instance, we first identify the table header and save the column names in a list. 
- We then collect all the data rows in the table and loop through the list
- Within each row, we then extract the data in the cell of each row

```python
precipitation_table_header = precipitation_table.thead.find_all("th")  
precipitation_table_header = [th.text for th in precipitation_table_header]
precipitation_table_header = precipitation_table_header[1:]
precipitation_table_rows = precipitation_table.find_all('tr')
all_rows_list = []
for eachTableRow in precipitation_table_rows:
    this_row = []
    for td in eachTableRow.find_all("td"):
        this_row.append(td.text)

    if this_row and len(this_row) > 1:
        all_rows_list.append(this_row)
```

We can then create a dataframe out of the list of data rows and the column headers using pandas. The precipitation 
stations information was similarly scraped with the page url used to retrieve the raw HTML.

Please refer to the
[How to Download the Datasets? - Web Scrapping](doc/assets/download.mdweb-scraping) documentation if you want to run
the web scrapping code yourself.

## Features of interest
The primary feature to be derived from this dataset is the average precipitation in inches for a Township-Range.
The precipitation data is collected for each year and for each precipitation recording station at the month level. The 
average precipitation over the year for every station is computed. 

| Feature Name                 | Description                      |
|------------------------------|----------------------------------|
| AVERAGE_YEARLY_PRECIPITATION | The average yearly precipitation |

## Mapping at the Township-Range level
Precipitations are measured in weather stations in specific locations. In order to estimate the precipitations at the 
Township-Range level per year, for each year we:
* used Voronoi diagrams to estimate precipitations for areas from the point measurements. Please refer to this
documentation for more details: 
[Transforming Point Values into Township-Range Values](doc/etl/from_point_to_region_values.md)
* overlaid the Township-Range boundaries over the Voronoi diagram and averaged the values of the areas intersecting
the Township-Ranges. Please refer to this documentation for more details: 
[Overlaying San Joaquin Valley Township-Range Boundaries](doc/etl/township_overlay.md)
## Potential issues
1. The weather stations are sparsely positioned, and we have to derive the precipitation information from a few stations.
### How did we remediate these issues?
1. As described above, we use a combination of the Voronoi diagram to estimate area measurements, overlay of the 
Township-Range boundaries and compute the average to estimate the precipitation at the Township-Range level. 