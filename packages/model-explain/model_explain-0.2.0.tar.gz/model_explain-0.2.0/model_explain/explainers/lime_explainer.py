# model_explain/explainers/lime_explainer.py

"""
LIME Explainer for Tabular Data
This module provides a function to create a LIME explainer for tabular data.

Features:
1. LIME Explainer: Generates local explanations for individual predictions made by
   machine learning models.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

# Import necessary libraries
from lime.lime_tabular import LimeTabularExplainer


def lime_explainer(model, X, instance_index=0):
    """
    Create a LIME explainer for tabular data.
    :param model: Trained machine learning model
    :type model: sklearn.base.BaseEstimator
    :param X: Feature data as a pandas DataFrame
    :type X: pandas.DataFrame
    :param instance_index: Index of the instance to explain
    :type instance_index: int
    :return: LIME explanation object
    :rtype: lime.lime_tabular.LimeTabularExplainer
    """
    explainer = LimeTabularExplainer(
        X.values,
        feature_names=X.columns,
        class_names=["target"],
        verbose=True,
        mode="classification",
    )
    explanation = explainer.explain_instance(
        X.iloc[instance_index].values, model.predict_proba
    )
    return explanation
