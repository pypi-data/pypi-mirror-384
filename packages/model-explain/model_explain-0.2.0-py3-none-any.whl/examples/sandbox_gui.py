"""
A simple Streamlit app to upload a dataset, train a model, and visualize explanations using SHAP and LIME.
"""

# Import necessary libraries
import streamlit as st
import shap
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from lime.lime_tabular import LimeTabularExplainer


def run_sandbox():
    """
    A simple Streamlit app to upload a dataset, train a model, and visualize explanations using SHAP and LIME.
    :return: None: The function runs a Streamlit app.
    """
    st.title("🧪 Explainability Sandbox")
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    if uploaded_file:
        data = pd.read_csv(uploaded_file)
        target = st.selectbox("Select target column", data.columns)
        X = data.drop(columns=[target])
        y = data[target]

        model = RandomForestClassifier().fit(X, y)
        st.success("Model trained!")

        instance_idx = st.slider("Select instance to explain", 0, len(X) - 1, 0)
        instance = X.iloc[instance_idx]

        explainer = shap.Explainer(model, X)
        shap_values = explainer(X)
        st.subheader("SHAP Summary Plot")
        shap.plots.waterfall(shap_values[instance_idx])

        lime_exp = LimeTabularExplainer(
            X.values,
            feature_names=X.columns.tolist(),
            class_names=list(map(str, set(y))),
            mode="classification",
        )
        explanation = lime_exp.explain_instance(instance.values, model.predict_proba)
        st.subheader("LIME Explanation")
        st.components.v1.html(explanation.as_html(), height=600)
