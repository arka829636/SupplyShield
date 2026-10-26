
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
    i.reorder_point,
    ROUND(
        i.stock_on_hand / NULLIF(i.average_daily_demand, 0),
        2
    ) AS stock_cover_days,
    CASE
        WHEN i.average_daily_demand <= 0 THEN 'CHECK DEMAND'
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

try:
    with engine.connect() as connection:
        df = pd.read_sql(text(query), connection)

    print("\nSUPPLYSHIELD — INVENTORY RISK ANALYSIS")
    print("=" * 75)
    print(df.to_string(index=False, na_rep="N/A"))

    output_file = "inventory_risk_analysis.csv"
    df.to_csv(output_file, index=False)
    print(f"\nAnalysis saved to: {output_file}")

except Exception as error:
    print(f"Inventory analysis failed: {error}")

finally:
    engine.dispose()
