# model_explain/explainers/nl_summary.py

"""
This module provides a function to generate a natural language summary
explaining the prediction of a machine learning model based on SHAP values.

Features:
- Generates human-readable explanations for model predictions.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

# Import necessary libraries
import numpy as np


def generate_summary(instance, shap_values, feature_names, prediction, class_names):
    """
    Generate a natural language summary explaining the model's prediction.
    :param instance: An array-like structure representing the input instance.
    :type instance: np.ndarray or pd.Series
    :param shap_values: An array-like structure representing the SHAP values for the instance.
    :type shap_values: np.ndarray
    :param feature_names: A list of feature names corresponding to the instance.
    :type feature_names: list[str]
    :param prediction: The predicted class index for the instance.
    :type prediction: int
    :param class_names: A list of class names corresponding to the model's output classes.
    :type class_names: list[str]
    :return: A natural language summary explaining the prediction.
    :rtype: str
    """
    top_indices = np.argsort(np.abs(shap_values))[::-1][:3]
    reasons = [
        f"{feature_names[i]} was {'high' if instance.iloc[i] > 0 else 'low'}"
        for i in top_indices
    ]
    reason_text = ", and ".join(reasons)
    return f"The model predicted '{class_names[prediction]}' because {reason_text}."
