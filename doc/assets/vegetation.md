# [The Vegetation Datasets](https://www.fs.usda.gov/detail/r5/landmanagement/resourcemanagement/?cid=stelprdb5347192)
## Description
These datasets represent the existing vegetation classification and mapping in the central valley and central coast 
mapping tiles of the [CALVEG mapping zones](https://www.fs.usda.gov/detail/r5/landmanagement/resourcemanagement/?cid=stelprdb5347192).
They contain classification data of existing vegetation in these two regions following the U.S. National Vegetation 
Classification Standard (USNVC) hierarchy.

According to the dataset documentation:
> This Existing Vegetation (EVeg) polygon feature class is a CALVEG (Classification and Assessment with LANDSAT of 
> Visible Ecological Groupings) map product from a scale of 1:24,000 to 1:100,000. The geographic extent entails the 
> northeastern portion of CALVEG Zone 6, Central Coast. Source imagery for this layer ranges from the year 1998 to 2015. 
> The CALVEG classification system was used for vegetation typing and crosswalked to other classification systems in 
> this database including the California Wildlife Habitat Relationship System (CWHR).
## Source
The two existing vegetation datasets are coming from the U.S. Department of Agriculture, Forest Service.

Central Valley dataset Information
* Originator: U.S. Forest Service
* Publication Date: 15-10-2019
* Title: EVeg Mid Region 5 Central Valley
* Geospatial Data Presentation Form: vector digital data
* Online Linkage: [http://data.fs.usda.gov/geodata/edw/datasets.php](http://data.fs.usda.gov/geodata/edw/datasets.php)

Central Coast dataset Information
* Originator: U.S. Forest Service
* Publication Date: 18-01-2018
* Title: EVeg Mid Region 5 Central Coast
* Geospatial Data Presentation Form: vector digital data
* Online Linkage: [http://data.fs.usda.gov/geodata/edw/datasets.php](http://data.fs.usda.gov/geodata/edw/datasets.php)
## How to download ?
The `VegetationDataset` class in the `/lib/vegetation.py` custom library is designed to load the vegetation geospatial
datasets from the local `/assets/inputs/vegetation/` folder. If files are not found the data are downloaded from the
[the USDA Forest Service data website](https://data.fs.usda.gov/geodata/edw/datasets.php?xmlKeyword=existing+vegetation)
page. The custom vegetation cover-type-to-name mapping JSON file is downloaded from 
[a dedicated Github repository](https://github.com/mlnrt/milestone2_waterwells_data) where we provide additional files.

The 2 datasets are ESRI geodatabases which can be downloaded from [the USDA Forest Service data website](https://data.fs.usda.gov/geodata/edw/datasets.php?xmlKeyword=existing+vegetation)
* [Existing Vegetation: Region 5 - Central Valley](https://data.fs.usda.gov/geodata/edw/edw_resources/fc/S_USA.EVMid_R05_CentralValley.gdb.zip)
* [Existing Vegetation: Region 5 - Central Coast](https://data.fs.usda.gov/geodata/edw/edw_resources/fc/S_USA.EVMid_R05_CentralCoast.gdb.zip)

For each of these datasets:
* only the a00000009.* files containing the desired detailed information have been kept.
## Features of interest
The full documentation for the fields in those datasets is available in the metadata link for each of the dataset :
* metadata for the [Central Valley dataset](https://data.fs.usda.gov/geodata/edw/edw_resources/meta/S_USA.EVMid_R05_CentralValley.xml)
* metadata for the [Central Coast dataset](https://data.fs.usda.gov/geodata/edw/edw_resources/meta/S_USA.EVMid_R05_CentralCoast.xml)

A table summary is available in [this documentation](https://www.fs.usda.gov/detail/r5/landmanagement/resourcemanagement/?cid=stelprdb5365219).

We are only interested in the forests' tree types so the features extracted from the original datasets are:

| Feature Name   | Description                                                                                                                                                                                                                                                                             |
|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| SAF_COVER_TYPE | The classification of Society of American Foresters (SAF) Forest Cover Types, which is based on the existing occupancy of an area by tree species (Eyre 1980). See [table 60C for the details](https://www.fs.usda.gov/detail/r5/landmanagement/resourcemanagement/?cid=fsbdev3_047991) |
| geometry       | containing the polygon shapes of each crop field. The polygon coordinates must be converted to EPSG:4326 format                                                                                                                                                                         |

## Mapping at the Township-Range level
Please refer to this documentation [Overlaying San Joaquin Valley Township Boundaries](doc/etl/township_overlay.md)
## Potential issues
### Description
1. The datasets only contain the forests' tree types as per the latest update, 2018 for the Central Coast and 2019 for
the Central Valley.
### How did we remediate these issues?
1. We made the assumption that forests do not change their tree type coverage on a yearly basis. Based on this 
assumption, we used those data for all the years between 2015 to 2021.