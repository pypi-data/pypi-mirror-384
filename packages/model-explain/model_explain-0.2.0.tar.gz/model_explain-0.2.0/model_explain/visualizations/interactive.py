# model_explain/visualizations/interactive.py

"""
Interactive visualizations for model explanations using Plotly.

Features:
- Plot feature importance using interactive bar charts.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

# Import necessary libraries
import plotly.express as px


def plot_feature_importance(importances, features):
    """
    Plots feature importance using Plotly.
    :param importances: A list or array of feature importances.
    :type importances: list or array
    :param features: A list of feature names.
    :type features: list
    :return: None: Displays an interactive bar chart of feature importances.
    """
    fig = px.bar(x=features, y=importances, title="Feature Importance")
    fig.show()
