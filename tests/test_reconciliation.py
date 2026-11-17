# from data_generator import generate_sample_data
# from reconciliation import reconcile
# import pandas as pd


# def test_reconciliation_engine():

#     generate_sample_data()

#     platform = pd.read_csv(
#         "sample_data/platform_transactions.csv"
#     )

#     bank = pd.read_csv(
#         "sample_data/bank_settlements.csv"
#     )

#     records, summary = reconcile(platform, bank)

#     print("\nRECONCILIATION RESULTS")
#     print(records[
#         ["transaction_id", "status", "reason"]
#     ].to_string(index=False))

#     print("\nSUMMARY")
#     print(summary)

#     assert summary["next_month_settlements"] == 2
#     assert summary["matched"] == 4
#     assert summary["duplicates"] == 1
#     assert summary["orphan_refunds"] == 1
#     assert summary["bank_only"] == 1
#     assert summary["missing_bank"] == 0
#     assert summary["aggregate_rounding_detected"] is True
#     assert abs(summary["aggregate_rounding_difference"] - 0.008) < 0.000001

import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

import pandas as pd

from data_generator import generate_sample_data
from reconciliation import reconcile


def test_original_assessment_scenarios():

    generate_sample_data()

    platform = pd.read_csv(
        "sample_data/platform_transactions.csv"
    )

    bank = pd.read_csv(
        "sample_data/bank_settlements.csv"
    )

    records, summary = reconcile(platform, bank)

    assert summary["matched"] == 4
    assert summary["next_month_settlements"] == 2
    assert summary["duplicates"] == 1
    assert summary["orphan_refunds"] == 1
    assert summary["bank_only"] == 1
    assert summary["aggregate_rounding_detected"] is True


def make_platform(amount=1000):

    return pd.DataFrame([{
        "transaction_id": "TXN100",
        "amount": amount,
        "transaction_date": "2026-01-10",
        "type": "PAYMENT",
        "original_transaction_id": ""
    }])


def make_bank(rows):

    return pd.DataFrame(rows, columns=[
        "settlement_id",
        "transaction_id",
        "amount",
        "settlement_date",
        "type"
    ])


def test_multiple_bank_settlements():

    platform = make_platform()

    bank = make_bank([
        ["SET1", "TXN100", 600, "2026-01-11", "CREDIT"],
        ["SET2", "TXN100", 400, "2026-01-12", "CREDIT"]
    ])

    records, summary = reconcile(platform, bank)

    assert records.iloc[0]["status"] == "MATCHED"
    assert records.iloc[0]["bank_amount"] == 1000


def test_partial_settlement():

    platform = make_platform()

    bank = make_bank([
        ["SET1", "TXN100", 700, "2026-01-11", "CREDIT"]
    ])

    records, summary = reconcile(platform, bank)

    assert records.iloc[0]["status"] == "PARTIAL_SETTLEMENT"
    assert summary["partial_settlements"] == 1


def test_duplicate_bank_settlement_id():

    platform = make_platform()

    bank = make_bank([
        ["SET1", "TXN100", 1000, "2026-01-11", "CREDIT"],
        ["SET1", "TXN100", 1000, "2026-01-11", "CREDIT"]
    ])

    records, summary = reconcile(platform, bank)

    assert records.iloc[0]["status"] == "DUPLICATE_BANK"
    assert summary["duplicates"] == 1


def test_missing_transaction_id():

    platform = make_platform()
    platform.loc[0, "transaction_id"] = None

    bank = make_bank([
        ["SET1", "TXN100", 1000, "2026-01-11", "CREDIT"]
    ])

    try:
        reconcile(platform, bank)
        assert False, "Expected validation error"
    except ValueError as error:
        assert "missing transaction IDs" in str(error)


def test_invalid_amount():

    platform = make_platform()

    # Convert amount column to text before inserting invalid data
    platform["amount"] = platform["amount"].astype(str)

    platform.loc[0, "amount"] = "invalid"

    bank = make_bank([
        ["SET1", "TXN100", 1000, "2026-01-11", "CREDIT"]
    ])

    try:
        reconcile(platform, bank)
        assert False, "Expected validation error"

    except ValueError as error:
        assert "Invalid monetary amount" in str(error)