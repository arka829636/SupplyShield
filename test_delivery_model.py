
import joblib
import pandas as pd

MODEL_FILE = "supplyshield_delivery_model.joblib"

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

def main():
    model = joblib.load(MODEL_FILE)
    print("PASS | Model loaded")

    sample = {
        "supplier_id": "S003",
        "supplier_region": "West",
        "supplier_category": "Electronics",
        "product_id": "P003",
        "product_category": "Electronics",
        "quantity": 120,
        "unit_cost": 480.00,
        "planned_lead_days": 8,
    }

    # Test a single order.
    one_order = pd.DataFrame([sample], columns=FEATURES)
    prediction = model.predict(one_order)
    probability = model.predict_proba(one_order)[:, 1]

    assert len(prediction) == 1
    assert int(prediction[0]) in (0, 1)
    assert 0.0 <= float(probability[0]) <= 1.0
    print("PASS | Single-order prediction")

    # Test multiple orders.
    two_orders = pd.DataFrame(
        [sample, {**sample, "supplier_id": "S001"}],
        columns=FEATURES,
    )
    batch_predictions = model.predict(two_orders)
    assert len(batch_predictions) == 2
    print("PASS | Batch prediction")

    # Test input validation.
    invalid_order = one_order.drop(columns=["quantity"])
    try:
        model.predict(invalid_order)
    except (ValueError, KeyError):
        print("PASS | Missing feature rejected")
    else:
        raise AssertionError("Model accepted missing required input.")

    print("\nAll prediction interface checks passed.")
    print("Note: interface checks do not prove predictive accuracy.")

if __name__ == "__main__":
    main()
