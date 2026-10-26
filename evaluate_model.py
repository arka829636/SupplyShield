
import pandas as pd
import joblib

from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.base import clone

# ============================================================
# SUPPLYSHIELD — MODEL EVALUATION AND BASELINE COMPARISON
# Synthetic data only: results are not real-world evidence.
# ============================================================

DATA_FILE = "synthetic_ml_training_data.csv"
MODEL_FILE = "delivery_delay_model.joblib"

TARGET = "was_late"

FEATURES = [
    "supplier_id",
    "supplier_region",
    "supplier_category",
    "product_id",
    "product_category",
    "quantity",
    "unit_cost",
    "planned_lead_days",
]

def calculate_metrics(y_true, predictions, probabilities=None):
    results = {
        "Accuracy": accuracy_score(y_true, predictions),
        "Precision (late)": precision_score(
            y_true, predictions, zero_division=0
        ),
        "Recall (late)": recall_score(
            y_true, predictions, zero_division=0
        ),
        "F1 (late)": f1_score(
            y_true, predictions, zero_division=0
        ),
    }

    if probabilities is not None and y_true.nunique() == 2:
        results["ROC-AUC"] = roc_auc_score(y_true, probabilities)

    return results


def print_metrics(title, metrics):
    print(f"\n{title}")
    print("-" * 58)
    for name, value in metrics.items():
        print(f"{name:<22}: {value:.3f}")


def main():
    df = pd.read_csv(DATA_FILE)

    if not (df["data_source"] == "SYNTHETIC").all():
        raise ValueError("This evaluation expects synthetic data only.")

    X = df[FEATURES]
    y = df[TARGET].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    # Load the previously trained pipeline.
    model = joblib.load(MODEL_FILE)

    # Check that the saved model's test metrics can be reproduced.
    saved_model_predictions = model.predict(X_test)
    saved_model_probabilities = model.predict_proba(X_test)[:, 1]

    model_test_metrics = calculate_metrics(
        y_test,
        saved_model_predictions,
        saved_model_probabilities,
    )

    print("=" * 58)
    print("SUPPLYSHIELD — MODEL EVALUATION")
    print("=" * 58)
    print(f"Training rows: {len(X_train)}")
    print(f"Testing rows:  {len(X_test)}")
    print("Dataset: synthetic demonstration data")

    # Train a fresh copy on this exact training split.
    # This allows us to compare training and test performance.
    fresh_model = clone(model)
    fresh_model.fit(X_train, y_train)

    train_predictions = fresh_model.predict(X_train)
    train_probabilities = fresh_model.predict_proba(X_train)[:, 1]

    test_predictions = fresh_model.predict(X_test)
    test_probabilities = fresh_model.predict_proba(X_test)[:, 1]

    train_metrics = calculate_metrics(
        y_train, train_predictions, train_probabilities
    )
    test_metrics = calculate_metrics(
        y_test, test_predictions, test_probabilities
    )

    print_metrics("Random Forest — training performance", train_metrics)
    print_metrics("Random Forest — test performance", test_metrics)

    # Majority-class baseline.
    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(X_train, y_train)

    baseline_predictions = baseline.predict(X_test)

    baseline_metrics = calculate_metrics(
        y_test, baseline_predictions
    )

    print_metrics("Majority-class baseline — test performance", baseline_metrics)

    # Save comparison for future review.
    comparison = pd.DataFrame([
        {"Model": "Random Forest (test)", **test_metrics},
        {"Model": "Majority baseline (test)", **baseline_metrics},
    ])

    comparison.to_csv("model_evaluation_comparison.csv", index=False)

    print("\nComparison saved to: model_evaluation_comparison.csv")

    print("\nInterpretation:")
    if test_metrics["F1 (late)"] > baseline_metrics["F1 (late)"]:
        print("- Random Forest has a higher late-order F1-score than the baseline.")
    else:
        print("- Random Forest does not improve on the baseline late-order F1-score.")

    gap = train_metrics["Accuracy"] - test_metrics["Accuracy"]
    print(f"- Training minus test accuracy: {gap:.3f}")

    if gap > 0.15:
        print("- The accuracy gap is substantial; investigate possible overfitting.")
    else:
        print("- No large accuracy gap by this simple check.")

    print(
        "\nIMPORTANT: These results use synthetic labels created by simulation "
        "rules. They do not establish real-world predictive performance."
    )


if __name__ == "__main__":
    main()
