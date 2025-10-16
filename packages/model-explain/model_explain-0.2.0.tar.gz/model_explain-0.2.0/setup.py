"""
Setup script for the model_explain package.

Author:
    Vaibhav Kulshrestha

Date:
    2025-10-15
"""

# Import necessary modules
from setuptools import setup, find_packages

setup(
    name="model_explain",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "plotly",
        "fairlearn",
        "dice-ml",
        "numpy",
        "pandas",
        "scikit-learn",
        "shap",
        "lime",
        "streamlit",
        "xgboost",
        "joblib",
        "matplotlib",
        "seaborn",
    ],
    entry_points={"console_scripts": ["explain-cli=model_explain.cli:main"]},
    author="Vaibhav Kulshrestha",
    author_email="vaibhav1kulshrestha@gmail.com",
    description="A model explainability toolkit with SHAP, LIME, scoring, summaries, and GUI sandbox",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
)
