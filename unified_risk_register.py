
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

SUPPLIER_QUERY = """
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
"""

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


def build_supplier_risks(df):
    df["late_orders"] = df["late_orders"].fillna(0)
    df["total_orders"] = df["total_orders"].fillna(0)

    df["late_delivery_pct"] = (
        df["late_orders"]
        .div(df["total_orders"].replace(0, float("nan")))
        .mul(100)
        .fillna(0)
    )

    delay_component = (
        df["average_late_days"].fillna(0).clip(0, 10) * 10
    )

    df["risk_score"] = (
        0.60 * df["late_delivery_pct"]
        + 0.40 * delay_component
    ).round(2)

    def supplier_priority(row):
        if row["total_orders"] < 3:
            return "LIMITED DATA"
        if row["risk_score"] >= 60:
            return "HIGH RISK"
        if row["risk_score"] >= 30:
            return "MEDIUM RISK"
        return "LOW RISK"

    df["priority"] = df.apply(supplier_priority, axis=1)

    df["risk_type"] = "SUPPLIER"
    df["entity_id"] = df["supplier_id"]
    df["entity_name"] = df["supplier_name"]
    df["key_indicator"] = df.apply(
        lambda r: (
            f'{int(r["late_orders"])} late of '
            f'{int(r["total_orders"])} orders; '
            f'{r["late_delivery_pct"]:.1f}% late'
        ),
        axis=1,
    )

    def supplier_action(row):
        if row["priority"] == "LIMITED DATA":
            return "Collect more delivery history"
        if row["priority"] == "HIGH RISK":
            return "Review supplier and agree on corrective action"
        if row["priority"] == "MEDIUM RISK":
            return "Monitor deliveries and discuss delays"
        return "Continue routine supplier monitoring"

    df["recommended_action"] = df.apply(
        supplier_action, axis=1
    )

    return df[
        [
            "risk_type", "entity_id", "entity_name",
            "risk_score", "priority", "key_indicator",
            "recommended_action",
        ]
    ]


def build_inventory_risks(df):
    df["stock_cover_days"] = (
        df["stock_on_hand"]
        .div(df["average_daily_demand"].replace(0, float("nan")))
        .round(2)
    )

    df["stock_gap_to_reorder"] = (
        df["reorder_point"] - df["stock_on_hand"]
    ).clip(lower=0)

    def inventory_priority(row):
        demand = row["average_daily_demand"]
        cover = row["stock_cover_days"]

        if pd.isna(demand) or demand <= 0:
            return "CHECK DEMAND"
        if cover < 3:
            return "CRITICAL"
        if cover < 7:
            return "HIGH"
        if row["stock_on_hand"] <= row["reorder_point"]:
            return "REORDER"
        return "NORMAL"

    df["priority"] = df.apply(inventory_priority, axis=1)

    # These are inventory prioritization points, not ML scores.
    inventory_points = {
        "CRITICAL": 90,
        "HIGH": 70,
        "REORDER": 50,
        "CHECK DEMAND": 40,
        "NORMAL": 10,
    }
    df["risk_score"] = df["priority"].map(inventory_points)

    df["risk_type"] = "INVENTORY"
    df["entity_id"] = df["product_id"]
    df["entity_name"] = df["product_name"]
    df["key_indicator"] = df.apply(
        lambda r: (
            f'{r["stock_cover_days"]:.2f} days cover; '
            f'{int(r["stock_gap_to_reorder"])} units below '
            'reorder point'
        ) if pd.notna(r["stock_cover_days"]) else "Demand needs review",
        axis=1,
    )

    actions = {
        "CRITICAL": "Escalate urgently and arrange replenishment",
        "HIGH": "Review replenishment and supplier lead time",
        "REORDER": "Create or review a replenishment order",
        "CHECK DEMAND": "Validate average daily demand",
        "NORMAL": "Continue routine inventory monitoring",
    }
    df["recommended_action"] = df["priority"].map(actions)

    return df[
        [
            "risk_type", "entity_id", "entity_name",
            "risk_score", "priority", "key_indicator",
            "recommended_action",
        ]
    ]


def main():
    try:
        with engine.connect() as connection:
            suppliers = pd.read_sql(
                text(SUPPLIER_QUERY), connection
            )
            inventory = pd.read_sql(
                text(INVENTORY_QUERY), connection
            )

        supplier_risks = build_supplier_risks(suppliers)
        inventory_risks = build_inventory_risks(inventory)

        register = pd.concat(
            [supplier_risks, inventory_risks],
            ignore_index=True,
        )

        # Explicit business-priority ordering across both risk types.
        priority_order = {
            "CRITICAL": 1,
            "HIGH RISK": 2,
            "HIGH": 3,
            "MEDIUM RISK": 4,
            "REORDER": 5,
            "CHECK DEMAND": 6,
            "LIMITED DATA": 7,
            "LOW RISK": 8,
            "NORMAL": 9,
        }

        register["priority_rank"] = (
            register["priority"].map(priority_order)
        )

        register = register.sort_values(
            ["priority_rank", "risk_score"],
            ascending=[True, False],
        ).reset_index(drop=True)

        register.insert(0, "register_rank", range(1, len(register) + 1))

        output_file = "unified_risk_register.csv"
        register.to_csv(output_file, index=False)

        print("\n" + "=" * 85)
        print("SUPPLYSHIELD — UNIFIED RISK REGISTER")
        print("=" * 85)
        print(
            register[
                [
                    "register_rank", "risk_type", "entity_name",
                    "risk_score", "priority", "key_indicator",
                    "recommended_action",
                ]
            ].to_string(index=False)
        )

        print("\nRisk summary:")
        print(register.groupby(["risk_type", "priority"]).size().to_string())
        print(f"\nSaved report: {output_file}")
        print(
            "\nNote: Supplier scores and inventory points use different "
            "scales. Ranking is based on the explicit priority rules, "
            "not a direct comparison of their numeric scores."
        )

    except Exception as error:
        print(f"Unified risk register failed: {error}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
