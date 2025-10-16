# model_explain/utils/explainability_score.py

"""
This module provides a function to compute an explainability score for machine learning models.
The score is based on the model's feature importance and complexity.

Features:
- Computes a score between 0 and 100.
    - Higher scores indicate more explainable models.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

# Import necessary libraries
import numpy as np


def compute_explainability_score(model):
    """
    Compute an explainability score for a given machine learning model.
    The score is based on feature importance and model complexity.
    Higher scores indicate more explainable models.
    :param model: A trained machine learning model with attributes 'feature_importances_' and 'max_depth'.
    :type model: object
    :return: float: Explainability score between 0 and 100.
    """
    score = 0
    if hasattr(model, "feature_importances_"):
        importance = model.feature_importances_
        top_features = np.sum(np.sort(importance)[-3:])
        score += top_features * 50  # weight for concentration
    if hasattr(model, "max_depth"):
        depth_penalty = max(0, 10 - model.max_depth)
        score += depth_penalty * 5
    return min(score, 100)
