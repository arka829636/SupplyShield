
import pandas as pd

FILE = "supplyshield_ml_dataset.csv"


def main():
    df = pd.read_csv(FILE)

    print("\n" + "=" * 60)
    print("SUPPLYSHIELD — ML DATASET READINESS CHECK")
    print("=" * 60)

    print(f"\nTotal rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")

    duplicates = df["order_id"].duplicated().sum()
    print(f"Duplicate order IDs: {duplicates}")

    unknown = df["was_late"].isna().sum()
    print(f"Unknown delivery outcomes: {unknown}")

    print("\nTarget distribution:")
    print(df["was_late"].value_counts(dropna=False).sort_index())

    known = df.dropna(subset=["was_late"])
    if len(known):
        print("\nTarget percentages:")
        print(
            (known["was_late"].value_counts(normalize=True) * 100)
            .sort_index()
            .round(2)
            .to_string()
        )

    print("\nMissing values:")
    missing = df.isna().sum()
    print(missing[missing > 0].to_string() if missing.any() else "None")

    print("\nReadiness assessment:")
    if duplicates:
        print("- FIX: duplicate order IDs found.")
    if unknown:
        print("- Review orders without known delivery outcomes.")
    if len(known) < 100:
        print("- CAUTION: too few labeled rows for reliable ML evaluation.")
    if known["was_late"].nunique() < 2:
        print("- CAUTION: the target needs both late and on-time examples.")
    if not duplicates and not unknown and len(known) >= 100:
        print("- Basic readiness checks passed; continue with feature review.")

    print(
        "\nThis is a data-quality check, not proof that the dataset "
        "is sufficient for a reliable predictive model."
    )


if __name__ == "__main__":
    main()
