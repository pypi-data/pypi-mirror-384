# model_explain/explainers/surrogate.py

"""
This module implements a surrogate model explainer using a decision tree classifier.
The surrogate model approximates the predictions of a more complex model, providing
a simpler and more interpretable representation of its decision-making process.

Goal: Train interpretable surrogate model to mimic complex model predictions.

Features:
- Uses DecisionTreeClassifier from scikit-learn.
- Fits the surrogate model on the predictions of the complex model.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

# Import necessary libraries
from sklearn.tree import DecisionTreeClassifier


def train_surrogate(model, X):
    """
    Train a surrogate decision tree model to approximate the predictions of a complex model.
    :param model: The complex model to be approximated.
    :type model: sklearn.base.BaseEstimator
    :param X: Feature data used for training.
    :type X: array-like
    :return: A trained surrogate decision tree model.
    :rtype: sklearn.tree.DecisionTreeClassifier
    """
    y_pred = model.predict(X)
    surrogate = DecisionTreeClassifier(max_depth=3)
    surrogate.fit(X, y_pred)
    return surrogate
