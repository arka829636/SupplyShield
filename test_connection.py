
import os

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

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT DATABASE(), COUNT(*) FROM purchase_orders")
        )
        database_name, order_count = result.fetchone()

        print("MySQL connection successful!")
        print(f"Database: {database_name}")
        print(f"Purchase orders found: {order_count}")

except Exception as error:
    print("MySQL connection failed.")
    print(f"Error: {error}")

finally:
    engine.dispose()
