# How to use the Deep Learning Notebooks?
The Deep Learning experiment used to try to produce an [LSTM model](doc/ml/multivariate_multi_timeseries.md) is made
of 2 Jupyter Notebooks:
1. [Deeplearning LSTM Model Hyperpamaters Tuning](ml/deeplearning_tuning.ipynb) where we perform hyperparameter tuning
on 3 multiple LSTM model architectures to find the best hyperparameters for each architecture.
2. [Training, Testing and Predicting With an LSTM Model](ml/deeplearning.ipynb) where, based on the hyperparameters found in the previous notebook, we 
  * train and test all 3 LSTM models with the best hyperparameters
  * perform hyperparameters sensitivity analysis on the best model
  * use the best model to predict the groundwater elevation in the San Joaquin Valley in 2022.

## Requirements
* tensorflow version 2.9.1
* keras-tuner version 1.1.2

Refer to the [requirements.txt](requirements.txt) file for more details on the python requirements of this project and the main [README.md](../../README.md) for the shell script to setup a Conda environment with the projet dependencies.