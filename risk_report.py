
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# --------------------------------------------------
# 1. Load database settings
# --------------------------------------------------
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

# --------------------------------------------------
# 2. Supplier delivery and risk analysis
# --------------------------------------------------
supplier_query = """
SELECT
    s.supplier_id,
    s.supplier_name,
    COUNT(po.order_id) AS total_orders,

    SUM(
        CASE
            WHEN po.order_id IS NOT NULL
             AND po.actual_delivery_date <= po.expected_delivery_date
            THEN 1 ELSE 0
        END
    ) AS on_time_orders,

    SUM(
        CASE
            WHEN po.actual_delivery_date > po.expected_delivery_date
            THEN 1 ELSE 0
        END
    ) AS late_orders,

    ROUND(
        100.0 * SUM(
            CASE
                WHEN po.order_id IS NOT NULL
                 AND po.actual_delivery_date <= po.expected_delivery_date
                THEN 1 ELSE 0
            END
        ) / NULLIF(COUNT(po.order_id), 0),
        2
    ) AS on_time_delivery_pct,

    ROUND(
        AVG(
            CASE
                WHEN po.actual_delivery_date > po.expected_delivery_date
                THEN DATEDIFF(
                    po.actual_delivery_date,
                    po.expected_delivery_date
                )
                ELSE NULL
            END
        ),
        2
    ) AS average_delay_days

FROM suppliers AS s
LEFT JOIN purchase_orders AS po
    ON s.supplier_id = po.supplier_id
GROUP BY s.supplier_id, s.supplier_name
ORDER BY s.supplier_name;
"""

# --------------------------------------------------
# 3. Inventory risk analysis
# --------------------------------------------------
inventory_query = """
SELECT
    p.product_id,
    p.product_name,
    p.category,
    i.stock_on_hand,
    i.average_daily_demand,
    i.reorder_point,

    ROUND(
        i.stock_on_hand / NULLIF(i.average_daily_demand, 0),
        2
    ) AS stock_cover_days,

    CASE
        WHEN i.average_daily_demand IS NULL
          OR i.average_daily_demand <= 0
            THEN 'CHECK DEMAND'
        WHEN i.stock_on_hand / i.average_daily_demand < 7
            THEN 'LOW COVER'
        WHEN i.stock_on_hand <= i.reorder_point
            THEN 'REORDER'
        ELSE 'OK'
    END AS inventory_status

FROM inventory AS i
JOIN products AS p
    ON p.product_id = i.product_id
ORDER BY stock_cover_days ASC;
"""


def main():
    try:
        # Read the database; do not modify source tables.
        with engine.connect() as connection:
            suppliers = pd.read_sql(
                text(supplier_query), connection
            )
            inventory = pd.read_sql(
                text(inventory_query), connection
            )

        # Calculate supplier risk indicators.
        suppliers["late_delivery_pct"] = (
            100 - suppliers["on_time_delivery_pct"].fillna(0)
        ).round(2)

        def classify_supplier(row):
            if row["total_orders"] < 3:
                return "LIMITED DATA"
            if row["late_delivery_pct"] >= 50:
                return "HIGH RISK"
            if row["late_delivery_pct"] >= 25:
                return "MEDIUM RISK"
            return "LOW RISK"

        suppliers["supplier_risk"] = suppliers.apply(
            classify_supplier, axis=1
        )

        # Calculate executive summary values.
        total_suppliers = len(suppliers)
        total_orders = int(suppliers["total_orders"].sum())
        late_orders = int(suppliers["late_orders"].sum())
        on_time_orders = int(suppliers["on_time_orders"].sum())

        on_time_pct = (
            round(100 * on_time_orders / total_orders, 2)
            if total_orders else 0
        )

        high_risk_suppliers = int(
            (suppliers["supplier_risk"] == "HIGH RISK").sum()
        )
        low_cover_products = int(
            (inventory["inventory_status"] == "LOW COVER").sum()
        )
        reorder_products = int(
            (inventory["inventory_status"] == "REORDER").sum()
        )

        summary = pd.DataFrame([
            {"metric": "Total Suppliers",
             "value": total_suppliers},
            {"metric": "Total Purchase Orders",
             "value": total_orders},
            {"metric": "Late Orders",
             "value": late_orders},
            {"metric": "On-Time Delivery %",
             "value": on_time_pct},
            {"metric": "High-Risk Suppliers",
             "value": high_risk_suppliers},
            {"metric": "Low-Cover Products",
             "value": low_cover_products},
            {"metric": "Products Requiring Reorder",
             "value": reorder_products},
        ])

        # Export three CSV reports in the project folder.
        output_dir = Path(__file__).resolve().parent

        suppliers.to_csv(
            output_dir / "supplier_delivery_analysis.csv",
            index=False
        )
        inventory.to_csv(
            output_dir / "inventory_risk_analysis.csv",
            index=False
        )
        summary.to_csv(
            output_dir / "supplyshield_executive_summary.csv",
            index=False
        )

        # Print executive summary.
        print("\n" + "=" * 60)
        print("SUPPLYSHIELD — EXECUTIVE RISK REPORT")
        print("=" * 60)
        print(summary.to_string(index=False))

        print("\nSUPPLIER DELIVERY AND RISK")
        print("-" * 60)
        print(suppliers.to_string(index=False, na_rep="N/A"))

        print("\nINVENTORY RISK")
        print("-" * 60)
        print(inventory.to_string(index=False, na_rep="N/A"))

        print("\nCSV reports saved successfully:")
        print("1. supplier_delivery_analysis.csv")
        print("2. inventory_risk_analysis.csv")
        print("3. supplyshield_executive_summary.csv")

    except Exception as error:
        print(f"\nRisk report failed: {error}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
