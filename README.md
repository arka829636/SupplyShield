# SupplyShield --- Supply Chain Analytics & Risk Intelligence

SupplyShield is an MCA portfolio prototype combining SQL analytics,
Python risk reporting, a Power BI dashboard, and an experimental
machine-learning workflow for supplier delivery and inventory risk.

> **Important limitation:** The current ML dataset and batch prediction
> examples are synthetic. Model probabilities are demonstrations, not
> calibrated real-world forecasts, and must not be used for operational
> purchasing decisions.

## Objectives

-   Analyze supplier delivery performance and late orders.
-   Identify low-stock-coverage products and replenishment needs.
-   Calculate rule-based supplier and inventory risk indicators.
-   Display operational KPIs in Power BI.
-   Demonstrate a delivery-delay classification workflow.
-   Validate exported data and selected project scripts.

## Technology stack

  -----------------------------------------------------------------------
  Technology                          Purpose
  ----------------------------------- -----------------------------------
  MySQL 8                             Suppliers, products, purchase
                                      orders, and inventory tables

  Python                              Analytics, risk reports, model
                                      workflow, and validation

  pandas / NumPy                      Data preparation and tabular
                                      analysis

  mysql-connector-python              Python-to-MySQL connection

  SQLAlchemy                          SQL toolkit used in the Python
                                      environment, where applicable

  scikit-learn                        Classification pipeline and model
                                      evaluation

  joblib                              Save and load the model pipeline

  python-dotenv                       Read local settings from `.env`

  Power BI Desktop                    Dashboard and prediction visual

  Git / GitHub                        Version control and sharing
  -----------------------------------------------------------------------

## Architecture

``` text
MySQL (suppliers, products, purchase_orders, inventory)
                 |
                 v
       Python analytics and risk rules
                 |
          CSV risk reports
                 |
                 v
       Synthetic ML demonstration
       | generate / validate data
       | train / compare models
       | save pipeline / predict
                 |
       batch prediction CSV
                 |
                 v
           Power BI report
       | operational KPIs
       | supplier and inventory charts
       | filters / demo prediction chart
```

## Database

The local database is named `supplyshield`. Its main tables are:

-   `suppliers`: supplier ID, name, region, and category.
-   `products`: product ID, name, category, and unit cost.
-   `purchase_orders`: order dates, expected and actual delivery dates,
    quantity, supplier/product references, and status.
-   `inventory`: stock on hand, average daily demand, reorder point, and
    last update.

The current sample database contains 4 suppliers, 4 products, 10
purchase orders, and 4 inventory records. These are sample records, not
production data.

## Prerequisites

-   Windows and Python
-   MySQL Server and MySQL Workbench
-   Power BI Desktop
-   A project virtual environment such as `.venv`

Install dependencies in the activated environment:

``` powershell
python -m pip install --upgrade pip
python -m pip install pandas numpy sqlalchemy mysql-connector-python python-dotenv scikit-learn joblib
```

If a `requirements.txt` file exists, prefer installing from it to keep
versions consistent.

## Environment configuration

Create a local `.env` file in the project root:

``` text
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YOUR_LOCAL_MYSQL_PASSWORD
DB_NAME=supplyshield
```

Replace the placeholder with your local MySQL password. Never commit
`.env` or credentials to GitHub. Confirm `.env` is included in
`.gitignore`.

## Running the project

Run commands from the project root with the virtual environment
activated.

### 1. Test the database connection

``` powershell
python test_connection.py
```

### 2. Run core analytics

``` powershell
python supplier_analytics.py
python inventory_analytics.py
python risk_report.py
python supplier_risk_scoring.py
python unified_risk_register.py
python risk_recommendations.py
```

These scripts produce terminal summaries and, depending on the script,
CSV reports.

### 3. Prepare and validate the ML dataset

``` powershell
python generate_synthetic_data.py
python validate_synthetic_data.py
python validate_ml_dataset.py
```

`synthetic_ml_training_data.csv` is simulated data, not a record of
actual deliveries.

### 4. Train and compare models

``` powershell
python train_delivery_model.py
python evaluate_model.py
python improve_delivery_model.py
python save_final_model.py
```

Generated artifacts may include:

