# Model Explainability Toolkit
[![Downloads](https://pepy.tech/badge/model-explain)](https://pepy.tech/project/model-explain)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/model-explain.svg)](https://badge.fury.io/py/model-explain)

This toolkit provides SHAP and LIME-based explanations for scikit-learn models, along with visualization tools.

## Features
- SHAP and LIME explainers
- Feature importance plots
- Modular design for easy extension

## Installation
Install via pip:
```bash
pip install model-explain
```

## API Reference

`shap_explainer.shap_explainer(model, X)`

Generates SHAP explanations for a fitted scikit-learn model.
- `model`: Trained scikit-learn estimator
- `X`: DataFrame of input features

`lime_explainer.lime_explainer(model, X)`

Generates LIME explanations for a fitted scikit-learn model.
- `model`: Trained scikit-learn estimator
- `X`: DataFrame of input features

## Example
```python
from model_explain.explainers import shap_explainer
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
import pandas as pd
# Load data
data = load_iris()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(data.target)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
# Train model
my_model = RandomForestClassifier()
my_model.fit(X_train, y_train)
# Explain model
shap_explainer.shap_explainer(my_model, X_test)
```

## Usage
See `examples/demo_notebook.ipynb` for a walkthrough.

## Support
For questions or issues, open an issue on GitHub or email the maintainer.