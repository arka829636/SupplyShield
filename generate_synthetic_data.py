
import numpy as np
import pandas as pd

# ============================================================
# SUPPLYSHIELD — SYNTHETIC TRAINING DATA GENERATOR
# Generates simulated data for ML pipeline practice.
# Does NOT modify the MySQL database.
# ============================================================

RANDOM_SEED = 42
NUMBER_OF_ORDERS = 500
OUTPUT_FILE = "synthetic_ml_training_data.csv"

rng = np.random.default_rng(RANDOM_SEED)

# ------------------------------------------------------------
# 1. Supplier profiles
# ------------------------------------------------------------
suppliers = {
    "S001": {
        "region": "East",
        "supplier_category": "Electronics",
        "late_probability": 0.60,
    },
    "S002": {
        "region": "South",
        "supplier_category": "Raw Materials",
        "late_probability": 0.20,
    },
    "S003": {
        "region": "West",
        "supplier_category": "Electronics",
        "late_probability": 0.65,
    },
    "S004": {
        "region": "North",
        "supplier_category": "Packaging",
        "late_probability": 0.45,
    },
}

# ------------------------------------------------------------
# 2. Product profiles
# All products have compatible supplier categories.
# ------------------------------------------------------------
products = {
    "P001": {
        "product_category": "Electronics",
        "unit_cost": 4200.00,
        "quantity_range": (40, 150),
    },
    "P002": {
        "product_category": "Raw Materials",
        "unit_cost": 650.00,
        "quantity_range": (200, 600),
    },
    "P003": {
        "product_category": "Electronics",
        "unit_cost": 480.00,
        "quantity_range": (80, 200),
    },
    "P004": {
        "product_category": "Packaging",
        "unit_cost": 35.00,
        "quantity_range": (1000, 2500),
    },
}

supplier_ids = list(suppliers.keys())

# ------------------------------------------------------------
# 3. Generate synthetic orders
# ------------------------------------------------------------
rows = []

start_date = pd.Timestamp("2025-01-01")
end_date = pd.Timestamp("2026-09-30")
date_range_days = (end_date - start_date).days

for i in range(1, NUMBER_OF_ORDERS + 1):

    # Choose a supplier first.
    supplier_id = rng.choice(supplier_ids)
    supplier = suppliers[supplier_id]

    # Choose a product compatible with that supplier.
    compatible_products = [
        product_id
        for product_id, product_info in products.items()
        if product_info["product_category"]
        == supplier["supplier_category"]
    ]

    if not compatible_products:
        raise ValueError(
            f"No compatible products for supplier {supplier_id}"
        )

    product_id = rng.choice(compatible_products)
    product = products[product_id]

    # Generate order and expected delivery dates.
    order_date = start_date + pd.Timedelta(
        days=int(rng.integers(0, date_range_days + 1))
    )

    planned_lead_days = int(rng.integers(3, 15))

    expected_delivery_date = (
        order_date + pd.Timedelta(days=planned_lead_days)
    )

    # Generate a quantity appropriate for the selected product.
    minimum_quantity, maximum_quantity = product["quantity_range"]

    quantity = int(
        rng.integers(minimum_quantity, maximum_quantity + 1)
    )

    # Simulated delay probability.
    # These assumptions are for demonstration, not real-world estimates.
    lead_adjustment = (8 - planned_lead_days) * 0.015

    probability = float(
        np.clip(
            supplier["late_probability"] + lead_adjustment,
            0.05,
            0.90,
        )
    )

    was_late = int(rng.random() < probability)

    rows.append({
        "order_id": f"SYN{i:04d}",
        "order_date": order_date,
        "expected_delivery_date": expected_delivery_date,
        "quantity": quantity,
        "unit_cost": product["unit_cost"],
        "supplier_id": supplier_id,
        "supplier_region": supplier["region"],
        "supplier_category": supplier["supplier_category"],
        "product_id": product_id,
        "product_category": product["product_category"],
        "planned_lead_days": planned_lead_days,
        "was_late": was_late,
        "data_source": "SYNTHETIC",
    })

# ------------------------------------------------------------
# 4. Create and validate the DataFrame
# ------------------------------------------------------------
df = pd.DataFrame(rows)

# Check supplier-product category compatibility.
mismatch_count = (
    df["supplier_category"] != df["product_category"]
).sum()

if mismatch_count:
    raise ValueError(
        f"Found {mismatch_count} incompatible supplier-product rows."
    )

if df["order_id"].duplicated().any():
    raise ValueError("Duplicate synthetic order IDs found.")

if df.isna().any().any():
    raise ValueError("Missing values found in generated data.")

# ------------------------------------------------------------
# 5. Export CSV
# ------------------------------------------------------------
df.to_csv(OUTPUT_FILE, index=False)

# ------------------------------------------------------------
# 6. Print summary
# ------------------------------------------------------------
print("\n" + "=" * 70)
print("SUPPLYSHIELD — SYNTHETIC TRAINING DATA")
print("=" * 70)

print(f"Generated orders: {len(df)}")
print(f"Unique order IDs: {df['order_id'].nunique()}")
print(f"Missing values: {int(df.isna().sum().sum())}")
print(f"Category mismatches: {int(mismatch_count)}")

print("\nDelivery outcome counts:")
outcome_counts = df["was_late"].value_counts().sort_index()
print(
    outcome_counts.rename(
        index={0: "On time", 1: "Late"}
    ).to_string()
)

print("\nDelivery outcome percentages:")
outcome_percentages = (
    df["was_late"]
    .value_counts(normalize=True)
    .mul(100)
    .sort_index()
    .rename(index={0: "On time", 1: "Late"})
    .round(2)
)
print(outcome_percentages.to_string())

print("\nSupplier-product category combinations:")
print(
    pd.crosstab(
        df["supplier_category"],
        df["product_category"],
    ).to_string()
)

print("\nFirst five records:")
print(df.head(5).to_string(index=False))

print(f"\nCSV saved to: {OUTPUT_FILE}")
print("All generated records are SYNTHETIC.")
print(
    "Model performance on this data does not establish "
    "real-world predictive accuracy."
)
