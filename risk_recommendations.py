
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# --------------------------------------------------
# 1. Connect to MySQL
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
# 2. Supplier performance
# --------------------------------------------------
SUPPLIER_QUERY = """
SELECT
    s.supplier_id,
    s.supplier_name,
    COUNT(po.order_id) AS total_orders,
    SUM(
        CASE
            WHEN po.actual_delivery_date IS NOT NULL
             AND po.expected_delivery_date IS NOT NULL
             AND po.actual_delivery_date > po.expected_delivery_date
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
"""

# --------------------------------------------------
# 3. Inventory data
# --------------------------------------------------
INVENTORY_QUERY = """
SELECT
    p.product_id,
    p.product_name,
    p.category,
    i.stock_on_hand,
    i.average_daily_demand,
    i.reorder_point
FROM inventory AS i
JOIN products AS p
    ON p.product_id = i.product_id
"""


def supplier_recommendations(df):
    recommendations = []

    for _, row in df.iterrows():
        total = int(row["total_orders"] or 0)
        late = int(row["late_orders"] or 0)
        average_delay = row["average_late_days"]

        if total < 3:
            priority = "LIMITED DATA"
            action = (
                "Collect more delivery history before making "
                "a firm supplier risk decision."
            )
        elif late / total >= 0.60:
            priority = "HIGH"
            action = (
                "Arrange a supplier performance review and agree "
                "on corrective actions for late deliveries."
            )
        elif late / total >= 0.30:
            priority = "MEDIUM"
            action = (
                "Monitor upcoming deliveries and discuss the "
                "causes of delays with the supplier."
            )
        elif late > 0:
            priority = "LOW"
            action = (
                "Monitor delivery performance and confirm "
                "upcoming delivery dates."
            )
        else:
            priority = "LOW"
            action = (
                "Continue routine monitoring of delivery performance."
            )

        if pd.notna(average_delay):
            evidence = (
                f"{late} late order(s) out of {total}; "
                f"average delay on late orders: "
                f"{average_delay:.1f} day(s)"
            )
        else:
            evidence = (
                f"{late} late order(s) out of {total}; "
                "no average delay available"
            )

        recommendations.append({
            "risk_type": "SUPPLIER",
            "entity_id": row["supplier_id"],
            "entity_name": row["supplier_name"],
            "priority": priority,
            "evidence": evidence,
            "recommended_action": action,
        })

    return recommendations


def inventory_recommendations(df):
    recommendations = []

    for _, row in df.iterrows():
        stock = row["stock_on_hand"]
        demand = row["average_daily_demand"]
        reorder_point = row["reorder_point"]

        if pd.isna(demand) or demand <= 0:
            cover = None
            gap = max(0, reorder_point - stock)
            priority = "CHECK DEMAND"
            action = (
                "Validate average daily demand before calculating "
                "stock coverage or replenishment needs."
            )
            evidence = "Average daily demand is missing or non-positive."

        else:
            cover = stock / demand
            gap = max(0, reorder_point - stock)

            if cover < 3:
                priority = "CRITICAL"
                action = (
                    "Urgently review available stock, open orders, "
                    "and replenishment options."
                )
            elif cover < 7:
                priority = "HIGH"
                action = (
                    "Review replenishment timing and supplier lead "
                    "time to reduce stockout risk."
                )
            elif stock <= reorder_point:
                priority = "REORDER"
                action = (
                    "Review a replenishment order to restore stock "
                    "to at least the reorder point."
                )
            else:
                priority = "LOW"
                action = (
                    "Continue routine stock monitoring and review "
                    "demand trends."
                )

            evidence = (
                f"{cover:.2f} days of stock cover; "
                f"{int(gap)} additional unit(s) to reach reorder point"
            )

        recommendations.append({
            "risk_type": "INVENTORY",
            "entity_id": row["product_id"],
            "entity_name": row["product_name"],
            "priority": priority,
            "evidence": evidence,
            "recommended_action": action,
        })

    return recommendations


def main():
    try:
        with engine.connect() as connection:
            suppliers = pd.read_sql(
                text(SUPPLIER_QUERY), connection
            )
            inventory = pd.read_sql(
                text(INVENTORY_QUERY), connection
            )

        recommendations = (
            supplier_recommendations(suppliers)
            + inventory_recommendations(inventory)
        )

        report = pd.DataFrame(recommendations)

        priority_order = {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "REORDER": 4,
            "CHECK DEMAND": 5,
            "LIMITED DATA": 6,
            "LOW": 7,
        }

        report["priority_rank"] = report["priority"].map(
            priority_order
        )

        report = report.sort_values(
            ["priority_rank", "risk_type", "entity_name"]
        ).reset_index(drop=True)

        report.insert(0, "recommendation_id", range(1, len(report) + 1))

        output_file = "risk_recommendations.csv"
        report.to_csv(output_file, index=False)

        print("\n" + "=" * 85)
        print("SUPPLYSHIELD — RISK RECOMMENDATIONS")
        print("=" * 85)

        columns = [
            "recommendation_id",
            "risk_type",
            "entity_name",
            "priority",
            "evidence",
            "recommended_action",
        ]

        print(report[columns].to_string(index=False))

        print("\nRecommendation summary:")
        print(report.groupby(["risk_type", "priority"]).size().to_string())
        print(f"\nReport saved to: {output_file}")
        print(
            "\nThese recommendations use rule-based logic and the "
            "current sample data. Review them before taking action."
        )

    except Exception as error:
        print(f"Risk recommendation generation failed: {error}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
