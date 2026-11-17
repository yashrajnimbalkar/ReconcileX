# ReconcileX
### Smart Financial Transaction Reconciliation System

ReconcileX is a Python-based financial reconciliation application that compares platform transactions with bank settlement records. It helps identify matched transactions, missing payments, duplicate records, partial settlements, refunds and amount mismatches.

The application provides an interactive dashboard to analyze reconciliation results and download reports.

## Key Features

- **Automated Reconciliation:** Compare platform transactions with bank settlements.
- **Transaction Matching:** Identify successfully matched transactions.
- **Multiple Settlements:** Handle multiple bank settlements for a single transaction.
- **Partial Settlement Detection:** Identify transactions where only part of the expected amount is settled.
- **Duplicate Detection:** Detect duplicate platform transactions and bank settlement IDs.
- **Refund Validation:** Identify orphan refunds, pending refunds and refund mismatches.
- **Exception Analysis:** Identify missing bank records, bank-only records and amount mismatches.
- **Interactive Dashboard:** View metrics, charts and transaction details.
- **Report Export:** Download reconciliation results in CSV and Excel formats.
- **Automated Testing:** Validate functionality using Pytest.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Interactive dashboard |
| Pandas | Data processing and analysis |
| Plotly | Interactive visualizations |
| OpenPyXL | Excel report generation |
| Pytest | Automated testing |

## Project Structure

```text
ReconcileX/
│
├── app.py
├── reconciliation.py
├── data_generator.py
├── validators.py
├── requirements.txt
├── README.md
│
├── sample_data/
│   ├── platform_transactions.csv
│   └── bank_settlements.csv
│
└── tests/
    └── test_reconciliation.py
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd ReconcileX
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```bash
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

Start the Streamlit dashboard:

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal.

## How to Use

1. Open the ReconcileX dashboard.
2. Upload the platform transactions CSV file.
3. Upload the bank settlements CSV file.
4. Click **Run Reconciliation**.
5. Review the reconciliation summary and analytics.
6. Explore transaction details and exceptions.
7. Download the final CSV or Excel report.

## Running Tests

Execute the automated test suite:

```bash
python -m pytest -v
```

The test suite covers original assessment scenarios, multiple settlements, partial settlements, duplicate settlement IDs, missing transaction IDs and invalid monetary amounts.

## Project Objective

The objective of ReconcileX is to simplify financial reconciliation by automating transaction comparisons, identifying discrepancies and presenting actionable results through an easy-to-use dashboard.

---

**ReconcileX — Making Financial Reconciliation Smarter and Simpler.**