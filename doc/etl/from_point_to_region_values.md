# Transforming Point Values into Township Values
## What is the Problematic?
Some of the data are collected and recorded in specific locations while we need them for all the townships of the San 
Joaquin Valley. An example is precipitation which is collected in weather stations, but there is not one weather station
for every township. If we look at all the weather stations in the state of California, from which we were able to 
collect data, we get the following map. The San Joaquin Valley (in grey) which has 409 townships, only has 16 weather 
stations.

!["California weather station"](../images/precipitation_stations.png)

How do we fill in the data for the townships without weather stations ?

## Solution applied

According to this documentation on [precipitation measurements](https://www.weather.gov/abrfc/map) from the U.S. 
National Weather Service, there are several methods which can be used to estimate areal precipitations from point
measurements. We decided to use the _Thiessen polygon_ method. Python's `shapely` library has a built-in
`voronoid_diagram()` function making it easy, given any weather station to build the _Thiessen polygon_ for that 
station.

## How does it work?
Taking a set of point measurements, a _[Voronoi diagram](https://en.wikipedia.org/wiki/Voronoi_diagram)_ is computed. 
The Voronoi Diagram is made of _Thiessen polygons_ representing the regions close to each of the point measurements.

!["Voronoi Diagram"](../images/voronoi_diagram.png)

We then overlay the Township boundaries on top of the Voronoi diagram and calculate the mean of the polygon values
within the townships. In the example below:
* Township TR1, which includes the point measurement with value 1, would have a value of 1
* Likewise township TR9 would have a value of 2
* Township TR13, which includes no point measurement and is included in a _Thiessen polygon_, would have the value of 1 
which is the value of the point measurement of that polygon
* Township TR5 which overlays 3 _Thiessen polygons_ would have the value equal to the mean of the three polygons it 
crosses. That is (3+2+1)/3=2
* Likewise township TR6 would have a value of (1+3+3+4+2)/5=2.6

!["From point measurements to Township value"](../images/point_to_township_value.png)

## Result
The result of the average precipitations per township for the year 2021 in the San Joaquin Valley is as follow.

!["2021 San Joaquin Valley Townships Average Precipitations"](../images/sjv_townships_precipitation.png)

## Code 
Please refer to the `compute_areas_from_points()` function in the `wsdatasets` library [here](lib/wsdatasets.py). 