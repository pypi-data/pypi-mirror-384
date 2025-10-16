# model_explain/utils/model_loader.py

"""
Utility function to load a machine learning model from a specified file path.

Features:
- Uses joblib for loading models.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

# Import necessary libraries
import joblib
import os


def load_model(path):
    """
    Load a machine learning model from the specified file path.
    :param path: The file path to the saved model.
    :type path: str
    :return: The loaded model object.
    :rtype: object
    :raises FileNotFoundError: If the specified file does not exist.
    :raises Exception: For any other issues encountered during loading.
    """
    if not isinstance(path, str):
        raise ValueError("The path must be a string.")
    if not path:
        raise ValueError("The path cannot be empty.")
    if not os.path.exists(path):
        raise FileNotFoundError(f"The specified file does not exist: {path}")
    try:
        return joblib.load(path)
    except Exception as e:
        raise Exception(f"An error occurred while loading the model: {e}")
