## [XBBoost](https://www.analyticsvidhya.com/blog/2016/03/complete-guide-parameter-tuning-xgboost-with-codes-python/)

[Statquest video](https://www.youtube.com/watch?v=OtD8wVaFm6E)
[Ritvik Math](https://www.youtube.com/watch?v=en2bmeB4QUo)
[Statquest Python implementation](https://www.youtube.com/watch?v=GrJP9FLV3FE)

It is Extreme Gradient Boosting best suited for large complicated datasets, 

### Understanding Boosting
- A family of models with production level implications. When we learn a final predition function F(x),
  it will be a sum of  **underspowered sequential weak learners** (these weak learners could be any linear regression/svm/tree).

#### STEP 0

    1. Define your loss function. True label and y-hat (prediction). Should be differentiable.

#### STEP 1

    1. Start with extremely weak learner (F1(x)) Say it is the mean of the y targets
    2. This is the initial prediction.
    3. The residuals (sum of difference of each data point from the mean(the current mode) line) show how good or bad this initial prediction is.


#### STEP 2
    This is essetially gradient descent

    Compute quantities r<sub>1i</sub> Where 1 is the first weak learner....
    This is the derivative of the loss function at data point i with respect to current prediction using F(x)- the first wek learner.

    At every iteration we add the previous weak learner to a gamma*(new learner) 
    That is we move in the direction of the decreasing loss by a factor of a learning rate (gamma).

    Every week learner descends down the gradient by reducing the loss.

#### STEP 2 DETAILED
    1. Start with all residuals in a leaf node
    2. Calculate the Similarity Score for this leaf which is the Square of the Sum of the Residuals 
       divided by (number of Residuals + lambda). Lambda is the regularization parameter that minimizes dependence on any one feature.
       Note the residuals are not sqaured before summing.Some of the residuals might cancel each other out.
    3. Now the question is : Can we do a better job if we cluster resdiuals together in some manner.(create a line separating the clusters)
    4. We split the observations into two parts based on say an average of a feature. 
    5. Calculate the similarity score of each leaf node with residuals clustered into the two nodes.
    6. The Gain is the sum of the similarity scores of these two leaf nodes minus the similarity score of the "root" node.
    7. We keep the clusters that result in the largest Gain.     
    8. Pruning trees. Set a threshold: Tree Complexity Parameter (gamma) to compare Gains against. If the Gain is greater than gamma, then the tree is not pruned. We start with the lowest tree.
    9. Lambda, the regularization parameter when set to more than 0, also can cause tree pruning, since it reduces the Similarity Scores and hence the Gain (which is compared to the threshold Gamma)
   10. Lambda has a greater effect on tree pruning than Gamma.
   11. After the trees have been created, we calculate the Outcome.Outcome is the Sum of Residuals/(number of residuals + Lambda) 
   12. Once we have the Outcomes we can make new predictions. Learning Rate = ETA 
       = original prediction (typically mean) + Learning Rate x Output



 


It has  the following features:


1. Regularization (lambda) used in Similarity Score computation where
   Similarity Score of a leaf is:
   square of (sum of residuals in a leaf)/(number of residuals in the leaf) + (lambda)
   In fact, XGBoost is also known as a ‘regularized boosting‘ technique.
2. Pruning: XGBoost on the other hand make splits upto the max_depth specified and then start pruning the tree backwards and removes splits beyond which
   there is no positive gain.

3.  XGBoost Parameters
    
    The overall parameters have been divided into 3 categories by XGBoost authors:

    - General Parameters: Guide the overall functioning
    - Booster Parameters: Guide the individual booster (tree/regression) at each step
    - Learning Task Parameters: Guide the optimization performed  

    - eta [default=0.3]
        - Analogous to learning rate in GBM
        -  Makes the model more robust by shrinking the weights on each step
        - Typical final values to be used: 0.01-0.2  

    - min_child_weight [default=1]
       -  Defines the minimum sum of weights of all observations required in a child.
       -  This is similar to min_child_leaf in GBM but not exactly. This refers to min “sum of weights” of observations while GBM has min “number of observations”.
       -  Used to control over-fitting. Higher values prevent a model from learning relations which might be highly specific to the particular sample selected for a tree.
       - Too high values can lead to under-fitting hence, it should be tuned using CV.

    -  lambda [default=1]
        - L2 regularization term on weights (analogous to Ridge regression)
        - This used to handle the regularization part of XGBoost. Though many data scientists don’t use it often, it should be explored to reduce overfitting.
        
    - alpha [default=0]
        - L1 regularization term on weight (analogous to Lasso regression)
        - Can be used in case of very high dimensionality so that the algorithm runs faster when implemented.
        - Look for reg_lambda

    - scale_pos_weight [default=1]
        - A value greater than 0 should be used in case of high class imbalance as it helps in faster convergence.  
