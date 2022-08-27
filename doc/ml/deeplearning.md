# How to use the Deep Learning Notebooks?
The Deep Learning experiment used to try to produce an [LSTM model](doc/ml/multivariate_multi_timeseries.md) is made
of 3 Jupyter Notebooks:
1. [Deeplearning LSTM Model Hyperpamaters Tuning](ml/deeplearning_tuning.ipynb) where we perform hyperparameter tuning
on 3 multiple LSTM model architectures to find the best hyperparameters for each architecture.
2. [Deeplearning LSTM Model Training and Testing](ml/deeplearning_training.ipynb) where we train and test all 3
LSTM models with the best hyperparameters found in the previous notebook and find the best model of the 3.
3. [Predicting With the LSTM Model](ml/deeplearning_results.ipynb) where we train the best of the 3 models and use it
to predict the groundwater elevation in the San Joaquin Valley in 2022.

## Requirements
* tensorflow version 2.9.1
* keras-tuner version 1.1.2

Refer to the [requirements.txt](requirements.txt) file for mre details on the ythonrequirements of this project.