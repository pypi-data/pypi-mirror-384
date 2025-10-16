# tests/test_counterfactual_explainer.py

"""
Unit tests for the `generate_counterfactual` function in the model_explain package.

These tests use pytest and unittest.mock to validate:
- Output correctness
- Output shape
- Handling of invalid models
- Robustness to bad input

Run with:
    pytest test_counterfactual.py

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""
import sys

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from model_explain.explainers.counterfactual import generate_counterfactual


@pytest.fixture
def sample_data():
    """
    Provides a sample dataset and instance for testing.

    Returns:
        tuple: A tuple of (DataFrame, DataFrame) for dataset and single-row instance.
    """
    df = pd.DataFrame(
        {
            "age": [25, 30],
            "income": [50000, 60000],
            "gender": ["male", "female"],
            "label": [0, 1],
        }
    )
    instance = df.drop(columns=["label"]).iloc[[0]]
    return df, instance


@patch("model_explain.explainers.counterfactual.dice_ml.Data")
@patch("model_explain.explainers.counterfactual.dice_ml.Model")
@patch("model_explain.explainers.counterfactual.dice_ml.Dice")
def test_generate_counterfactual_success(mock_dice, mock_model, mock_data, sample_data):
    """
    Test that generate_counterfactual successfully returns a non-empty DataFrame.
    """
    df, instance = sample_data

    mock_explainer = MagicMock()
    mock_cf = MagicMock()
    mock_cf.visualize_as_dataframe.return_value = pd.DataFrame(
        {"age": [28], "income": [52000], "gender": ["male"]}
    )

    mock_dice.return_value = mock_explainer
    mock_model.return_value = MagicMock()
    mock_explainer.generate_counterfactuals.return_value = mock_cf

    result = generate_counterfactual(
        model=MagicMock(),
        data=df,
        instance=instance,
        features_to_vary=["age", "income"],
    )

    assert isinstance(result, pd.DataFrame)
    assert not result.empty


@patch("model_explain.explainers.counterfactual.dice_ml.Data")
@patch("model_explain.explainers.counterfactual.dice_ml.Model")
@patch("model_explain.explainers.counterfactual.dice_ml.Dice")
def test_generate_counterfactual_output_shape(
    mock_dice, mock_model, mock_data, sample_data
):
    """
    Test that the output DataFrame has the correct shape (1 row, expected columns).
    """
    df, instance = sample_data

    mock_explainer = MagicMock()
    mock_cf = MagicMock()
    mock_cf.visualize_as_dataframe.return_value = pd.DataFrame(
        {"age": [28], "income": [52000], "gender": ["male"]}
    )

    mock_dice.return_value = mock_explainer
    mock_model.return_value = MagicMock()
    mock_explainer.generate_counterfactuals.return_value = mock_cf

    result = generate_counterfactual(
        model=MagicMock(),
        data=df,
        instance=instance,
        features_to_vary=["age", "income"],
    )

    assert result.shape == (1, 3), "Unexpected counterfactual output shape."


@patch("model_explain.explainers.counterfactual.dice_ml.Data")
@patch("model_explain.explainers.counterfactual.dice_ml.Model")
def test_counterfactual_explainer_invalid_model(mock_model, mock_data, sample_data):
    """
    Test that an invalid model input raises a ValueError.
    """
    df, instance = sample_data
    mock_model.side_effect = ValueError("Invalid model")

    with pytest.raises(ValueError, match="Invalid model"):
        generate_counterfactual(
            model="invalid_model_object",
            data=df,
            instance=instance,
            features_to_vary=["age", "income"],
        )


def test_generate_counterfactual_invalid_input():
    """
    Test that completely invalid input raises a general exception.
    """
    with pytest.raises(Exception):
        generate_counterfactual(
            model=None, data=None, instance=None, features_to_vary=None
        )


def main():
    """
    Run all tests in this module using pytest.
    """
    sys.exit(pytest.main([__file__]))


if __name__ == "__main__":
    main()
