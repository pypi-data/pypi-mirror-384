# model_explain/explainers/model_comparison.py

"""
Module for comparing different models using SHAP values.

Features:
1. Model Comparison: Compares multiple models based on their SHAP values to identify
   the most important features influencing their predictions.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

# Import necessary libraries
import shap


def compare_models(models, X_test):
    """
    Compare models based on SHAP values and return the top 3 features for each model.
    :param models: dict of models to compare
    :type models: dict
    :param X_test: test data
    :type X_test: pd.DataFrame
    :return: dict of top 3 features for each model
    """
    comparison = {}
    for name, model in models.items():
        explainer = shap.Explainer(model, X_test)
        shap_vals = explainer(X_test)
        top_features = shap_vals.abs.mean(0).argsort()[-3:][::-1]
        comparison[name] = [X_test.columns[i] for i in top_features]
    return comparison
