import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from reconciliation import reconcile


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="ReconcileX | Transaction Reconciliation",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# DESIGN SYSTEM
# =====================================================

st.markdown("""
<style>

/* Main application */
.stApp {
    background: #f5f7fb;
    color: #172033;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #101c35;
}

[data-testid="stSidebar"] * {
    color: #e8eef9 !important;
}

/* Headings */
h1, h2, h3 {
    color: #172b4d !important;
    letter-spacing: -0.5px;
}

p, label {
    color: #526078;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #ffffff;
    padding: 20px;
    border-radius: 13px;
    border: 1px solid #e5eaf2;
    box-shadow: 0 2px 8px rgba(20, 40, 80, 0.04);
}

[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-size: 14px;
}

[data-testid="stMetricValue"] {
    color: #172b4d !important;
    font-weight: 700;
}

/* Upload area */
[data-testid="stFileUploader"] {
    background: #ffffff;
    border: 1px solid #dce4f0;
    border-radius: 12px;
    padding: 12px;
}

[data-testid="stFileUploaderDropzone"] {
    background: #f8faff;
    border: 1px dashed #9db5dc;
    border-radius: 10px;
}

/* Buttons */
.stButton > button,
.stDownloadButton > button {
    border-radius: 9px;
    font-weight: 600;
    min-height: 42px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 10px 18px;
}

/* Tables */
[data-testid="stDataFrame"] {
    border: 1px solid #e5eaf2;
    border-radius: 10px;
}

/* Info containers */
div[data-testid="stAlert"] {
    border-radius: 10px;
}

/* Dividers */
hr {
    border-color: #e5eaf2;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def create_excel_report(records, summary):

    output = BytesIO()

    summary_data = []

    for key, value in summary.items():
        summary_data.append({
            "Metric": key.replace("_", " ").title(),
            "Value": str(value)
        })

    summary_df = pd.DataFrame(summary_data)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        records.to_excel(
            writer,
            index=False,
            sheet_name="Transactions"
        )

        summary_df.to_excel(
            writer,
            index=False,
            sheet_name="Summary"
        )

    output.seek(0)

    return output.getvalue()


def show_metric(label, value, help_text=None):
    st.metric(
        label=label,
        value=value,
        help=help_text
    )


def safe_count(summary, key):
    return summary.get(key, 0)


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.markdown("# 💳 ReconcileX")
    st.caption("FINANCIAL RECONCILIATION PLATFORM")

    st.divider()

    st.markdown("### Navigation")
    st.markdown("📊  Dashboard Overview")
    st.markdown("📁  File Upload")
    st.markdown("🔍  Transaction Analysis")
    st.markdown("⚠️  Exception Monitoring")
    st.markdown("📥  Reports")

    st.divider()

    st.markdown("### How it works")

    st.markdown("""
    **01 — Upload**

    Upload your platform and bank CSV files.

    **02 — Reconcile**

    Compare transaction records automatically.

    **03 — Analyze**

    Review matched records and exceptions.

    **04 — Export**

    Download your reconciliation report.
    """)

    st.divider()

    st.caption("ReconcileX • Smart Reconciliation")


# =====================================================
# HEADER
# =====================================================

header_left, header_right = st.columns([3, 1])

with header_left:
    st.markdown("# Reconciliation Dashboard")
    st.markdown(
        "Monitor payments, compare bank settlements and identify "
        "transaction discrepancies."
    )

with header_right:
    st.markdown(" ")
    st.markdown(" ")
    st.success("● System Ready")

st.divider()


# =====================================================
# FILE UPLOAD SECTION
# =====================================================

st.markdown("## Upload your data")
st.caption(
    "Upload both CSV files to start the reconciliation process."
)

upload_col1, upload_col2 = st.columns(2)

with upload_col1:

    st.markdown("### 🧾 Platform Transactions")

    platform_file = st.file_uploader(
        "Choose platform CSV",
        type=["csv"],
        key="platform_upload",
        help="Upload your platform transaction records."
    )

    if platform_file:
        st.success(f"Uploaded: {platform_file.name}")

with upload_col2:

    st.markdown("### 🏦 Bank Settlements")

    bank_file = st.file_uploader(
        "Choose bank CSV",
        type=["csv"],
        key="bank_upload",
        help="Upload your bank settlement records."
    )

    if bank_file:
        st.success(f"Uploaded: {bank_file.name}")


with st.expander("What format should my CSV files have?"):

    st.markdown("""
    **Platform CSV:** should contain transaction details such as
    transaction ID, amount, date and transaction type.

    **Bank CSV:** should contain settlement ID, transaction ID,
    amount, settlement date and transaction type.

    The exact required column names are validated by the
    reconciliation engine.
    """)


run_col, reset_col = st.columns([3, 1])

with run_col:

    run_button = st.button(
        "▶  Run Reconciliation",
        type="primary",
        use_container_width=True
    )

with reset_col:

    reset_button = st.button(
        "↻  Reset Dashboard",
        use_container_width=True
    )


if reset_button:

    st.session_state.pop("records", None)
    st.session_state.pop("summary", None)

    st.rerun()


# =====================================================
# RECONCILIATION PROCESS
# =====================================================

if run_button:

    if platform_file is None or bank_file is None:

        st.warning(
            "Please upload both Platform Transactions and "
            "Bank Settlements CSV files."
        )

    else:

        try:

            platform_df = pd.read_csv(platform_file)
            bank_df = pd.read_csv(bank_file)

            with st.spinner(
                "Analyzing transactions and comparing settlements..."
            ):

                records, summary = reconcile(
                    platform_df,
                    bank_df
                )

            st.session_state["records"] = records
            st.session_state["summary"] = summary

            st.success(
                "Reconciliation completed successfully!"
            )

        except Exception as error:

            st.error(f"Reconciliation failed: {error}")


# =====================================================
# DASHBOARD RESULTS
# =====================================================

if "records" in st.session_state:

    records = st.session_state["records"]
    summary = st.session_state["summary"]

    st.divider()

    st.markdown("## Overview")
    st.caption("A quick summary of your reconciliation results.")

    # Main KPI cards

    row1 = st.columns(4)

    with row1[0]:
        show_metric(
            "Platform Transactions",
            safe_count(summary, "total_platform_records")
        )

    with row1[1]:
        show_metric(
            "Matched Transactions",
            safe_count(summary, "matched")
        )

    with row1[2]:
        show_metric(
            "Missing Bank Records",
            safe_count(summary, "missing_bank")
        )

    with row1[3]:
        show_metric(
            "Bank-only Records",
            safe_count(summary, "bank_only")
        )

    st.markdown(" ")

    row2 = st.columns(4)

    with row2[0]:
        show_metric(
            "Duplicate Records",
            safe_count(summary, "duplicates")
        )

    with row2[1]:
        show_metric(
            "Amount Mismatches",
            safe_count(summary, "amount_mismatches")
        )

    with row2[2]:
        show_metric(
            "Partial Settlements",
            safe_count(summary, "partial_settlements")
        )

    with row2[3]:
        show_metric(
            "Orphan Refunds",
            safe_count(summary, "orphan_refunds")
        )

    st.markdown(" ")

    st.info(
        f"Additional refund exceptions pending bank: "
        f"{safe_count(summary, 'refunds_pending_bank')}"
    )

    # =================================================
    # TABS
    # =================================================

    overview_tab, transactions_tab, exceptions_tab, reports_tab = st.tabs([
        "📊 Overview",
        "🔍 Transactions",
        "⚠️ Exceptions",
        "📥 Reports"
    ])

    # =================================================
    # OVERVIEW TAB
    # =================================================

    with overview_tab:

        st.markdown("### Transaction Analytics")

        if not records.empty and "status" in records.columns:

            status_counts = (
                records["status"]
                .fillna("UNKNOWN")
                .value_counts()
                .reset_index()
            )

            status_counts.columns = ["Status", "Count"]

            matched_count = safe_count(summary, "matched")
            total_records = len(records)
            other_count = max(total_records - matched_count, 0)

            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:

                comparison = pd.DataFrame({
                    "Category": ["Matched", "Other"],
                    "Count": [matched_count, other_count]
                })

                fig1 = px.pie(
                    comparison,
                    names="Category",
                    values="Count",
                    hole=0.65,
                    title="Matched vs Other Transactions",
                    color="Category",
                    color_discrete_map={
                        "Matched": "#16a36a",
                        "Other": "#e8a23b"
                    }
                )

                fig1.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=60, b=20, l=20, r=20),
                    legend_title_text=""
                )

                st.plotly_chart(
                    fig1,
                    use_container_width=True
                )

            with chart_col2:

                fig2 = px.bar(
                    status_counts,
                    x="Status",
                    y="Count",
                    color="Status",
                    title="Transaction Status Distribution",
                    text="Count"
                )

                fig2.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=60, b=20, l=20, r=20),
                    showlegend=False,
                    xaxis_title="Transaction Status",
                    yaxis_title="Number of Transactions"
                )

                st.plotly_chart(
                    fig2,
                    use_container_width=True
                )

            # Aggregate rounding information

            st.markdown("### Settlement Summary")

            rounding_col1, rounding_col2 = st.columns(2)

            with rounding_col1:

                st.metric(
                    "Aggregate Rounding Difference",
                    str(summary.get(
                        "aggregate_rounding_difference", 0
                    ))
                )

            with rounding_col2:

                detected = summary.get(
                    "aggregate_rounding_detected", False
                )

                if detected:
                    st.warning("Aggregate rounding detected")
                else:
                    st.success("No aggregate rounding detected")

        else:

            st.info("No transaction records are available for analytics.")

    # =================================================
    # TRANSACTIONS TAB
    # =================================================

    with transactions_tab:

        st.markdown("### All Transactions")

        if not records.empty and "status" in records.columns:

            statuses = sorted(
                records["status"]
                .fillna("UNKNOWN")
                .unique()
                .tolist()
            )

            selected_status = st.selectbox(
                "Filter transactions by status",
                ["ALL"] + statuses
            )

            if selected_status == "ALL":

                filtered_records = records

            else:

                filtered_records = records[
                    records["status"].fillna("UNKNOWN")
                    == selected_status
                ]

            st.caption(
                f"{len(filtered_records)} transaction(s) displayed"
            )

            st.dataframe(
                filtered_records,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No transactions available.")

    # =================================================
    # EXCEPTIONS TAB
    # =================================================

    with exceptions_tab:

        st.markdown("### Exception Monitoring")

        st.caption(
            "Review transactions that require attention or investigation."
        )

        if not records.empty and "status" in records.columns:

            exceptions = records[
                ~records["status"].isin([
                    "MATCHED",
                    "REFUND_SETTLED"
                ])
            ]

            if not exceptions.empty:

                st.warning(
                    f"{len(exceptions)} transaction(s) require review."
                )

                st.dataframe(
                    exceptions,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.success("Great! No outstanding exceptions found.")

        else:

            st.info("No exception records available.")

    # =================================================
    # REPORTS TAB
    # =================================================

    with reports_tab:

        st.markdown("### Export Reconciliation Reports")

        st.caption(
            "Download your results for further analysis and record keeping."
        )

        download_col1, download_col2 = st.columns(2)

        with download_col1:

            st.markdown("#### CSV Report")

            st.write(
                "Download the complete transaction-level reconciliation data."
            )

            st.download_button(
                "⬇ Download CSV",
                data=records.to_csv(index=False).encode("utf-8"),
                file_name="reconcilex_report.csv",
                mime="text/csv",
                use_container_width=True
            )

        with download_col2:

            st.markdown("#### Excel Report")

            st.write(
                "Download an Excel workbook with transaction and summary sheets."
            )

            excel_data = create_excel_report(
                records,
                summary
            )

            st.download_button(
                "⬇ Download Excel",
                data=excel_data,
                file_name="reconcilex_report.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True
            )

        st.success("Your reports are ready to download.")


# =====================================================
# EMPTY DASHBOARD STATE
# =====================================================

else:

    st.markdown(" ")

    st.info(
        "Your dashboard is waiting for data. Upload both CSV files "
        "and click **Run Reconciliation** to view your results."
    )

    st.markdown("### What you can analyze")

    feature1, feature2, feature3 = st.columns(3)

    with feature1:

        st.markdown("#### ✅ Transaction Matching")
        st.caption(
            "Identify transactions that match between the platform and bank."
        )

    with feature2:

        st.markdown("#### ⚠️ Exception Detection")
        st.caption(
            "Find missing payments, duplicate records and amount mismatches."
        )

    with feature3:

        st.markdown("#### 📊 Financial Reports")
        st.caption(
            "Analyze results and export reconciliation reports."
        )


# =====================================================
# FOOTER
# =====================================================

st.divider()

st.markdown(
    "<div style='text-align:center;color:#8491a5;"
    "font-size:13px;padding:10px;'>"
    "ReconcileX • Smart Financial Transaction Reconciliation"
    "</div>",
    unsafe_allow_html=True
)