
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
    s.supplier_id,
    s.supplier_name,
    COUNT(po.order_id) AS total_orders,
    SUM(
        CASE
            WHEN po.actual_delivery_date <= po.expected_delivery_date
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
                WHEN po.actual_delivery_date <= po.expected_delivery_date
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
ORDER BY on_time_delivery_pct ASC, s.supplier_name;
"""

try:
    with engine.connect() as connection:
        df = pd.read_sql(text(query), connection)

    print("\nSUPPLYSHIELD — SUPPLIER DELIVERY PERFORMANCE")
    print("=" * 65)
    print(df.to_string(index=False))

    # Save the analysis output for later reporting.
    output_file = "supplier_delivery_analysis.csv"
    df.to_csv(output_file, index=False)
    print(f"\nAnalysis saved to: {output_file}")

except Exception as error:
    print(f"Analytics failed: {error}")

finally:
    engine.dispose()
