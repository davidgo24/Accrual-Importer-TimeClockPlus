#!/usr/bin/env python3
"""Streamlit UI for Accrual Balance Report → TimeClockPlus import."""

import tempfile
from pathlib import Path

import streamlit as st

from accrual_import import (
    build_import_rows,
    load_accrual_report,
    load_current_employees,
    write_timeclockplus_csv,
)

st.set_page_config(
    page_title="Accrual Import",
    page_icon="⏱️",
    layout="centered",
)

st.title("⏱️ TimeClockPlus Accrual Import")
st.markdown(
    "Convert your Accrual Balance Report into TimeClockPlus format. "
    "Only employees from your current bus operator list are included."
)

st.divider()

# File uploads
col1, col2 = st.columns(2)

with col1:
    balance_report = st.file_uploader(
        "**Accrual Balance Report** (Excel)",
        type=["xlsx", "xls"],
        help="Upload AccrualBalanceReport.xlsx",
    )

with col2:
    employee_list = st.file_uploader(
        "**Employee List** (current bus operators)",
        type=["csv"],
        help="Upload employee_list.csv with EmployeeNumber column",
    )

# Pay period dates
st.subheader("Pay period dates")
st.caption("Day pay period starts and ends (adjust end date for when TimeClockPlus clears)")

date_col1, date_col2 = st.columns(2)
with date_col1:
    pay_start = st.date_input("Pay period start", value=None)
with date_col2:
    pay_end = st.date_input("Pay period end", value=None)

# Convert dates to M/D/YYYY format for output (matches TimeClockPlus)
def format_date(d):
    return f"{d.month}/{d.day}/{d.year}" if d else None

# Run import
st.divider()

if st.button("Generate import CSV", type="primary", use_container_width=True):
    if not balance_report:
        st.error("Please upload the Accrual Balance Report (Excel file).")
    elif not employee_list:
        st.error("Please upload the Employee List (CSV).")
    elif not pay_start or not pay_end:
        st.error("Please select both pay period start and end dates.")
    elif pay_start >= pay_end:
        st.error("Pay period end must be after pay period start.")
    else:
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                report_path = Path(tmpdir) / "balance_report.xlsx"
                emp_path = Path(tmpdir) / "employee_list.csv"

                report_path.write_bytes(balance_report.read())
                emp_path.write_bytes(employee_list.read())

                pay_start_str = format_date(pay_start)
                pay_end_str = format_date(pay_end)

                current_employees = load_current_employees(emp_path)
                report_df = load_accrual_report(report_path)
                rows = build_import_rows(
                    report_df,
                    current_employees,
                    pay_start_str,
                    pay_end_str,
                )

                out_path = Path(tmpdir) / "timeclockplus_accrual_import.csv"
                write_timeclockplus_csv(rows, out_path)
                csv_bytes = out_path.read_bytes()

            num_employees = len(set(r[0] for r in rows))
            st.success(
                f"Generated **{len(rows)}** accrual rows for **{num_employees}** employees. "
                f"Pay period: {pay_start_str} — {pay_end_str}"
            )

            st.download_button(
                label="Download timeclockplus_accrual_import.csv",
                data=csv_bytes,
                file_name="timeclockplus_accrual_import.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )

        except Exception as e:
            st.error(f"Error processing files: {e}")

st.divider()
st.caption(
    "Output format: Employee # | Type (AL, CTO, HOL, SICK, VACA) | Balance | Index (1-5) | Start | End"
)
