
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
    p.product_id,
    p.product_name,
    p.category,
    i.stock_on_hand,
    i.average_daily_demand,
    i.reorder_point
FROM inventory AS i
JOIN products AS p
    ON p.product_id = i.product_id
ORDER BY p.product_name;
"""


def classify_priority(row):
    if pd.isna(row["average_daily_demand"]) or row["average_daily_demand"] <= 0:
        return "CHECK DEMAND"

    if row["stock_cover_days"] < 3:
        return "CRITICAL"

    if row["stock_cover_days"] < 7:
        return "HIGH"

    if row["stock_on_hand"] <= row["reorder_point"]:
        return "REORDER"

    return "NORMAL"


def main():
    try:
        with engine.connect() as connection:
            df = pd.read_sql(text(query), connection)

        # Calculate stock coverage and distance from reorder point.
        df["stock_cover_days"] = (
            df["stock_on_hand"]
            / df["average_daily_demand"].replace(0, float("nan"))
        ).round(2)

        df["stock_gap_to_reorder"] = (
            df["reorder_point"] - df["stock_on_hand"]
        ).clip(lower=0)

        df["priority"] = df.apply(classify_priority, axis=1)

        priority_order = {
            "CRITICAL": 1,
            "HIGH": 2,
            "REORDER": 3,
            "CHECK DEMAND": 4,
            "NORMAL": 5,
        }

        df["priority_rank"] = df["priority"].map(priority_order)

        df = df.sort_values(
            ["priority_rank", "stock_cover_days"],
            ascending=[True, True],
            na_position="last",
        ).reset_index(drop=True)

        df.insert(0, "risk_rank", range(1, len(df) + 1))

        output_file = "inventory_risk_prioritization.csv"
        df.to_csv(output_file, index=False)

        print("\n" + "=" * 75)
        print("SUPPLYSHIELD — INVENTORY RISK PRIORITIZATION")
        print("=" * 75)

        columns = [
            "risk_rank",
            "product_name",
            "stock_on_hand",
            "reorder_point",
            "stock_cover_days",
            "stock_gap_to_reorder",
            "priority",
        ]

        print(df[columns].to_string(index=False, na_rep="N/A"))

        print("\nPriority rules:")
        print("CRITICAL: stock coverage below 3 days")
        print("HIGH: stock coverage below 7 days")
        print("REORDER: stock at or below reorder point")
        print("NORMAL: sufficient coverage and stock")
        print(f"\nReport saved to: {output_file}")

    except Exception as error:
        print(f"Inventory prioritization failed: {error}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
