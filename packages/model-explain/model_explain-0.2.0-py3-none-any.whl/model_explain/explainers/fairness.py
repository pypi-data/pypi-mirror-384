# model_explain/explainers/fairness.py

"""
This module provides functions to audit the fairness of machine learning models
using the Fairlearn library. It includes metrics such as Demographic Parity and
Equalized Odds.

Features:
1. Demographic Parity: Measures the difference in positive outcome rates between
   different demographic groups.
2. Equalized Odds: Measures the difference in true positive rates and false positive
   rates between different demographic groups.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

# Import necessary libraries
from fairlearn.metrics import demographic_parity_difference, equalized_odds_difference


def audit_fairness(y_true, y_pred, sensitive_features):
    """
    Audit the fairness of a model using Demographic Parity and Equalized Odds metrics.
    1. Demographic Parity: Measures the difference in positive outcome rates between
       different demographic groups.
    2. Equalized Odds: Measures the difference in true positive rates and false positive
       rates between different demographic groups.
    :param y_true: Actual labels
    :type y_true: array-like
    :param y_pred: Predicted labels
    :type y_pred: array-like
    :param sensitive_features: Sensitive attributes (e.g., race, gender)
    :type sensitive_features: array-like
    :return: dict: A dictionary containing the fairness metrics
    """
    dp = demographic_parity_difference(
        y_true, y_pred, sensitive_features=sensitive_features
    )
    eo = equalized_odds_difference(
        y_true, y_pred, sensitive_features=sensitive_features
    )
    return {"Demographic Parity": dp, "Equalized Odds": eo}
