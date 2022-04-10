# Public Land Survey System

## Understanding PLSS
The Public Land Survey System (PLSS) is the surveying method developed and used in the United States to plat, or divide, land for sale and settling. 
Also known as the Rectangular Survey System, it was created by the Land Ordinance of 1785.
Under this system the lands are divided into “townships,” 6 miles square, which are related to base lines established by the federal government. The base lines running north and south are known as
 “Principal Meridians”, while the east and west base lines are called simply “Base Lines”. The township numbers east or west of the Principal Meridians are designated as ranges; whereas, the numbers north
 and south of the Base Line are tiers.

Thus, the description of a township as “Township 16 North, Range 7 West” would mean that the township is situated 16 tiers north of the Base Line for the Principal Meridian and 7 ranges west of that meridian.
Guide Meridians, at intervals of 24 miles east and (or) west of the Principal Meridian, are extended north and (or) south from the Base Line; Standard Parallels, at 24-mile intervals north and (or) south of 
the Base Line, are extended east and (or) west from the Principal Meridian.

The Township is 6 miles square. It is divided into 36 square-mile “sections” of 640 acres, each which may be divided and subdivided as desired. The diagram below show the system of numbering the sections and
the usual method of subdividing them.

![PLSS pictorial description](https://raw.githubusercontent.com/sjtalkar/milestone2_waterwells_deepnote/master/doc/images/plss_info.png)

We will merge datasets at the TownshipRange level. 

The geometries available to us are of two different types : points (specific locations) and polygons (areas). 

1. In the case of well Completion reports, groundwater reports, shortage, precipitation and reservoir data, we have latitude and longitude of specific points of interest,
such as the well, the groundwater station, or the stations recording the precipitation and reservoir data. From the logitude and latitude, geopandas enables us to translate these values to 
 point coordinates within a specified reference plane. For instance in a pandas dataframe 'df' with columns 'longitude' and 'latitude', the following geopandas function call with return a series that can be saved in a column called 
 'geometry' (this is the default column name in geopandas, but it can be varied). Note the Coordinate Reference System (CRS) of the geometry objects created. If you then call, df.crs, you will be informed of the CRS of the geomtery 
 column of the dataframe which comes in very handy when you want to merge two geometries or chart on projection over another and need to align them, say a a base map of counties and well locations.  

```Python
  geopandas.points_from_xy(df.longitude, df.latitude, crs="EPSG:4326")
```

Once we have the geometry of stations or well locations, we can then spatially join the dataframe to the subbasin dataframe. As explained in the [geopandas documentation](https://geopandas.org/en/stable/docs/user_guide/mergingdata.html?highlight=spatial%20join#spatial-joins),
in a Spatial Join, observations from two GeoSeries or GeoDataFrame are combined based on their spatial relationship to one another. Attributes from either dataframe can be brought into the other. For instance if we perform a left join of 
precipitation stations to the subbasin, we retain precipitation value recorded in the precipitation station and the point in the CRS where the station is located, but we also bring in the TownshipRange and County from the subbbasin dataframe 
in which the station is located, thus enabling us to average the precipitation over the years for TownshipRanges and counties.
On the other hand we can right join the two dataframes and this will retain the geomtery of the right dataframe (subbasin). This geometry is a polygon or multi-polygon which dentoes counties and TownshipRanges. We then have converted the
point in the station dataframe to the containing polygon region for aggregation and charting purposes.   

**GeoDataFrame.sjoin()** has two core arguments: how and predicate.

**how**
The how argument specifies the type of join that will occur and which geometry is retained in the resultant GeoDataFrame. It accepts the following options:

- left: use the index from the first (or left_df) GeoDataFrame that you provide to GeoDataFrame.sjoin(); retain only the left_df geometry column

- right: use index from second (or right_df); retain only the right_df geometry column

- inner: use intersection of index values from both GeoDataFrame; retain only the left_df geometry column


**predicate**
The predicate argument specifies how geopandas decides whether or not to join the attributes of one object to another, based on their geometric relationship. The default spatial index in geopandas currently supports the following values 
for predicate which are defined in the Shapely documentation:

- intersects

- contains

- within

- touches

- crosses

- overlaps


2. When it come to land areas covered by crops and soil or vegetation, we have to determine the proportion of land that falls within the PLSS region of the San Joaquin river basin. The document 
[township_overlay.md]('../doc/etl/township_overlay.md') goes into deeper depth to explain the manner in which this proportion is calculated.


## Description
The investigation in this project is confined to the San Joaquin valley. Characteristics of this region include:

- Climate
    - The San Joaquin Basin has mild winters and particularly hot and dry summers.
- Land Use
    - A large part of the population of the basin is involved in all facets of agricultural production. Gradually, the population is shifting towards supporting the large urban areas and industry.


## Source
[Data Download of SanJoaquin river basin PLSS geoJSON](https://github.com/datadesk/groundwater-analysis/blob/main/data/plss_subbasin.geojson)

## How to download ?
The file can be downloaded using the download link in Github. The raw file has to saved with extension geojson.

## Features of interest
The geojson is used as is.


## Mapping at the TRS level
The geojson is joined spatially with points in a geo dataframe to yield columns that can then be merged on Township, Range or TownshipRange levels.
For details, please refer to [this documentation](../etl/township_overlay.md). 

## Potential issues
### Description
None
### How did we remediate these issues?



