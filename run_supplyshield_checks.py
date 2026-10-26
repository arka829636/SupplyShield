
import subprocess
import sys

SCRIPTS = [
    "validate_synthetic_data.py",
    "validate_batch_predictions.py",
    "test_delivery_model.py",
    "integration_check.py",
]

def main():
    print("=" * 65)
    print("SUPPLYSHIELD — PROJECT CHECK RUNNER")
    print("=" * 65)

    results = []

    for script in SCRIPTS:
        print(f"\n\nRunning: {script}")
        print("-" * 65)

        result = subprocess.run(
            [sys.executable, script],
            check=False,
        )

        passed = result.returncode == 0
        results.append((script, passed))

        print(f"\n{'PASS' if passed else 'FAIL'} | {script}")

    print("\n\nFINAL SUMMARY")
    print("=" * 65)

    for script, passed in results:
        print(f"{'PASS' if passed else 'FAIL'} | {script}")

    failed = [script for script, passed in results if not passed]

    print(f"\nPassed: {len(results) - len(failed)} / {len(results)}")

    if failed:
        print("Fix the failed checks before continuing.")
        sys.exit(1)

    print("All selected project checks passed.")
    print("This does not establish real-world model accuracy.")

if __name__ == "__main__":
    main()
