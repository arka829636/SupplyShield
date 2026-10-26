
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# 1. Load MySQL configuration
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

# 2. Retrieve supplier delivery performance
query = """
SELECT
    s.supplier_id,
    s.supplier_name,
    COUNT(po.order_id) AS total_orders,
    SUM(
        CASE
            WHEN po.actual_delivery_date IS NOT NULL
             AND po.expected_delivery_date IS NOT NULL
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
    AVG(
        CASE
            WHEN po.actual_delivery_date > po.expected_delivery_date
            THEN DATEDIFF(
                po.actual_delivery_date,
                po.expected_delivery_date
            )
        END
    ) AS average_late_days
FROM suppliers AS s
LEFT JOIN purchase_orders AS po
    ON s.supplier_id = po.supplier_id
GROUP BY s.supplier_id, s.supplier_name
ORDER BY s.supplier_name;
"""


def classify_risk(row):
    # Avoid strong conclusions from very small samples.
    if row["total_orders"] < 3:
        return "LIMITED DATA"

    if row["risk_score"] >= 60:
        return "HIGH RISK"
    elif row["risk_score"] >= 30:
        return "MEDIUM RISK"
    else:
        return "LOW RISK"


def main():
    try:
        with engine.connect() as connection:
            df = pd.read_sql(text(query), connection)

        # 3. Calculate performance indicators
        df["late_orders"] = df["late_orders"].fillna(0).astype(int)
        df["on_time_orders"] = (
            df["on_time_orders"].fillna(0).astype(int)
        )

        df["late_delivery_pct"] = (
            df["late_orders"]
            .div(df["total_orders"].replace(0, pd.NA))
            .mul(100)
            .fillna(0)
            .round(2)
        )

        # 4. Score: 60% late-order rate + 40% delay severity.
        # Average delay is capped at 10 days for scoring.
        delay_component = (
            df["average_late_days"].fillna(0).clip(0, 10) * 10
        )

        df["risk_score"] = (
            0.60 * df["late_delivery_pct"]
            + 0.40 * delay_component
        ).round(2)

        df["risk_level"] = df.apply(classify_risk, axis=1)

        # 5. Rank suppliers by score
        df = df.sort_values(
            by=["risk_score", "late_delivery_pct"],
            ascending=[False, False]
        ).reset_index(drop=True)

        df.insert(0, "risk_rank", range(1, len(df) + 1))

        # 6. Export results
        output_file = "supplier_risk_scoring.csv"
        df.to_csv(output_file, index=False)

        # 7. Print report
        print("\n" + "=" * 75)
        print("SUPPLYSHIELD — SUPPLIER RISK SCORING")
        print("=" * 75)

        columns_to_show = [
            "risk_rank",
            "supplier_name",
            "total_orders",
            "late_orders",
            "late_delivery_pct",
            "average_late_days",
            "risk_score",
            "risk_level",
        ]

        print(
            df[columns_to_show].to_string(
                index=False,
                na_rep="N/A"
            )
        )

        print("\nScoring methodology:")
        print("60% weight: percentage of late orders")
        print("40% weight: average late-delivery days, capped at 10")
        print("Fewer than 3 orders: LIMITED DATA classification")
        print(f"\nReport saved to: {output_file}")

    except Exception as error:
        print(f"Supplier risk scoring failed: {error}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
