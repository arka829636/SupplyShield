
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

connection_url = URL.create(
    drivername="mysql+mysqlconnector",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME", "supplyshield"),
)

engine = create_engine(connection_url)

query = """
SELECT
    po.order_id,
    po.order_date,
    po.expected_delivery_date,
    po.quantity,
    po.unit_cost,
    s.supplier_id,
    s.supplier_region,
    s.supplier_category,
    p.product_id,
    p.category AS product_category,
    DATEDIFF(
        po.expected_delivery_date,
        po.order_date
    ) AS planned_lead_days,
    CASE
        WHEN po.actual_delivery_date IS NULL THEN NULL
        WHEN po.actual_delivery_date > po.expected_delivery_date THEN 1
        ELSE 0
    END AS was_late
FROM purchase_orders AS po
JOIN suppliers AS s
    ON po.supplier_id = s.supplier_id
JOIN products AS p
    ON po.product_id = p.product_id
WHERE po.order_date IS NOT NULL
  AND po.expected_delivery_date IS NOT NULL
ORDER BY po.order_date, po.order_id;
"""


def main():
    try:
        with engine.connect() as connection:
            df = pd.read_sql(text(query), connection)

        # Convert date columns to proper date types.
        df["order_date"] = pd.to_datetime(df["order_date"])
        df["expected_delivery_date"] = pd.to_datetime(
            df["expected_delivery_date"]
        )

        # Save the prepared dataset.
        output_file = "supplyshield_ml_dataset.csv"
        df.to_csv(output_file, index=False)

        print("\n" + "=" * 70)
        print("SUPPLYSHIELD — ML DATASET PREPARATION")
        print("=" * 70)

        print(f"Rows: {len(df)}")
        print(f"Columns: {len(df.columns)}")

        print("\nTarget distribution:")
        print(
            df["was_late"]
            .value_counts(dropna=False)
            .sort_index()
            .rename(index={0: "On time", 1: "Late", float("nan"): "Unknown"})
            .to_string()
        )

        print("\nDataset preview:")
        print(df.head(10).to_string(index=False))

        print("\nMissing values by column:")
        missing = df.isna().sum()
        print(missing[missing > 0].to_string() if missing.any() else "None")

        print(f"\nDataset saved to: {output_file}")
        print(
            "\nImportant: this is a preparation dataset, not a trained "
            "prediction model. The current sample is too small for "
            "reliable model evaluation."
        )

    except Exception as error:
        print(f"ML dataset preparation failed: {error}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
