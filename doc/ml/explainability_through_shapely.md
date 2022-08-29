**Explainability through SHAP**

!["Diagram Description automatically generated"](../doc/images/shapely-1.png)

Figure 1: Power set of features

**Motivation for using SHAP**

The models we create in this project, whether as supervised learning
linear, tree based models or deep learning models, predict the
groundwater depth in future years in a township-range based on certain
features of the township-range and point in time, such as the ground
elevation, precipitation and population density to name a few. The
prediction can be explained based on the coefficients of the predictors
(in the case of linear models) or GINI impurity metric or node
importance in decision trees. Deep Learning models such as LSTM are
harder to explain and for our stakeholders, who make policy decisions
based on whether impact of growing population or reduced rainfall is
greater, **Sh**apely **A**dditive ex**P**lanations importance can play a
significant role in providing model agnostic explanations.\
Aside from the requirement cited above, in several domains,
interpretability is a legal requirement or understanding the model to
debug it when it breaks, can be a necessity.

Originally introduced in 2017 by Lundberg and Lee in
[this](https://arxiv.org/abs/1705.07874) paper, SHAP, which is based on
Game Theory, assigns each feature an importance value for a particular
prediction. 

-   The "Game" is reproducing the outcome of the model

-   The "Players" are the features in the model

We want to understand quantitively how much each feature such as
Precipitation or Ground Surface Elevation contributes to the Ground
Water Depth for a Township-Range in any particular year. In other words,
SHAP is about the local interpretability of a predictable model. Each
combination of features (or players) contributes to a "coalition" in the
Game. If we have 'n' features or players (the number of coalitions
(combinations of player contributions) = 2^n^. As seen in the tree
representation of the Power Set of features, in Figure 1, where every
node is a coalition, each edge represents the inclusion of a feature not
present in the previous coalition. Each coalition can be thought of as a
predictive model, with the prediction of Ground Water Depth, as seen in
the node. Note again that the tree corresponds to a singular set of
features and one instance of observation say, I~0.~

The root node is the model is with no features which will predict the
ground water depth as the average of all observations (this is the
baseline). In the next level, each feature contributes individually to
the model to predict the groundwater depth.

**Marginal Contribution**

Since SH**A**P, makes note of incrementally adding a feature as the
difference between the predictions of two connected nodes we can derive
the marginal contribution of a feature as we traverse an edge. In the
edge movement from no features to addition of precipitation feature, the
marginal contribution is calculated as 125 -- 90 = 35

!["Shapely 2"](../doc/images/shapely-2.png)
Formulaically, this can be represented as: )

MC~Precipitation,{Precipitation}(I₀)~ = Predict~{Precipitation}(I₀)~ -
Predict~Φ~ ( I~0~)

We now extend this to every edge that connects nodes to which the
feature Precipitation is added, so that we can compute the overall
"marginal computation" of Precipitation. Since the nodes have other
features as well, we weight the contribution of Precipitation
accordingly. For instance, in the below weighted edges,

!["Shapely 3"](../doc/images/shapely-3.png)\
\
SHAP ~Precipitation~ (I~0~) = w1 \* MC~Precipitation~,~{Precipitation}~
(I~0~) +\
w2 \* MC~Precipitation~,~{Precipitation,\ Groundsurface\ Elevation}~
(I~0~) +\
w3 \* MC~Precipitation~,~{Precipitation,\ Pop.\ Density}~ (I~0~) +\
w4 \*
MC~Precipitation~,~{Precipitation,\ Groundsurface\ Elevation,\ Pop.\ Density}~
(I~0~)

where *w₁+w₂ +w₃+w₄=*1.

To compute the weights, group the number of contributions at each level
:

*w₁+(w₂ +w₃)+w₄ = 1 i.e,\
1/3 + 1/3 + 1/3 = 1\
=\> w₁ = 1/3 and w4 = 1/3\
while w2 + w3 = 1/3 =\> w2 = 1/6 and w3 = 1/6*

*\
*The above pattern indicates that the weight of an edge is the
reciprocal of the total number of edges in the same "row". The weight of
a marginal contribution to an n feature-model is the reciprocal of
possible marginal contributions to all the n-feature-models. It is
simplified in a visual as:

!["Shapely 4"](../doc/images/shapely-4.png)
The number of all the marginal contributions of all the n-feature-models
alternatively, the number of edges in each row) is :\
If the Total number of features is N and possible
n-feature-models/coalitions = n, then the number of all the marginal
contributions of all the n-feature-models is\
n \* ~N~C~n~

The weight of the marginal contribution to an n-feature-model is the
reciprocal of the above.

[**Programmatic usage of SHAP python
package**](https://pypi.org/project/shap/)

SHAP was utilized for explainability in the project. Interpret the
instance feature importance :

import shap\
explainer = shap.explainer (model)\
shap.plots.waterfall(shap_values\[0\])

The XGBoostRegressor model in our study indicated the current
groundwater depth followed by groundsurface elevation of the township
range are the the top predictors and the red bar showing increase in
predicted value and blue bar denoting a decrease. The gray text before
the feature names shows the value of each feature for this sample, in
the below it is normalized data.

!["Shapely Waterfall"](../doc/images/shapely-5.png)

Credits: [SHAP Values explained exactly how you wished someone
explained to
you.](https://towardsdatascience.com/shap-explained-the-way-i-wish-someone-explained-it-to-me-ab81cc69ef30)\
[SHAP
documentation](https://shap.readthedocs.io/en/latest/example_notebooks/api_examples/plots/waterfall.html)
