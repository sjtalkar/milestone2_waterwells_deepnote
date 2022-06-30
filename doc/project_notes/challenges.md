### Challenges faced when working on this dataset

##### Issue 1

The California Groundwater Shortage has 10 datasets but as might be expected, these datasets are not complete, that is we have data for some years (when it is recorded) and
 not for others. So it is not just a matter of dropping NaNs as if we do so, we lose the ability to look into an entire year at a time or are being forced to drop entire features.

**To be specific with examples:**
Dataset has 478 TownshipRanges and data for years from 2014-2021 for most features but not all. For many features we have to infer the value from the previous year.

`Vegetation/Crops/Soil features`

The nature of the data as in the case of soil of an area is such that it can be reasonably assumed to be the same for the next year. Also we have  spatial component where we can 
impute the data for a TownshipRange based on its value from a previous year. But when we impute for a test set, the previous year data is not available to us.

`Population Density feature:`
The population of the test set containing year 2021 can be derived from the population of 2020 and the trend over the previous year.
Now, we learned about data cleaning and making a decision on how to treat NaNs in SIADS 505 but we were not working with  a split dataset and could comfortably impute
over the entire dataset well into the last year of the dataset. In our case, using scikit-learn pipelines, when we fit the imputation based on a township-range and year 
in the training set,  and then try to transform the test set with this imputation, the pipeline cannot grab the data for a certain previous year trend.

In this case how do we go about with imputing values for the test set? We would ideally not like to drop features not available in the test set. If we perform imputation
prior to splitting the dataset (like we did in 505, then would that be considered as data leakage?

**Status**
Resolved

**Resolution**
When you are dealing with temporal data you should, generally, hold out more recent years. That is, you want your models to be valid in 2021, and you want to have your model trained
 on years from 2014-2020, because 2022 is when you actually want to be able to make predictions.
So in a case like this, you might separate out 2014-2020 into training, and 2021 into testing.
Now, you can do whatever you want to 2014-2020, impute, fit, transform, whatever, that's what you're going to learn from. , then when you go to predict() on 2021, you need
 to have those features filled in, or at least you would like to. There is no problem imputing those features from the 2014-2020 dataset. 
**The key is that you're not in the learning task here, and this holdout set is your future set, so you are not leaking information back into the past**

For the imputation:
- We can split the train and test set
-  We create the pipeline
-  We fit_transform the train set
-  We recombine the train and test (or just use the full dataset).
-  We transform the test dataset (we only have forward fills and so data from the future is leaking into the past)
-  Split the full set imputed and extract out the test set.

##### Issue 2
The scores for linear regression models and decision tree are neagtive for the test set.

The singular vector machine with a radial base kernel performed slightly better than the linear and decision tree regressors.
The KNN performed marginally better too.

I tried to fit a Polynomial function on the train and test but ran out of memory.

**Status:**
Unresolved

**Ideas**
- Drop features and check if that impacts scores
- Have tried with different scalers
- Check if dimensionality reduction techniques applied work such as PCA
- Check if K Means clustering applied to the dataset works

##### Issue 3

PyCaret takes a long time to load

**Status:**
PyCaret was installed inside the notebook with 
```
!pip install pycaret[full]
```
The notebook kernel should be restarted after this.
PyCaret has several limitations arising out of dependencies of various packages being mismatched with the packages currently 
in use in the project. 

**Ideas**
- Check if by using the already split train and test we can have another requirements files that contains 
PyCaret and sklearn 0.23.0 as in the local environment

##### Issue 4

Low (as in 0.1-0.2) r-squared score with [SVM](https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html) and
 with PyCaret highlighted best algorithm [Extra Trees Regressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesRegressor.html)

**Status:**
Tried adding clustering labels to the features. This had an impact but imprived score by 0.01
Made sure the target which is left skewed is normalized. This made a large impact. About 27% increase in R-squared.

Tried out XGBoost and  hypertuned the parameters. This along with normalized target has brought the training score up
to 95%, a huge increase but the test score is very low.

Other things to try :
1. Reduction algorithm such as PCA to reduce number of correlated features
2. Radical change: Try a different target variable, number of wells for instance.



**Ideas**
- Check if by using the already split train and test we can have another requirements files that contains 
PyCaret and sklearn 0.23.0 as in the local environment


##### Issue 5

- Transforming the target, poses challenges in using cross validation since you need to inverse_transform before
  scoring

**Status:**
[Wrap the model in TransformedTargetRegressor](https://machinelearningmastery.com/how-to-transform-target-variables-for-regression-with-scikit-learn/)


##### Issue 6
Which score to use to evaluate model. Why the scitch from r-square to mean squared error or root mean sqaured 
error was made.

https://github.com/keras-team/keras/issues/14090
https://stats.stackexchange.com/questions/83948/is-r-squared-value-appropriate-for-comparing-models
https://www.bmc.com/blogs/mean-squared-error-r2-and-variance-in-regression-analysis/


##### Issue 7

- Major difference in number of components when the data is scaled using StandardScaler versus MinMaxScaler
- I split up the research into MinMaxScaler and StandardScaler notebooks. The variations in the algorithmic evaluation and PCA is so radical that these two scaling methods have to be differentiated.
With Standard Scaling, the Biplot does not look awesome, but the components make total sense.
- The Silhouette score is better with StandardScaler
- The evaluation metrics for testing are better
- With MinMaxScaling, the Silhouette Score does not show as much negative area for the first three clusters

