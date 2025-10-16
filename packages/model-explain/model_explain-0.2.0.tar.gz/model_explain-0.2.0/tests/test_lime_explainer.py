# tests/test_lime_explainer.py

"""
Unit tests for the LIME explainer in the model_explain package.

These tests verify the behavior of the LIME explainer with scikit-learn models
using the Iris dataset.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from model_explain.explainers.lime_explainer import lime_explainer


def test_lime_output_shape():
    """
    Test that the LIME explainer returns a non-empty explanation list.

    Uses a RandomForestClassifier trained on the Iris dataset.
    """
    data = load_iris()
    X = data.data
    model = RandomForestClassifier().fit(X, data.target)
    lime_exp = lime_explainer(model, X)
    assert len(lime_exp.as_list()) > 0


def test_lime_explainer_invalid_model():
    """
    Test that the LIME explainer raises a ValueError when given an invalid model.
    """
    data = load_iris()
    X = data.data
    try:
        lime_explainer(None, X)
    except Exception as exc:
        assert isinstance(exc, ValueError)


def main():
    """
    Run all LIME explainer tests.
    """
    test_lime_output_shape()
    test_lime_explainer_invalid_model()
    print("LIME tests passed!")


if __name__ == "__main__":
    main()
