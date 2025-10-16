"""
Command-line interface for the Model Explainability Toolkit.

Provides functionalities to compute explainability scores, generate natural language summaries,
compare models, generate counterfactual explanations, and assess fairness.

Author: Vaibhav Kulshrestha
"""

# Import necessary libraries
import argparse

import numpy as np
import pandas as pd

from examples import run_sandbox
from model_explain.explainers import generate_summary, compare_models
from model_explain.utils import compute_explainability_score, load_model


def load_data(path):
    """
    Load dataset from a CSV file.
    :param path: Path to the CSV file.
    :type path: str
    :return: DataFrame containing the dataset.
    :rtype: pd.DataFrame
    """
    return pd.read_csv(path)


def main():
    """
    Main function to parse arguments and execute commands.
    """
    parser = argparse.ArgumentParser(description="Model Explainability Toolkit CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Explainability Score
    score_parser = subparsers.add_parser("score", help="Compute explainability score")
    score_parser.add_argument("--model", required=True, help="Path to saved model file")
    score_parser.add_argument("--data", required=True, help="Path to dataset CSV")

    # Natural Language Summary
    summary_parser = subparsers.add_parser(
        "summary", help="Generate natural language summary"
    )
    summary_parser.add_argument("--data", required=True, help="Path to dataset CSV")
    summary_parser.add_argument(
        "--shap", required=True, help="Path to SHAP values .npy file"
    )
    summary_parser.add_argument(
        "--instance", type=int, default=0, help="Index of instance to explain"
    )
    summary_parser.add_argument(
        "--prediction", type=int, required=True, help="Predicted class index"
    )
    summary_parser.add_argument(
        "--classes", nargs="+", required=True, help="List of class names"
    )

    # Model Comparison
    compare_parser = subparsers.add_parser("compare", help="Compare models")
    compare_parser.add_argument(
        "--models", nargs="+", required=True, help="List of model paths"
    )
    compare_parser.add_argument("--data", required=True, help="Path to dataset CSV")

    # Counterfactual Explanations
    cf_parser = subparsers.add_parser(
        "counterfactual", help="Generate counterfactual explanation"
    )
    cf_parser.add_argument("--model", required=True)
    cf_parser.add_argument("--data", required=True)
    cf_parser.add_argument("--instance", type=int, default=0)

    # Fairness Assessment
    fair_parser = subparsers.add_parser("audit", help="Run fairness audit")
    fair_parser.add_argument("--data", required=True)
    fair_parser.add_argument("--predictions", required=True)
    fair_parser.add_argument("--sensitive", required=True)

    # Sandbox GUI
    subparsers.add_parser("sandbox", help="Launch explainability sandbox GUI")

    args = parser.parse_args()

    if args.command == "score":
        model = load_model(args.model)
        data = load_data(args.data)
        score = compute_explainability_score(model, data)
        print(f"Explainability Score: {score}/100")

    elif args.command == "summary":
        data = load_data(args.data)
        shap_values = np.load(args.shap)
        instance = data.iloc[args.instance]
        summary = generate_summary(
            instance,
            shap_values[args.instance],
            data.columns,
            args.prediction,
            args.classes,
        )
        print("🗣️ Summary:")
        print(summary)

    elif args.command == "compare":
        data = load_data(args.data)
        models = {f"Model{i+1}": load_model(path) for i, path in enumerate(args.models)}
        comparison = compare_models(models, data)
        print("⚖️ Top Features by Model:")
        for name, features in comparison.items():
            print(f"{name}: {features}")

    elif args.command == "sandbox":
        run_sandbox()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
