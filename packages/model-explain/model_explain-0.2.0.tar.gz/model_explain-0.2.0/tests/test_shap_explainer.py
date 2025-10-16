# tests/test_shap_explainer.py

"""
Unit tests for the SHAP explainer in the model_explain package.

These tests verify the behavior of the SHAP explainer with scikit-learn models
using the Iris dataset.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from model_explain.explainers.shap_explainer import shap_explainer


def test_shap_output_shape():
    """
    Test that the SHAP explainer returns values matching the input data length.

    Uses a RandomForestClassifier trained on the Iris dataset.
    """
    data = load_iris()
    X = data.data
    model = RandomForestClassifier().fit(X, data.target)
    shap_values = shap_explainer(model, X)
    assert len(shap_values.values) == len(X)


def test_shap_explainer_invalid_model():
    """
    Test that the SHAP explainer raises a ValueError when given an invalid model.
    """
    data = load_iris()
    X = data.data
    try:
        shap_explainer(None, X)
    except Exception as exc:
        assert isinstance(exc, ValueError)


def main():
    """
    Run all SHAP explainer tests.
    """
    test_shap_output_shape()
    test_shap_explainer_invalid_model()
    print("All tests passed!")


if __name__ == "__main__":
    main()
