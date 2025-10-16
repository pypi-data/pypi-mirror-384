# model_explain/explainers/counterfactual.py

"""
This module provides functionality to generate counterfactual explanations
for machine learning models using the DiCE library.

Features:
- Generate counterfactuals for a given instance.
- Customize features to vary in the counterfactual generation process.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

# Import necessary libraries
import dice_ml


def generate_counterfactual(model, data, instance, features_to_vary=None):
    """
    Generate counterfactual explanations for a given instance using DiCE.
    1. Initialize DiCE data and model objects.
    2. Create a DiCE explainer.
    3. Generate counterfactuals for the specified instance.
    4. Return the counterfactuals as a DataFrame.
    :param model: The machine learning model to explain.
    :type model: Any
    :param data: The dataset used for generating counterfactuals.
    :type data: pd.DataFrame
    :param instance: The instance for which to generate counterfactuals.
    :type instance: pd.DataFrame
    :param features_to_vary: List of features that can be changed in the counterfactuals.
    :type features_to_vary: List[str], optional
    :return: pd.DataFrame: DataFrame containing the generated counterfactuals.
    """
    dice_data = dice_ml.Data(
        dataframe=data,
        continuous_features=features_to_vary,
    )
    dice_model = dice_ml.Model(model=model, backend="sklearn")
    explainer = dice_ml.Dice(dice_data, dice_model)
    cf = explainer.generate_counterfactuals(
        instance, total_CFs=1, desired_class="opposite"
    )
    return cf.visualize_as_dataframe()
