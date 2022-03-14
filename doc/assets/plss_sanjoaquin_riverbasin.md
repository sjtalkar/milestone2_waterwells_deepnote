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
![PLSS pictorial description](https://github.com/sjtalkar/milestone2_waterwells_deepnote/blob/master/doc/images/plss_info.png)

We will merge datasets at the TownshipRange level.

## Description
The investigation in this project is confined to the San Joaquin valley. Characteristics of this region include:

- Climate
    - The San Joaquin Basin has mild winters and particularly hot and dry summers.
- Land Use
    - A large part of the population of the basin is involved in all facets of agricultural production. Gradually, the population is shifting towards supporting the large urban areas and industry.


## Source
[Data Download of SanJoaquin river basin PLSS geoJSON](https://github.com/datadesk/groundwater-analysis/blob/main/data/plss_subbasin.geojson
)

## How to download ?
The file can be downloaded using the download link in Github. The raw file has to saved with extension geojson.

## Features of interest
The geojson is used as is.


## Mapping at the TRS level
The geojson is joined spatially with points in a geo dataframe to yield columns that can then be merged on Township, Range or TownshipRange levels.

## Potential issues
### Description
None
### How did we remediate these issues?



