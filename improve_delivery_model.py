
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

DATA_FILE = "synthetic_ml_training_data.csv"

df = pd.read_csv(DATA_FILE)

if not (df["data_source"] == "SYNTHETIC").all():
    raise ValueError("Expected synthetic demonstration data only.")

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

X = df[features]
y = df["was_late"].astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
])

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

preprocessor = ColumnTransformer([
    ("categorical", categorical_pipeline, categorical),
    ("numeric", numeric_pipeline, numeric),
])

models = {
    "Logistic Regression": LogisticRegression(
        max_iter=2000,
        C=0.1,
        class_weight="balanced",
        random_state=42,
    ),
    "Regularized Random Forest": RandomForestClassifier(
        n_estimators=200,
        max_depth=4,
        min_samples_leaf=10,
        max_features="sqrt",
        class_weight="balanced",
        random_state=42,
    ),
}

results = []

for name, classifier in models.items():
    model = Pipeline([
        ("preprocessing", preprocessor),
        ("classifier", classifier),
    ])

    model.fit(X_train, y_train)

    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    test_prob = model.predict_proba(X_test)[:, 1]

    results.append({
        "model": name,
        "train_accuracy": accuracy_score(y_train, train_pred),
        "test_accuracy": accuracy_score(y_test, test_pred),
        "test_precision_late": precision_score(
            y_test, test_pred, zero_division=0
        ),
        "test_recall_late": recall_score(
            y_test, test_pred, zero_division=0
        ),
        "test_f1_late": f1_score(
            y_test, test_pred, zero_division=0
        ),
        "test_roc_auc": roc_auc_score(y_test, test_prob),
    })

comparison = pd.DataFrame(results)
comparison.to_csv("improved_model_comparison.csv", index=False)

print("\nSUPPLYSHIELD — MODEL IMPROVEMENT COMPARISON")
print("=" * 70)
print(comparison.round(3).to_string(index=False))
print("\nSaved: improved_model_comparison.csv")
print(
    "\nThese are comparisons on synthetic data, not evidence of "
    "real-world predictive accuracy."
)
