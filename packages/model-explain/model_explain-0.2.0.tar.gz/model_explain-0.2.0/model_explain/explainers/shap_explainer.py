# model_explain/explainers/shap_explainer.py

"""
This module provides a SHAP explainer function to interpret machine learning models.

Features:
- Computes SHAP values for a given model and dataset.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

# Import necessary libraries
import shap


def shap_explainer(model, X):
    """
    SHAP Explainer Function
    ----------------------------------
    This function creates a SHAP explainer for the given model and dataset.
    It computes SHAP values for the dataset using the provided model.
    :param model: Trained machine learning model
    :type model: Any
    :param X: Input dataset for which SHAP values are to be computed
    :type X: pd.DataFrame or np.ndarray
    :return: SHAP values object
    :rtype: shap.Explanation
    """
    explainer = shap.Explainer(model, X)
    shap_values = explainer(X)
    return shap_values
