# model_explain/visualizations/feature_importance_plot.py

"""
This module provides a function to visualize feature importance using bar plots.
It uses Matplotlib and Seaborn for plotting.

Features:
- plot_feature_importance: Plots feature importance as a horizontal bar plot.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

# Import necessary libraries
import matplotlib.pyplot as plt
import seaborn as sns


def plot_feature_importance(importances, feature_names, title="Feature Importance"):
    """
    Plots feature importance as a horizontal bar plot.
    :param importances: A list or array of feature importance values
    :type importances: list
    :param feature_names: A list of feature names corresponding to the importances
    :type feature_names: list
    :param title: Title of the plot
    :type title: str
    :return: None: Displays the plot
    """
    sns.barplot(x=importances, y=feature_names)
    plt.title(title)
    plt.xlabel("Importance")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.show()
