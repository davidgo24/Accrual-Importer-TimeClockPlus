#!/usr/bin/env python3
"""
Accrual Balance Report → TimeClockPlus Accrual Bank Import

Transforms the AccrualBalanceReport.xlsx into TimeClockPlus format, filtering
to only include current bus operators from employee_list.csv.
"""

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd


# Map Accrual Balance Report columns → TimeClockPlus format
# Report cols: 0=EmpNum, 3=AL, 6=COMP/CTO, 7=HOLIDAY, 8=SICK, 9=VAC
ACCRUAL_MAPPING = [
    ("AL", 3, 1),   # Annual Leave, report col 3, TCP index 1
    ("CTO", 6, 2),  # Comp Time, report col 6, TCP index 2
    ("HOL", 7, 3),  # Holiday, report col 7, TCP index 3
    ("SICK", 8, 4), # Sick, report col 8, TCP index 4
    ("VACA", 9, 5), # Vacation, report col 9, TCP index 5
]


def load_current_employees(employee_list_path: Path) -> set[str]:
    """Load employee numbers from employee_list.csv."""
    employees = set()
    with open(employee_list_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "EmployeeNumber" not in reader.fieldnames:
            raise ValueError(
                "employee_list.csv must have an 'EmployeeNumber' column. "
                f"Found: {reader.fieldnames}"
            )
        for row in reader:
            emp_num = row.get("EmployeeNumber", "").strip()
            if emp_num:
                employees.add(emp_num)
    return employees


def load_accrual_report(report_path: Path) -> pd.DataFrame:
    """Load AccrualBalanceReport.xlsx, return data rows only."""
    df = pd.read_excel(report_path, header=None)

    def is_data_row(x):
        if pd.isna(x):
            return False
        s = str(x).strip().upper()
        if s in ("EMPLOYEE", "NAN", ""):
            return False
        if "PRIMARY DEPARTMENT" in s or "GRAND TOTALS" in s:
            return False
        try:
            int(float(x))
            return True
        except (ValueError, TypeError):
            return False

    mask = df.iloc[:, 0].apply(is_data_row)
    return df[mask].copy()


def build_import_rows(
    report_df: pd.DataFrame,
    current_employees: set[str],
    accrual_start: str,
    accrual_end: str,
) -> list[tuple]:
    """Build TimeClockPlus import rows (EmployeeNumber, Type, Balance, Index, Start, End)."""
    rows = []
    for _, r in report_df.iterrows():
        emp_num = str(int(r.iloc[0])).strip()
        if emp_num not in current_employees:
            continue
        for tcp_code, report_col, tcp_index in ACCRUAL_MAPPING:
            balance = r.iloc[report_col]
            if pd.isna(balance):
                balance = 0
            try:
                balance = float(balance)
            except (ValueError, TypeError):
                balance = 0
            # TCP rejects zeros ("cannot all be zero") and negatives ("Accrued must be between 0 and 200000.9999")
            if balance <= 0:
                continue
            # Preserve exact decimals; drop .0 only for whole numbers
            if balance == int(balance):
                balance_str = str(int(balance))
            else:
                balance_str = str(balance)
            rows.append((emp_num, tcp_code, balance_str, tcp_index, accrual_start, accrual_end))
    return rows


def write_timeclockplus_csv(rows: list[tuple], out_path: Path) -> None:
    """Write rows to CSV in TimeClockPlus format (no header)."""
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert Accrual Balance Report to TimeClockPlus accrual import CSV. "
        "Only includes employees from employee_list (current bus operators)."
    )
    parser.add_argument(
        "balance_report",
        type=Path,
        help="Path to AccrualBalanceReport.xlsx",
    )
    parser.add_argument(
        "employee_list",
        type=Path,
        help="Path to employee_list.csv (current bus operators)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("timeclockplus_accrual_import.csv"),
        help="Output CSV path (default: timeclockplus_accrual_import.csv)",
    )
    parser.add_argument(
        "--pay-period-start",
        required=True,
        help="Pay period start date (e.g. 2/22/2026) — Col E in output, day pay period starts",
    )
    parser.add_argument(
        "--pay-period-end",
        required=True,
        help="Pay period end date (e.g. 3/8/2026) — Col F in output, day pay period ends (adjust for when TimeClockPlus clears)",
    )
    args = parser.parse_args()

    if not args.balance_report.exists():
        print(f"Error: Balance report not found: {args.balance_report}", file=sys.stderr)
        return 1
    if not args.employee_list.exists():
        print(f"Error: Employee list not found: {args.employee_list}", file=sys.stderr)
        return 1

    current_employees = load_current_employees(args.employee_list)
    report_df = load_accrual_report(args.balance_report)
    rows = build_import_rows(
        report_df,
        current_employees,
        args.pay_period_start,
        args.pay_period_end,
    )

    write_timeclockplus_csv(rows, args.output)
    print(f"Wrote {len(rows)} accrual rows to {args.output}")
    print(f"  Employees included: {len(set(r[0] for r in rows))}")
    print(f"  Pay period: {args.pay_period_start} — {args.pay_period_end}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
