
import json
from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

DATA_FILE = "synthetic_ml_training_data.csv"
MODEL_FILE = "supplyshield_delivery_model.joblib"
METADATA_FILE = "supplyshield_model_metadata.json"

features = [
    "supplier_id",
    "supplier_region",
    "supplier_category",
    "product_id",
    "product_category",
    "quantity",
    "unit_cost",
    "planned_lead_days",
]

categorical = [
    "supplier_id",
    "supplier_region",
    "supplier_category",
    "product_id",
    "product_category",
]

numeric = ["quantity", "unit_cost", "planned_lead_days"]

df = pd.read_csv(DATA_FILE)

if not (df["data_source"] == "SYNTHETIC").all():
    raise ValueError("Expected synthetic data only.")

if df[features + ["was_late"]].isna().any().any():
    raise ValueError("Missing values found.")

X = df[features]
y = df["was_late"].astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

preprocessor = ColumnTransformer([
    (
        "categorical",
        OneHotEncoder(handle_unknown="ignore"),
        categorical,
    ),
    ("numeric", "passthrough", numeric),
])

model = Pipeline([
    ("preprocessing", preprocessor),
    (
        "classifier",
        RandomForestClassifier(
            n_estimators=200,
            max_depth=4,
            min_samples_leaf=10,
            max_features="sqrt",
            class_weight="balanced",
            random_state=42,
        ),
    ),
])

model.fit(X_train, y_train)

joblib.dump(model, MODEL_FILE)

metadata = {
    "project": "SupplyShield",
    "model_type": "Regularized Random Forest",
    "target": "was_late",
    "training_rows": int(len(X_train)),
    "test_rows": int(len(X_test)),
    "features": features,
    "data_source": "SYNTHETIC",
    "status": "Prototype only",
    "limitation": (
        "Model trained on simulated labels. "
        "Real-world predictive performance is not established."
    ),
}

Path(METADATA_FILE).write_text(
    json.dumps(metadata, indent=4),
    encoding="utf-8",
)

print("SUPPLYSHIELD — MODEL ARTIFACT SAVED")
print(f"Model: {MODEL_FILE}")
print(f"Metadata: {METADATA_FILE}")
print(f"Training rows: {len(X_train)}")
print(f"Test rows reserved: {len(X_test)}")
print("Status: Synthetic-data prototype; not production validated.")
