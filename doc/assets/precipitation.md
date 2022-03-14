# [The Precipitation Dataset](https://cdec.water.ca.gov/reportapp/javareports?name=PRECIPMON")
## Description


Well Water shortage directly relates to insufficient groundwater, but groundwater begins as precipitation - the rain or snow that falls to the ground. 
The water that fully saturates pores or cracks in soils and rocks is termed as groundwater. It is **replenished by precipitation** and, depending on the local climate and geology, is unevenly distributed 
in both quantity and quality. When rain falls or snow melts, some of the water evaporates, some is transpired by plants, some flows overland and collects in streams, and some infiltrates into
the pores or cracks of the soil and rocks. The first water that enters the soil replaces water that has been evaporated or used by plants during a preceding dry period. After the water requirements 
for plant and soil are satisfied, any excess water will infiltrate to the water table--the top of the zone below which the openings in rocks are saturated.Below the [water table](https://pubs.usgs.gov/gip/gw/how_a.html), all the openings in 
the rocks are full of water that moves through the aquifer to streams, springs, or wells from which water is being withdrawn. 

## Source
This dataset was scraped from the California Data Exchange Center (CDEC) website.The primary function of CDEC is to facilitate the collection, storage, and exchange of hydrologic
and climate information to support real-time flood management and water supply needs in California. It is an agency within California Department of Water Resources which protects,
conserves, develops, and manages much of California's water supply. 

## How to download ?

Web scraping was employed to scrape data over multiple years from 2013 through 2022. The data can be manually downloaded by entering the year for the download but it is expedited using BeautifulSoup 
by sending requests through Python's requests package. The raw HTML is retrieved from the response. The HTML is then parsed using BeautifulSoup. As an example, using Chrome Browser Developer tools, the aatributes of the
HTML table that contains precipitation data is identified and passed to the 'find' method of the constructed BeautifulSoup class.

``` python
# Parse the html content
soup = BeautifulSoup(html_content, "lxml")
precipitation_table = soup.find("table", attrs={"id":"data", "class": "data"})  
```

Analysis of the table structure is performed to furthe identify the specifuc rows and columns to be retrieved through parsing. 
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

We can then create a dataframe out of the list of datarows and the column headers using pandas. The precipitation stations information was similarly scraped with the page url used to retrieve the raw HTML.

## Features of interest

The precipitation data is collected for each year and for each precipitation recording station at the month level. The average precipitation over the year for every station is first computed.
We have the station's latitude and longitude available to us. We use the strategy described in well_completion_reports.md and groundwater.md to convert the latitude and longitude to point geomtery and then through spatial join 
into TownshipRange. Merge to othe datasets can now be performed through this TownshipRange.

The primary feature to be derived from this dataset is the average precipitation in inches for a TownshipRange.

## Mapping at the Township level

The strategy in the project is:
- Create a GeoDataFrame when starting from a regular DataFrame that has latitudinal and longitudinal coordinates. Each shortage report should have a viable latitude and longitude that can be converted to points.
  If not, the record is dropped from the dataset.
- A GeoDataFrame needs a shapely object.
-  We use geopandas points_from_xy() to transform Longitude and Latitude into a list of shapely.Point objects and set it as a geometry while creating the GeoDataFrame.
- Once we have a GeoDataframe with the points in the coordinate reference system, we spatially join to the California PLSS GeoJSON to map to the closest TownshipRange using sjoin method in geopandas.

## Potential issues
The availablity of data for precipitation is limited by the collection of data by the stations positioned in the river basin of interest. We have to average the data over the year since the precipitation over
the entire year has the possibility of feeding the groundwater subsystem.
The stations are sparsely positioned and we have to derive/impute the precipitation information from a few stations' data that is available, for other townships where a station is not located.

### How did we remediate these issues?
For TownshipRanges where a station is not situated, the average of precipitation of the entire region will be allocated.