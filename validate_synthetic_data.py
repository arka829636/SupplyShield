
import pandas as pd

FILE = "synthetic_ml_training_data.csv"

def main():
    df = pd.read_csv(FILE)

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["expected_delivery_date"] = pd.to_datetime(
        df["expected_delivery_date"], errors="coerce"
    )

    checks = {
        "Expected row count (500)": len(df) == 500,
        "Unique order IDs": df["order_id"].is_unique,
        "No missing values": not df.isna().any().any(),
        "Valid target values (0 or 1)": set(df["was_late"].unique()) <= {0, 1},
        "Expected date after order date": (
            df["expected_delivery_date"] > df["order_date"]
        ).all(),
        "Positive planned lead times": (df["planned_lead_days"] > 0).all(),
        "Date difference matches lead time": (
            (
                df["expected_delivery_date"] - df["order_date"]
            ).dt.days == df["planned_lead_days"]
        ).all(),
        "All rows labelled synthetic": (df["data_source"] == "SYNTHETIC").all(),
    }

    print("\nSUPPLYSHIELD — SYNTHETIC DATA VALIDATION")
    print("=" * 55)

    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} | {name}")

    print("\nSupplier and product category combinations:")
    print(
        pd.crosstab(df["supplier_category"], df["product_category"])
        .to_string()
    )

    print("\nDelivery outcome counts:")
    print(df["was_late"].value_counts().sort_index().to_string())

    if all(checks.values()):
        print("\nAll basic validation checks passed.")
        print("Review category combinations before model training.")
    else:
        print("\nSome checks failed. Fix the data before model training.")

if __name__ == "__main__":
    main()
