
import joblib
import pandas as pd

MODEL_FILE = "supplyshield_delivery_model.joblib"

model = joblib.load(MODEL_FILE)

# Illustrative sample order.
# All values must match the model's expected feature columns.
sample_order = pd.DataFrame([{
    "supplier_id": "S003",
    "supplier_region": "West",
    "supplier_category": "Electronics",
    "product_id": "P003",
    "product_category": "Electronics",
    "quantity": 120,
    "unit_cost": 480.00,
    "planned_lead_days": 8,
}])

prediction = int(model.predict(sample_order)[0])
probability = float(model.predict_proba(sample_order)[0][1])

print("=" * 55)
print("SUPPLYSHIELD — DELIVERY DELAY PREDICTION")
print("=" * 55)
print("\nSample order:")
print(sample_order.to_string(index=False))

print("\nModel output:")
print(f"Predicted outcome: {'LATE' if prediction == 1 else 'ON TIME'}")
print(f"Estimated late probability: {probability:.1%}")

print(
    "\nIMPORTANT: This is a synthetic-data prototype. "
    "The probability is not a calibrated real-world risk estimate."
)
