
import pandas as pd

FILE = "supplyshield_batch_predictions.csv"

REQUIRED_COLUMNS = [
    "order_id",
    "supplier_id",
    "product_id",
    "predicted_was_late",
    "predicted_late_probability",
    "predicted_outcome",
    "data_source",
]

def main():
    df = pd.read_csv(FILE)

    checks = {
        "Exactly 3 demo orders": len(df) == 3,
        "Unique order IDs": df["order_id"].is_unique,
        "Required columns exist": set(REQUIRED_COLUMNS).issubset(df.columns),
        "Predictions are 0 or 1": df["predicted_was_late"].isin([0, 1]).all(),
        "Probabilities between 0 and 1": (
            df["predicted_late_probability"].between(0, 1).all()
        ),
        "No missing values in required columns": (
            not df[REQUIRED_COLUMNS].isna().any().any()
        ),
        "All rows marked as synthetic demo": (
            (df["data_source"] == "SYNTHETIC_DEMO").all()
        ),
    }

    print("\nSUPPLYSHIELD — BATCH PREDICTION VALIDATION")
    print("=" * 60)

    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} | {name}")

    if all(checks.values()):
        print("\nAll batch prediction checks passed.")
    else:
        print("\nValidation failed. Fix the reported checks.")

if __name__ == "__main__":
    main()
