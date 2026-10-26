# SupplyShield — Supply Chain Analytics & Risk Intelligence

SupplyShield is a supply chain analytics prototype built using **Python, MySQL, Power BI, and machine learning**. It analyzes supplier delivery performance, identifies inventory risks, generates recommendations, and demonstrates a delivery-delay prediction workflow.

> **Important:** The current ML model uses synthetic training data. Its predictions are experimental and have not been validated on real-world delivery data.

## Dashboard Preview

The Power BI dashboard provides a consolidated view of supplier performance, inventory health, and delivery trends.

**Dashboard file:** [`SupplyShield_Dashboard.pbix`](SupplyShield_Dashboard.pbix)

Download the PBIX file from this repository and open it using Power BI Desktop.

## Key Features

- **Supplier analytics:** On-time delivery rates, late-order counts, and supplier comparisons.
- **Inventory risk analysis:** Stock coverage, reorder thresholds, and low-cover product identification.
- **Risk scoring:** Rule-based supplier risk ranking and inventory prioritization.
- **Actionable recommendations:** Suggested follow-up actions based on observed risk indicators.
- **Delivery-delay ML prototype:** A scikit-learn classification workflow trained on synthetic data.
- **Batch predictions:** Export predicted outcomes and probabilities to CSV.
- **Validation tools:** Scripts for data-quality, prediction-structure, and integration checks.
- **Interactive Power BI dashboard:** KPI cards, charts, and supplier, category, and region slicers.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Analytics, risk calculations, and ML workflow |
| MySQL | Relational database |
| pandas and NumPy | Data processing |
| scikit-learn | Classification and model evaluation |
| joblib | Model serialization |
| python-dotenv | Local environment configuration |
| Power BI Desktop | Interactive dashboard |
| Git and GitHub | Version control and project sharing |

## Architecture

```text
MySQL Database
      |
      v
Python Analytics
  |-- Supplier Performance
  |-- Inventory Risk
  |-- Risk Scoring
  |-- Recommendations
      |
      +------> CSV Reports
      |
      v
Synthetic ML Workflow
  |-- Dataset Generation and Validation
  |-- Model Training and Evaluation
  |-- Batch Predictions
      |
      v
Power BI Dashboard
```

## Database

The MySQL database is named `supplyshield` and contains these main tables:

- `suppliers`
- `products`
- `purchase_orders`
- `inventory`

The current operational sample contains 4 suppliers, 4 products, 10 purchase orders, and 4 inventory records. These are demonstration records, not production data.

## Setup

### Prerequisites

- Python
- MySQL Server and MySQL Workbench
- Power BI Desktop

### Install dependencies

Activate your virtual environment, then run:

```bash
python -m pip install -r requirements.txt
```

### Configure MySQL

Create a local `.env` file in the project root:

```text
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YOUR_LOCAL_MYSQL_PASSWORD
DB_NAME=supplyshield
```

Replace the password placeholder with your local MySQL password. Never upload `.env` or credentials to GitHub.

### Run the project

Test the database connection:

```bash
python test_connection.py
```

Run core analytics:

```bash
python supplier_analytics.py
python inventory_analytics.py
python risk_report.py
python supplier_risk_scoring.py
python unified_risk_register.py
python risk_recommendations.py
```

Generate and validate synthetic training data:

```bash
python generate_synthetic_data.py
python validate_synthetic_data.py
python validate_ml_dataset.py
```

Train and evaluate the experimental model:

```bash
python train_delivery_model.py
python evaluate_model.py
python improve_delivery_model.py
python save_final_model.py
```

Generate and validate batch predictions:

```bash
python batch_delivery_predictions.py
python validate_batch_predictions.py
```

Run the selected project checks:

```bash
python run_supplyshield_checks.py
```

## Power BI Dashboard

The report includes:

- Supplier and purchase-order KPIs
- On-time delivery percentage and late-order counts
- Inventory stock by product
- Supplier late-delivery rates
- Delivery volume trend
- Supplier, category, and region slicers
- A chart showing synthetic demo prediction probabilities

The dashboard's prediction visual uses `supplyshield_batch_predictions.csv`. Regenerate the file by running the batch prediction script, then refresh or re-import it in Power BI as required.

## Machine Learning Limitations

The delivery-delay model is an experimental demonstration trained on synthetic records. Its evaluation scores do not establish real-world predictive accuracy. The displayed probabilities are not calibrated business risk estimates.

A larger, representative historical dataset and more rigorous validation are needed before the model can support operational decisions.

## Testing

The project includes scripts to check synthetic-data validity, batch prediction structure, model interface behavior, and integration with MySQL. The selected automated checks have passed on the local development environment.

Passing these checks confirms the tested interfaces and data conditions; it does not establish production readiness or real-world model accuracy.

## Future Improvements

- Obtain and validate representative historical supply-chain data.
- Add comprehensive unit and integration tests.
- Improve model validation and probability calibration.
- Add a FastAPI service once data and prediction interfaces are stable.
- Improve dashboard design and refresh documentation.
- Plan deployment, monitoring, and access control.

## Portfolio Summary

SupplyShield demonstrates practical skills in SQL, Python analytics, inventory and supplier risk analysis, Power BI reporting, machine-learning experimentation, data validation, and Git-based project management.
