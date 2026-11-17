import pandas as pd
import os


def generate_sample_data():

    # Create sample_data folder if it doesn't exist
    os.makedirs("sample_data", exist_ok=True)

    # --------------------------------
    # 1. PAYMENT PLATFORM TRANSACTIONS
    # --------------------------------

    platform_data = [
        {
            "transaction_id": "TXN001",
            "amount": 1000.00,
            "transaction_date": "2026-01-28",
            "type": "PAYMENT",
            "original_transaction_id": ""
        },
        {
            "transaction_id": "TXN002",
            "amount": 500.00,
            "transaction_date": "2026-01-29",
            "type": "PAYMENT",
            "original_transaction_id": ""
        },
        {
            "transaction_id": "TXN003",
            "amount": 2000.00,
            "transaction_date": "2026-01-31",
            "type": "PAYMENT",
            "original_transaction_id": ""
        },
        {
            "transaction_id": "TXN004",
            "amount": 750.00,
            "transaction_date": "2026-01-31",
            "type": "PAYMENT",
            "original_transaction_id": ""
        },
        {
            "transaction_id": "TXN005",
            "amount": 300.00,
            "transaction_date": "2026-01-30",
            "type": "PAYMENT",
            "original_transaction_id": ""
        },

        # Intentional duplicate entry
        {
            "transaction_id": "TXN005",
            "amount": 300.00,
            "transaction_date": "2026-01-30",
            "type": "PAYMENT",
            "original_transaction_id": ""
        },

        # Intentional orphan refund
        {
            "transaction_id": "REF001",
            "amount": 250.00,
            "transaction_date": "2026-01-31",
            "type": "REFUND",
            "original_transaction_id": "TXN999"
        },

        # Rounding difference test records
        {
            "transaction_id": "ROUND001",
            "amount": 10.004,
            "transaction_date": "2026-01-25",
            "type": "PAYMENT",
            "original_transaction_id": ""
        },
        {
            "transaction_id": "ROUND002",
            "amount": 10.004,
            "transaction_date": "2026-01-26",
            "type": "PAYMENT",
            "original_transaction_id": ""
        }
    ]

    # --------------------------------
    # 2. BANK SETTLEMENT RECORDS
    # --------------------------------

    bank_data = [
        {
            "settlement_id": "SET001",
            "transaction_id": "TXN001",
            "amount": 1000.00,
            "settlement_date": "2026-01-29",
            "type": "CREDIT"
        },
        {
            "settlement_id": "SET002",
            "transaction_id": "TXN002",
            "amount": 500.00,
            "settlement_date": "2026-01-30",
            "type": "CREDIT"
        },

        # Next-month settlement
        {
            "settlement_id": "SET003",
            "transaction_id": "TXN003",
            "amount": 2000.00,
            "settlement_date": "2026-02-02",
            "type": "CREDIT"
        },
        {
            "settlement_id": "SET004",
            "transaction_id": "TXN004",
            "amount": 750.00,
            "settlement_date": "2026-02-02",
            "type": "CREDIT"
        },
        {
            "settlement_id": "SET005",
            "transaction_id": "TXN005",
            "amount": 300.00,
            "settlement_date": "2026-01-31",
            "type": "CREDIT"
        },

        # Bank-only transaction
        {
            "settlement_id": "SET006",
            "transaction_id": "TXN006",
            "amount": 400.00,
            "settlement_date": "2026-01-31",
            "type": "CREDIT"
        },

        # Rounding test records
        {
            "settlement_id": "SET007",
            "transaction_id": "ROUND001",
            "amount": 10.00,
            "settlement_date": "2026-01-27",
            "type": "CREDIT"
        },
        {
            "settlement_id": "SET008",
            "transaction_id": "ROUND002",
            "amount": 10.00,
            "settlement_date": "2026-01-28",
            "type": "CREDIT"
        }
    ]

    # Convert to DataFrames
    platform_df = pd.DataFrame(platform_data)
    bank_df = pd.DataFrame(bank_data)

    # Save CSV files
    platform_df.to_csv(
        "sample_data/platform_transactions.csv",
        index=False
    )

    bank_df.to_csv(
        "sample_data/bank_settlements.csv",
        index=False
    )

    print("Sample data generated successfully!")
    print("Platform records:", len(platform_df))
    print("Bank records:", len(bank_df))
    print("Files saved inside sample_data folder.")


if __name__ == "__main__":
    generate_sample_data()