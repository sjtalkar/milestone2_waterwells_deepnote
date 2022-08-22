# Multi-Variate Multi Time-Series Predictions with LSTM
## The Data
In a multi-variate multi time-series prediction problem, the inputs are 3 dimensional, made of multiple subjects, 
each characterized by several features (X1 - X4 and Y), each being a time-series.
The objective is to predict the value of one feature (many-to-one), here Y, or multiple features (many-to-many), 
one or multiple steps into the future (one step *Y(t+n+1)* in this example).

LSTMs are used for time series and NLP because they are both sequential data and depend on previous states.
The future prediction *Y(t+n+1)* depends not only on the last state *X1(t+n) - Y(t+n)*, not only on past values of the 
feature *Y(t+1) - Y(t+n)*, but on the entire past states sequence.

Examples:
* IoT devices collecting multiple metrics over time.
* A server farm, each measuring CPU, memory, disk IO usage over time.
* Retail stores sales of multiple products over time, etc.

![Multi-Variate Multi TImes-Series Predictions with LSTM - Training and Prediction](../images/lstm_inputs_outputs.jpg)

In our case, the dataset is made of 478 Township-Ranges, each containing a multivariate (81 features) time series 
(data between 2014 to 2021). This dataset can thus be seen as a 3 dimensional dataset of $478 TownshipRanges * 
8 time stamps * 81 features$
The objective is to predict the 2022 target value of `GSE_GWE` (Ground Surface Elevation to Groundwater Water Elevation 
- Depth to groundwater elevation in feet below ground surface) for each Township-Range.

## Feeding the LSTM Model
LSTM models are often explained with NLP examples. Using this is as an analogy, here
* subjects (sentences) are passed into the model
* each cell in the LSTM neural network receives a subject’s state at a specific time
(a word, the state of the sentence at a specific position)
* each state in the series is represented by a multi-dimensional vector of all features
(the word vector), here X1 - X4 and Y.

This example shows a many-to-one LSTM model where the output is the subject’s next state for
the specific feature Y, one time stamp into the future (the next word in the sentence).

![Multi-Variate Multi TImes-Series Predictions with LSTM - Cells Inputs](../images/lstm_table_to_cells.jpg)