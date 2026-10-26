
import pandas as pd
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
import matplotlib.pyplot as plt

# ============================================================
# SUPPLYSHIELD — BASELINE DELIVERY DELAY MODEL
# Training data: synthetic demonstration records only.
# ============================================================

DATA_FILE = "synthetic_ml_training_data.csv"
MODEL_FILE = "delivery_delay_model.joblib"
PREDICTIONS_FILE = "delivery_model_test_predictions.csv"
MATRIX_FILE = "delivery_model_confusion_matrix.png"

TARGET = "was_late"

# ------------------------------------------------------------
# 1. Load and check the dataset
# ------------------------------------------------------------
df = pd.read_csv(DATA_FILE)

required_columns = [
    "order_id",
    "supplier_id",
    "supplier_region",
    "supplier_category",
    "product_id",
    "product_category",
    "quantity",
    "unit_cost",
    "planned_lead_days",
    "was_late",
    "data_source",
]

missing_columns = set(required_columns) - set(df.columns)

if missing_columns:
    raise ValueError(f"Missing columns: {sorted(missing_columns)}")

if not (df["data_source"] == "SYNTHETIC").all():
    raise ValueError("Expected synthetic training data only.")

if df[TARGET].isna().any():
    raise ValueError("Target column contains missing values.")

if df[TARGET].nunique() != 2:
    raise ValueError("Training requires both on-time and late examples.")

print("=" * 65)
print("SUPPLYSHIELD — DELIVERY DELAY MODEL")
print("=" * 65)
print(f"Dataset rows: {len(df)}")
print("Data source: SYNTHETIC")

# ------------------------------------------------------------
# 2. Select features and target
# Do not use actual delivery date or post-delivery information.
# ------------------------------------------------------------
feature_columns = [
    "supplier_id",
    "supplier_region",
    "supplier_category",
    "product_id",
    "product_category",
    "quantity",
    "unit_cost",
    "planned_lead_days",
]

X = df[feature_columns].copy()
y = df[TARGET].astype(int)

categorical_features = [
    "supplier_id",
    "supplier_region",
    "supplier_category",
    "product_id",
    "product_category",
]

numeric_features = [
    "quantity",
    "unit_cost",
    "planned_lead_days",
]

# ------------------------------------------------------------
# 3. Split data before training
# Stratification preserves the target ratio in both sets.
# ------------------------------------------------------------
X_train, X_test, y_train, y_test, id_train, id_test = (
    train_test_split(
        X,
        y,
        df["order_id"],
        test_size=0.20,
        random_state=42,
        stratify=y,
    )
)

print(f"\nTraining rows: {len(X_train)}")
print(f"Testing rows: {len(X_test)}")

# ------------------------------------------------------------
# 4. Preprocess categorical features and train the model
# ------------------------------------------------------------
preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features,
        ),
        ("numeric", "passthrough", numeric_features),
    ]
)

pipeline = Pipeline(
    steps=[
        ("preprocessing", preprocessor),
        (
            "classifier",
            RandomForestClassifier(
                n_estimators=200,
                max_depth=8,
                min_samples_leaf=3,
                class_weight="balanced",
                random_state=42,
            ),
        ),
    ]
)

pipeline.fit(X_train, y_train)

# ------------------------------------------------------------
# 5. Evaluate on the held-out test set
# ------------------------------------------------------------
predictions = pipeline.predict(X_test)
probabilities = pipeline.predict_proba(X_test)[:, 1]

accuracy = accuracy_score(y_test, predictions)
auc = roc_auc_score(y_test, probabilities)

print("\nEvaluation on held-out synthetic test data")
print("-" * 65)
print(f"Accuracy: {accuracy:.3f}")
print(f"ROC-AUC:  {auc:.3f}")

print("\nClassification report:")
print(
    classification_report(
        y_test,
        predictions,
        labels=[0, 1],
        target_names=["On time", "Late"],
        zero_division=0,
    )
)

matrix = confusion_matrix(y_test, predictions, labels=[0, 1])
print("Confusion matrix (rows = actual, columns = predicted):")
print(matrix)

# ------------------------------------------------------------
# 6. Save test predictions
# ------------------------------------------------------------
test_results = pd.DataFrame({
    "order_id": id_test.to_numpy(),
    "actual_was_late": y_test.to_numpy(),
    "predicted_was_late": predictions,
    "predicted_late_probability": probabilities.round(4),
})

test_results.to_csv(PREDICTIONS_FILE, index=False)

# ------------------------------------------------------------
# 7. Save confusion matrix image
# ------------------------------------------------------------
display = ConfusionMatrixDisplay(
    confusion_matrix=matrix,
    display_labels=["On time", "Late"],
)

display.plot(values_format="d")
plt.title("SupplyShield — Synthetic Test Confusion Matrix")
plt.tight_layout()
plt.savefig(MATRIX_FILE, dpi=150)
plt.close()

# ------------------------------------------------------------
# 8. Save trained pipeline
# ------------------------------------------------------------
joblib.dump(pipeline, MODEL_FILE)

print("\nSaved files:")
print(f"1. Model pipeline: {MODEL_FILE}")
print(f"2. Test predictions: {PREDICTIONS_FILE}")
print(f"3. Confusion matrix: {MATRIX_FILE}")

print(
    "\nIMPORTANT: These results measure performance on simulated data. "
    "They do not establish real-world predictive accuracy."
)
