# model_explain/explainers/summary.py

"""
Module for generating textual summaries of model explanations.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

# Import necessary libraries
from model_explain.explainers import generate_summary


def batch_generate_summaries(data, shap_values, predictions, classes):
    """
    Generate textual summaries for a batch of data instances.
    :param data: The input data as a DataFrame.
    :type data: pd.DataFrame
    :param shap_values: SHAP values corresponding to the data instances.
    :type shap_values: np.ndarray
    :param predictions: Model predictions for the data instances.
    :type predictions: np.ndarray
    :param classes: List of class labels.
    :type classes: list[str]
    :return: List of textual summaries for each data instance.
    :rtype: list[str]
    """
    summaries = []
    for i, instance in data.iterrows():
        summary = generate_summary(
            instance, shap_values[i], data.columns, predictions[i], classes
        )
        summaries.append(summary)
    return summaries