-   `supplyshield_delivery_model.joblib`
-   `supplyshield_model_metadata.json`
-   `model_evaluation_comparison.csv`
-   `improved_model_comparison.csv`

Scores from synthetic data must not be presented as real-world accuracy.

### 5. Generate and validate demo predictions

``` powershell
python predict_delivery.py
python batch_delivery_predictions.py
python validate_batch_predictions.py
```

The batch script creates `supplyshield_batch_predictions.csv`. Its
`DEMO` order IDs and `SYNTHETIC_DEMO` label identify illustrative
records, not actual purchase orders.

### 6. Run project checks

``` powershell
python test_delivery_model.py
python integration_check.py
python run_supplyshield_checks.py
```

A passing run confirms the selected checks completed. It does not prove
predictive accuracy, security, production readiness, or business impact.

## Power BI dashboard

The current report includes operational views such as:

-   Supplier, purchase-order, completion, late-order, and
    on-time-delivery KPIs
-   Inventory stock by product and low-cover product counts
-   Supplier late-delivery rate
-   Delivery volume trend
-   Supplier, category, and region slicers
-   A prediction chart based on `supplyshield_batch_predictions.csv`

To regenerate the demo prediction CSV:

``` powershell
python batch_delivery_predictions.py
```

Then refresh or re-import the CSV in Power BI as needed. Keep synthetic
predictions clearly labelled and separate from actual operational data.
Do not join `DEMO001`-style IDs to real purchase-order IDs.

## Risk methodology

-   Inventory coverage is stock on hand divided by average daily demand.
-   Reorder status follows the configured stock-coverage and
    reorder-point rules.
-   Supplier risk scores summarize the delivery history using rule-based
    calculations.
-   The ML classifier predicts a simulated `was_late` target from the
    input features.

Rule-based scores and ML probabilities are different measures and should
not be compared directly. Thresholds and recommended actions require
review against real business requirements before operational use.

## Current limitations

-   The operational sample is small: 4 suppliers, 4 products, and 10
    purchase orders.
-   ML labels are generated synthetically, so the model may learn
    simulation patterns rather than real causes of delays.
-   Test scores do not establish real-world predictive performance.
-   Batch predictions are illustrative demo orders.
-   Authentication, API serving, production deployment, monitoring, and
    comprehensive automated tests are not established as completed
    features.
-   Verify Power BI refresh and relationships when moving the report to
    another computer.

## Recommended next milestones

1.  Add a pinned `requirements.txt`.
2.  Add unit tests for analytics and risk calculations.
3.  Obtain a larger, representative, permissioned historical delivery
    dataset.
4.  Use leakage-safe validation and meaningful baselines.
5.  Add FastAPI after the data and model interfaces are stable.
6.  Polish Power BI formatting and document refresh steps.
7.  Add deployment instructions and a short demo.

## Suggested repository structure

``` text
SupplyShield/
├── .env                         # Local only; never commit
├── .gitignore
├── README.md
├── test_connection.py
├── supplier_analytics.py
├── inventory_analytics.py
├── risk_report.py
├── supplier_risk_scoring.py
├── unified_risk_register.py
├── risk_recommendations.py
├── generate_synthetic_data.py
├── validate_synthetic_data.py
├── validate_ml_dataset.py
├── train_delivery_model.py
├── evaluate_model.py
├── improve_delivery_model.py
├── save_final_model.py
├── predict_delivery.py
├── test_delivery_model.py
├── batch_delivery_predictions.py
├── validate_batch_predictions.py
├── integration_check.py
├── run_supplyshield_checks.py
├── *.csv                         # Generated reports / demo data
├── *.joblib                      # Generated model artifact
└── *.pbix                        # Power BI report, if stored here
```

This is a guide; include only files that actually exist in your
repository.

## Portfolio description

**SupplyShield --- Supply Chain Analytics & Risk Intelligence:** Built a
prototype combining MySQL, Python analytics, rule-based supplier and
inventory risk scoring, a Power BI dashboard, and an experimental
scikit-learn delivery-delay classifier. Added synthetic-data validation,
model evaluation, prediction export, and repeatable integration checks.
The ML component is documented as a demonstration pending validation on
representative real-world data.
