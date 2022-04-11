# [California Household Water Supply Shortage Dataset ](https://data.cnra.ca.gov/dataset/household-water-supply-shortage-reporting-system-data)

## Description
Household well shortage reports from 2015 through 2022 publicly available dataset is available for API retrieval. There 
are less than 5000 records of reported shortage.

In California, water systems serving one (1) to 15 households are regulated at the county level. Counties vary in their 
practices, but rarely do counties collect data regularly from these systems. Even where data is collected, it is 
**entirely voluntary**. A review of well permit information suggests there are over 1 million such water systems in 
California.

In early 2014, a cross-agency Work Group created an easily accessible reporting system to get more systematic data on 
which parts of the state had households at risk of water supply shortages. The initial motivation for local water supply 
systems to report shortage information was to obtain statewide drought assistance. The reporting system receives ongoing 
reports of shortages from local, state, federal and non-governmental organizations, and tracks their status to 
resolution. While several counties have developed their own tracking mechanisms, this data is manually entered into 
the reporting system.

The cross-agency team, led by DWR, seeks to verify and update the data submitted. However, due to the volunteer nature 
of the reporting and limitations on reporting agencies, collected data are undoubtedly **under-representative of all 
shortages to have occurred**. In addition, reports are received from multiple sources and there are occasionally errors 
and omissions that can create duplicate entries, non-household water supply reporting, and under-reporting. For example, 
missing information or no data for a given county does not necessarily mean that there are no household water shortages 
in the county, rather only that none have been reported to the State.

## Source
This data is published by The Department of Water Resources that manages California's water resources, systems, 
and infrastructure, including the State Water Project (SWP), in a responsible, sustainable way.

Datasets information:
* Organization: California Department of Water Resources
* Contact  Name: Benjamin Brezing
* Title: Household Water Supply Shortage Reporting System Data
* Resources, website: [https://data.cnra.ca.gov/dataset/household-water-supply-shortage-reporting-system-data](https://data.cnra.ca.gov/dataset/household-water-supply-shortage-reporting-system-data).

## How to download ?
The `ShortageReportsDataset` class in the `/lib/shortage.py` custom library is designed to load the well shortage 
reports dataset from the local  `/assets/inputs/shortage/` folder. If files are not found, it is  automatically 
downloaded from the 
[Household Water Supply Shortage Reporting System Data](https://data.cnra.ca.gov/dataset/household-water-supply-shortage-reporting-system-data) 
page, when running the `/eda/shortage.ipynb` notebook. 

The datasets can be manually downloaded from the 
[Household Water Supply Shortage Reporting System Data](https://data.cnra.ca.gov/dataset/household-water-supply-shortage-reporting-system-data) 
page, using the download button.

## Features of interest
The features extracted from the original datasets in the EDA notebook are:

| COLUMN         | DESCRIPTION                                                                                                                               |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| Status         | Local Agency designated status [null, outage, temporary, resolved]                                                                        |
| Shortage Type  | Answer to: What type of water shortage are you facing? [Dry well (groundwater); Low creek, stream, spring, or other surface water source] |
| Primary Usages | Answer to: What is the primary use of this well or creek? [Household; Ag/Irrigation; Combination of Household/Agriculture; Other __]      |
| County         | [pull down of California counties]                                                                                                        |
| LATITUDE       | [Interactive map generates latitude, longitude, street address, city, zip code, or; numerical decimal degrees]                            |
| LONGITUDE      | [Interactive map generates latitude, longitude, street address, city, zip code, or; numerical decimal degrees]                            |
| Report Date    | Answer to: Report Date [available only if reported by agency/local government/housing assistance organization; ___]                       |

Based on the above features we compute the below features per Township-Range and year:

| Feature Name   | Description                                                          |
|----------------|----------------------------------------------------------------------|
| SHORTAGE_COUNT | The total number of well shortage report per Township-Range and year |

## Mapping at the TownshipRange level
To compute well shortage count per Township-Range we use the following approach:
1. We overlay the Township-Ranges boundaries on the well geolocation information and group wells by Township-Range.
2. We count the number of wells per Township-Range and year in the WELL_COUNT feature.
3Township-Ranges without any new well completion reported get a value of 0 for all the WELL_COUNT features 

## Potential issues
### Description
As mentioned above, reporting this data is voluntary and abscence of shortage for a county does not represent due absence of shortage
The data is in its raw form and has to be cleaned to make it usable.
### How did we remediate the issues?
