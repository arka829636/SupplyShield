
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


def run_check(connection, name, query):
    """Run one data-quality check and return its findings."""
    df = pd.read_sql(text(query), connection)
    issue_count = len(df)

    status = "PASS" if issue_count == 0 else "WARNING"

    print(f"\n[{status}] {name}: {issue_count} issue(s)")

    if issue_count:
        print(df.to_string(index=False, na_rep="NULL"))
    else:
        print("No issues found.")

    return {
        "check_name": name,
        "status": status,
        "issue_count": issue_count,
    }


checks = [
    (
        "Duplicate purchase order IDs",
        """
        SELECT order_id, COUNT(*) AS occurrences
        FROM purchase_orders
        GROUP BY order_id
        HAVING COUNT(*) > 1
        """,
    ),
    (
        "Missing purchase order dates or status",
        """
        SELECT order_id, order_date, expected_delivery_date,
               actual_delivery_date, order_status
        FROM purchase_orders
        WHERE order_date IS NULL
           OR expected_delivery_date IS NULL
           OR actual_delivery_date IS NULL
           OR order_status IS NULL
        """,
    ),
    (
        "Invalid purchase order quantities or costs",
        """
        SELECT order_id, quantity, unit_cost
        FROM purchase_orders
        WHERE quantity IS NULL OR quantity <= 0
           OR unit_cost IS NULL OR unit_cost < 0
        """,
    ),
    (
        "Delivery date before order date",
        """
        SELECT order_id, order_date, expected_delivery_date,
               actual_delivery_date
        FROM purchase_orders
        WHERE expected_delivery_date < order_date
           OR actual_delivery_date < order_date
        """,
    ),
    (
        "Unexpected order status",
        """
        SELECT order_id, order_status
        FROM purchase_orders
        WHERE order_status IS NULL
           OR order_status NOT IN
              ('Pending', 'In Transit', 'Delivered', 'Cancelled')
        """,
    ),
    (
        "Duplicate supplier IDs",
        """
        SELECT supplier_id, COUNT(*) AS occurrences
        FROM suppliers
        GROUP BY supplier_id
        HAVING COUNT(*) > 1
        """,
    ),
    (
        "Duplicate product IDs",
        """
        SELECT product_id, COUNT(*) AS occurrences
        FROM products
        GROUP BY product_id
        HAVING COUNT(*) > 1
        """,
    ),
    (
        "Missing or invalid inventory values",
        """
        SELECT product_id, stock_on_hand, average_daily_demand,
               reorder_point
        FROM inventory
        WHERE stock_on_hand IS NULL OR stock_on_hand < 0
           OR average_daily_demand IS NULL
           OR average_daily_demand < 0
           OR reorder_point IS NULL OR reorder_point < 0
        """,
    ),
    (
        "Inventory with no matching product",
        """
        SELECT i.product_id
        FROM inventory AS i
        LEFT JOIN products AS p
            ON p.product_id = i.product_id
        WHERE p.product_id IS NULL
        """,
    ),
    (
        "Purchase orders with missing supplier or product",
        """
        SELECT po.order_id, po.supplier_id, po.product_id
        FROM purchase_orders AS po
        LEFT JOIN suppliers AS s
            ON s.supplier_id = po.supplier_id
        LEFT JOIN products AS p
            ON p.product_id = po.product_id
        WHERE s.supplier_id IS NULL
           OR p.product_id IS NULL
        """,
    ),
]


def main():
    results = []

    try:
        print("=" * 65)
        print("SUPPLYSHIELD — DATA QUALITY REPORT")
        print("=" * 65)

        with engine.connect() as connection:
            for name, query in checks:
                results.append(
                    run_check(connection, name, query)
                )

        report = pd.DataFrame(results)
        output_file = "data_quality_report.csv"
        report.to_csv(output_file, index=False)

        total_checks = len(report)
        passed = int((report["status"] == "PASS").sum())
        warnings = int((report["status"] == "WARNING").sum())
        total_issues = int(report["issue_count"].sum())

        print("\n" + "=" * 65)
        print("DATA QUALITY SUMMARY")
        print("=" * 65)
        print(f"Checks run:       {total_checks}")
        print(f"Passed checks:    {passed}")
        print(f"Checks with issues: {warnings}")
        print(f"Total issue rows: {total_issues}")
        print(f"\nReport saved to: {output_file}")

        if total_issues:
            print("\nReview the warnings before relying on the analytics.")
        else:
            print("\nAll configured checks passed.")

    except Exception as error:
        print(f"\nData-quality validation failed: {error}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
