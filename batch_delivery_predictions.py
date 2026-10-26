
import joblib
import pandas as pd

MODEL_FILE = "supplyshield_delivery_model.joblib"
OUTPUT_FILE = "supplyshield_batch_predictions.csv"

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

# Illustrative orders for demonstrating batch predictions.
# These are not actual purchase orders.
sample_orders = [
    {
        "order_id": "DEMO001",
        "supplier_id": "S003",
        "supplier_region": "West",
        "supplier_category": "Electronics",
        "product_id": "P003",
        "product_category": "Electronics",
        "quantity": 120,
        "unit_cost": 480.00,
        "planned_lead_days": 8,
    },
    {
        "order_id": "DEMO002",
        "supplier_id": "S002",
        "supplier_region": "South",
        "supplier_category": "Raw Materials",
        "product_id": "P002",
        "product_category": "Raw Materials",
        "quantity": 400,
        "unit_cost": 650.00,
        "planned_lead_days": 10,
    },
    {
        "order_id": "DEMO003",
        "supplier_id": "S004",
        "supplier_region": "North",
        "supplier_category": "Packaging",
        "product_id": "P004",
        "product_category": "Packaging",
        "quantity": 1800,
        "unit_cost": 35.00,
        "planned_lead_days": 4,
    },
]

def main():
    model = joblib.load(MODEL_FILE)

    df = pd.DataFrame(sample_orders)
    predictions_input = df[FEATURES]

    predicted_class = model.predict(predictions_input)
    late_probability = model.predict_proba(predictions_input)[:, 1]

    df["predicted_was_late"] = predicted_class.astype(int)
    df["predicted_late_probability"] = late_probability.round(4)
    df["predicted_outcome"] = df["predicted_was_late"].map({
        0: "Predicted On Time",
        1: "Predicted Late",
    })
    df["data_source"] = "SYNTHETIC_DEMO"

    df.to_csv(OUTPUT_FILE, index=False)

    print("=" * 65)
    print("SUPPLYSHIELD — BATCH DELIVERY PREDICTIONS")
    print("=" * 65)
    print(
        df[
            [
                "order_id",
                "supplier_id",
                "product_id",
                "predicted_outcome",
                "predicted_late_probability",
            ]
        ].to_string(index=False)
    )

    print(f"\nSaved to: {OUTPUT_FILE}")
    print("All records are illustrative demo orders, not real orders.")

if __name__ == "__main__":
    main()
