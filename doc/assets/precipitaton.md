# [California Precipitation Dataset](https://cdec.water.ca.gov/)
## Description

California precipitation is monitored at uniformly distributed stations along the landscape of the state.
The Department of Water Resources hosts and maintains a California Data Exchange Center website to 
_"facilitate  the collection, storage, and exchange of hydrologic and climate information to support real-time flood management and water supply
 needs in California."_


 

## Features of interest
For this analysis we limit ourselves to the main class of crops (e.g. `Deciduous fruits and nuts`, `Vineyard`, etc),
without going the sublass details of each crop (e.g. `Apples`, `Apricots`, `Cherries`, etc for the `Deciduous fruits 
and nuts` class). This means that we are assuming that each crop in a class have the same agricultural impact on
water usage and resources. This assumption obviously does not hold but is made in order to simplify the analysis.

Thus the features extracted from the original dataset are:
* `DWR_Standa` - the July crop class in the 2014 dataset. We keep only the first letter of the column which corresponds
to the class code (e.g. "V | VINEYARD") and corresponds to the class codes used in the 2016 and 2018 datasets 
* `CLASS2` - the summer crops in the 2016 and 2018 datasets.
* `geometry` - containing the polygon shapes of each crop field. The polygon coordinates must be converted to 
EPSG:4326 format. 
* 
The 2016 and 2018 have other interesting features like:
* `IRR_TYP1PA` - which indicates if the land is irrigated or not for the crop farming
* `IRR_TYP2PA` - which provides details on the type of irragation performed on a specific farming land.

Unfortunately those data are available only for the 2016 and 2018 datasets. It feels very complicated to augment the
2014 dataset with irrigation status from past years as a crop/farming land in 2014 might not necessary cover the
same land area and might be used for a different crop with a different irrigation system. These fields have thus been 
ignored at this stage.

Aquifers water level are usually measured in spring when they are at their maximum levels due to water recharge from
snowpack melting and precipitations. On the contrary the main crop growing season is the summer months and is as such
the season having the biggest impact on water usage. For this analysis we thus limit ourselves to the summer crops data.
## Mapping at the Township level
Please refer to this documentation [Overlaying San Joaquin Valley Township Boundaries](doc/etl/township_overlay.md)
## Potential issues
### Description
1. The 2014 and 2016-2018 datasets organize data differently
  * The 2014 dataset list all the crops individually by class names (e.g. `D ¦ Deciduous fruits and nuts`) in the 
`DWR_Standa` column and name (e.g. `Strawberries`, `Tomatoes`, `Grapes`... ) in the `Crop2014` dataset while the 
2016-2018 organize the crops by class codes (e.g. `D` for `Deciduous fruits and nuts`) and subclasses (e.g. `D1` for 
`Apples`, `D2` for `Apricots`, etc). 
  * The 2014 dataset only list one crop type per area, while the 2016-2018 datasets list one crop type per season when 
available with `CLASS1` column corresponding to spring crops, `CLASS2` to summer crops, etc.
2. Compared to other datasets we do not have a dataset per year.
3. The crops classification in R,R,F,P,T... classes has little to do with the amount of water required to grow a
specific crop. E.g. `Beans`, `Flowers, nursery & Christmas tree farms`, `Lettuce or Leafy Greens`, `Potato or Sweet 
potato` are all in the same class `T`. But obviously the impact of growing trees, lettuces or potatoes is not the same
in terms of water consumption. 
### How did we remediate the issues?
The above issues were remediated as follow:
1. In the 2016 and 2018 datasets we limited ourselves to the summer crops class (the `CLASS2` column).
2. Having only data for 3 years over the analysis survey, we assume little year-to-year variation in crop farming and 
extended the data for the missing years (2015, 2017, ~2019) with the data from the previous years 
(i.e. we assume that 2015 crops = 2014 crops). We understand that farming practices like crop rotation would challenge
these assumptions.
3. This problem has been ignored at this stage
