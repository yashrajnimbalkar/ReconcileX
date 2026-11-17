import pandas as pd
from decimal import Decimal, InvalidOperation


TOLERANCE = Decimal("0.005")


def to_decimal(value):
    """Convert monetary values safely into Decimal."""

    if pd.isna(value):
        raise ValueError("Amount cannot be empty.")

    try:
        amount = Decimal(str(value))

        if not amount.is_finite():
            raise ValueError("Amount must be a finite number.")

        return amount

    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid monetary amount: {value}")


def reconcile(platform_df, bank_df, tolerance=TOLERANCE):

    # -----------------------------------
    # 1. VALIDATE REQUIRED COLUMNS
    # -----------------------------------

    required_platform = {
        "transaction_id",
        "amount",
        "transaction_date",
        "type",
        "original_transaction_id"
    }

    required_bank = {
        "settlement_id",
        "transaction_id",
        "amount",
        "settlement_date",
        "type"
    }

    if not required_platform.issubset(platform_df.columns):
        raise ValueError("Platform CSV is missing required columns.")

    if not required_bank.issubset(bank_df.columns):
        raise ValueError("Bank CSV is missing required columns.")

    if not isinstance(tolerance, Decimal):
        tolerance = Decimal(str(tolerance))

    if not tolerance.is_finite() or tolerance < 0:
        raise ValueError("Tolerance must be a non-negative finite number.")

    platform = platform_df.copy()
    bank = bank_df.copy()

    # -----------------------------------
    # 2. NORMALIZE IDENTIFIERS
    # -----------------------------------

    for column in ["transaction_id", "type"]:
        platform[column] = (
            platform[column].astype("string").str.strip().str.upper()
        )

    for column in ["settlement_id", "transaction_id", "type"]:
        bank[column] = (
            bank[column].astype("string").str.strip().str.upper()
        )

    if platform["transaction_id"].isna().any() or (
        platform["transaction_id"] == ""
    ).any():
        raise ValueError("Platform contains missing transaction IDs.")

    if bank["transaction_id"].isna().any() or (
        bank["transaction_id"] == ""
    ).any():
        raise ValueError("Bank contains missing transaction IDs.")

    if bank["settlement_id"].isna().any() or (
        bank["settlement_id"] == ""
    ).any():
        raise ValueError("Bank contains missing settlement IDs.")

    # -----------------------------------
    # 3. VALIDATE AMOUNTS AND DATES
    # -----------------------------------

    platform["amount_decimal"] = platform["amount"].apply(to_decimal)
    bank["amount_decimal"] = bank["amount"].apply(to_decimal)

    if (platform["amount_decimal"] < 0).any():
        raise ValueError("Platform amounts cannot be negative.")

    if (bank["amount_decimal"] < 0).any():
        raise ValueError("Bank amounts cannot be negative.")

    platform["transaction_date"] = pd.to_datetime(
        platform["transaction_date"], errors="raise"
    )

    bank["settlement_date"] = pd.to_datetime(
        bank["settlement_date"], errors="raise"
    )

    # -----------------------------------
    # 4. DETECT DUPLICATES
    # -----------------------------------

    duplicate_platform_ids = set(
        platform.loc[
            platform["transaction_id"].duplicated(keep=False),
            "transaction_id"
        ]
    )

    duplicate_settlement_ids = set(
        bank.loc[
            bank["settlement_id"].duplicated(keep=False),
            "settlement_id"
        ]
    )

    duplicate_bank_transaction_ids = set(
        bank.loc[
            bank["settlement_id"].isin(duplicate_settlement_ids),
            "transaction_id"
        ]
    )

    # A repeated settlement ID is not counted twice.
    bank = bank.drop_duplicates(
        subset=["settlement_id"],
        keep="first"
    ).copy()

    # -----------------------------------
    # 5. GROUP BANK SETTLEMENTS
    # -----------------------------------

    bank_groups = {
        transaction_id: group
        for transaction_id, group in bank.groupby(
            "transaction_id",
            sort=False
        )
    }

    platform_ids = set(platform["transaction_id"])

    results = []

    used_bank_ids = set()

    rounding_platform_total = Decimal("0")
    rounding_bank_total = Decimal("0")
    rounding_count = 0

    # -----------------------------------
    # 6. PROCESS PLATFORM TRANSACTIONS
    # -----------------------------------

    for _, transaction in platform.iterrows():

        txn_id = transaction["transaction_id"]
        txn_type = transaction["type"]
        amount = transaction["amount_decimal"]

        bank_amount = None
        difference = None
        settlement_date = None
        settlement_ids = []

        status = ""
        reason = ""

        bank_group = bank_groups.get(txn_id)

        if bank_group is not None:
            settlement_ids = bank_group["settlement_id"].tolist()
            used_bank_ids.update(settlement_ids)

            bank_amount = sum(
                bank_group["amount_decimal"],
                Decimal("0")
            )

            settlement_date = bank_group["settlement_date"].max()

            difference = amount - bank_amount

        # Duplicate platform transaction
        if txn_id in duplicate_platform_ids:

            status = "DUPLICATE"
            reason = (
                "Transaction ID occurs multiple times in platform data. "
                "Manual investigation required."
            )

        # Duplicate bank settlement identifier
        elif txn_id in duplicate_bank_transaction_ids:

            status = "DUPLICATE_BANK"
            reason = (
                "A bank settlement ID is duplicated. "
                "Duplicate settlement was excluded from totals."
            )

        # Refund validation
        elif txn_type == "REFUND":

            original_id = transaction["original_transaction_id"]

            if pd.isna(original_id) or str(original_id).strip() == "":

                status = "ORPHAN_REFUND"
                reason = "Refund has no original transaction ID."

            else:

                original_id = str(original_id).strip().upper()

                original_payment_exists = (
                    (
                        platform["transaction_id"] == original_id
                    ) &
                    (
                        platform["type"] == "PAYMENT"
                    )
                ).any()

                if not original_payment_exists:

                    status = "ORPHAN_REFUND"
                    reason = (
                        f"Original payment {original_id} does not exist."
                    )

                elif bank_group is None:

                    status = "REFUND_PENDING_BANK"
                    reason = (
                        "Original payment exists, but refund "
                        "settlement is not present in bank data."
                    )

                elif abs(difference) <= tolerance:

                    status = "REFUND_SETTLED"
                    reason = (
                        "Refund has a valid original payment "
                        "and matching bank settlement."
                    )

                else:

                    status = "REFUND_AMOUNT_MISMATCH"
                    reason = (
                        "Refund amount does not match bank settlement."
                    )

        # Payment validation
        elif txn_type == "PAYMENT":

            if bank_group is None:

                status = "MISSING_BANK_SETTLEMENT"
                reason = "No bank settlement found for this transaction."

            elif abs(difference) <= tolerance:

                months = set(
                    bank_group["settlement_date"].dt.to_period("M")
                )

                if (
                    transaction["transaction_date"].to_period("M")
                    not in months
                ):

                    status = "NEXT_MONTH_SETTLEMENT"
                    reason = (
                        "Payment was settled in a different month."
                    )

                else:

                    status = "MATCHED"

                    if len(bank_group) > 1:
                        reason = (
                            "Multiple bank settlements were combined "
                            "and successfully matched."
                        )
                    else:
                        reason = "Transaction ID and amount match."

                # Track small individual rounding differences
                if difference != 0:

                    rounding_platform_total += amount
                    rounding_bank_total += bank_amount
                    rounding_count += 1

            elif bank_amount < amount:

                status = "PARTIAL_SETTLEMENT"
                reason = (
                    "Bank received less than the platform transaction "
                    "amount."
                )

            else:

                status = "AMOUNT_MISMATCH"
                reason = (
                    "Bank received more than the expected platform amount."
                )

        else:

            status = "UNSUPPORTED_TRANSACTION_TYPE"
            reason = f"Unsupported transaction type: {txn_type}"

        results.append({
            "transaction_id": txn_id,
            "transaction_type": txn_type,
            "platform_amount": float(amount),
            "bank_amount": (
                float(bank_amount)
                if bank_amount is not None else None
            ),
            "difference": (
                float(difference)
                if difference is not None else None
            ),
            "settlement_ids": ", ".join(settlement_ids),
            "settlement_date": settlement_date,
            "status": status,
            "reason": reason
        })

    # -----------------------------------
    # 7. FIND BANK-ONLY TRANSACTIONS
    # -----------------------------------

    for _, bank_row in bank.iterrows():

        txn_id = bank_row["transaction_id"]

        if txn_id not in platform_ids:

            results.append({
                "transaction_id": txn_id,
                "transaction_type": "BANK_ONLY",
                "platform_amount": None,
                "bank_amount": float(bank_row["amount_decimal"]),
                "difference": None,
                "settlement_ids": bank_row["settlement_id"],
                "settlement_date": bank_row["settlement_date"],
                "status": "BANK_ONLY_TRANSACTION",
                "reason": (
                    "Bank transaction has no corresponding "
                    "platform transaction."
                )
            })

    # -----------------------------------
    # 8. AGGREGATE ROUNDING CHECK
    # -----------------------------------

    aggregate_difference = (
        rounding_platform_total - rounding_bank_total
    )

    aggregate_rounding_detected = (
        rounding_count > 1 and aggregate_difference != 0
    )

    # -----------------------------------
    # 9. BUILD RESULTS
    # -----------------------------------

    records = pd.DataFrame(results)

    status_counts = records["status"].value_counts().to_dict()

    # -----------------------------------
    # 10. SUMMARY
    # -----------------------------------

    summary = {

        "total_platform_records": len(platform),
        "total_bank_records": len(bank),

        "matched": status_counts.get("MATCHED", 0),

        "next_month_settlements": status_counts.get(
            "NEXT_MONTH_SETTLEMENT", 0
        ),

        "duplicates": (
            len(duplicate_platform_ids)
            + len(duplicate_settlement_ids)
        ),

        "orphan_refunds": status_counts.get(
            "ORPHAN_REFUND", 0
        ),

        "missing_bank": status_counts.get(
            "MISSING_BANK_SETTLEMENT", 0
        ),

        "bank_only": status_counts.get(
            "BANK_ONLY_TRANSACTION", 0
        ),

        "amount_mismatches": status_counts.get(
            "AMOUNT_MISMATCH", 0
        ),

        "partial_settlements": status_counts.get(
            "PARTIAL_SETTLEMENT", 0
        ),

        "refunds_pending_bank": status_counts.get(
            "REFUND_PENDING_BANK", 0
        ),

        "aggregate_rounding_difference": float(
            aggregate_difference
        ),

        "aggregate_rounding_detected": aggregate_rounding_detected,

        "status_counts": status_counts
    }

    return records, summary