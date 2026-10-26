
from pathlib import Path
import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

PREDICTIONS_FILE = Path("supplyshield_batch_predictions.csv")

def main():
    print("=" * 60)
    print("SUPPLYSHIELD — INTEGRATION CHECK")
    print("=" * 60)

    # Check 1: MySQL connection and source record count.
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "supplyshield"),
        )

        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM purchase_orders")
        order_count = cursor.fetchone()[0]

        print(f"PASS | MySQL connected; purchase orders: {order_count}")

        cursor.close()
        connection.close()
    except Exception as error:
        print(f"FAIL | MySQL connection: {error}")

    # Check 2: Prediction CSV exists and has required columns.
    if not PREDICTIONS_FILE.exists():
        print(f"FAIL | Prediction CSV missing: {PREDICTIONS_FILE}")
        return

    try:
        df = pd.read_csv(PREDICTIONS_FILE)

        required = {
            "order_id",
            "predicted_was_late",
            "predicted_late_probability",
            "predicted_outcome",
            "data_source",
        }

        if not required.issubset(df.columns):
            print("FAIL | Prediction CSV is missing required columns")
            return

        print(f"PASS | Prediction CSV loaded; rows: {len(df)}")

        valid_predictions = df["predicted_was_late"].isin([0, 1]).all()
        valid_probabilities = df["predicted_late_probability"].between(0, 1).all()
        unique_ids = df["order_id"].is_unique
        labelled_demo = (df["data_source"] == "SYNTHETIC_DEMO").all()

        print(f"{'PASS' if valid_predictions else 'FAIL'} | Prediction labels valid")
        print(f"{'PASS' if valid_probabilities else 'FAIL'} | Probabilities within 0–1")
        print(f"{'PASS' if unique_ids else 'FAIL'} | Order IDs unique")
        print(f"{'PASS' if labelled_demo else 'FAIL'} | Rows labelled as synthetic demo")

        print("\nIntegration check finished.")
        print("These checks verify connectivity and data structure, not model accuracy.")

    except Exception as error:
        print(f"FAIL | Prediction CSV validation: {error}")


if __name__ == "__main__":
    main()
