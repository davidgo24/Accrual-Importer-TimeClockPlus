# Accrual Balance Report → TimeClockPlus Import

Converts the AccrualBalanceReport.xlsx into TimeClockPlus accrual bank import format, filtering to **current bus operators only** (employees in `employee_list.csv`).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate   # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

## Web UI (recommended)

```bash
streamlit run accrual_app.py
```

Opens a browser where you can:
- Upload the Accrual Balance Report (Excel) and Employee List (CSV)
- Pick pay period start and end dates
- Download the generated import CSV

## Command line

```bash
python accrual_import.py <AccrualBalanceReport.xlsx> <employee_list.csv> \
  --pay-period-start "2/22/2026" \
  --pay-period-end "3/8/2026" \
  -o timeclockplus_accrual_import.csv
```

### Required arguments

| Argument | Description |
|----------|-------------|
| `balance_report` | Path to AccrualBalanceReport.xlsx |
| `employee_list` | Path to employee_list.csv (current bus operators) |
| `--pay-period-start` | **Col E** – Day pay period starts (e.g. `2/22/2026`) |
| `--pay-period-end` | **Col F** – Day pay period ends (e.g. `3/8/2026`) — adjust for when TimeClockPlus clears |

### Optional

- `-o`, `--output` – Output CSV path (default: `timeclockplus_accrual_import.csv`)

## Pay period dates (Col E & F)

Enter the day the pay period starts (`--pay-period-start`) and the day it ends (`--pay-period-end`). Adjust the end date if needed based on when TimeClockPlus clears accruals.

## Output format

Matches TimeClockPlus accrual import:

| Col A | Col B | Col C | Col D | Col E | Col F |
|-------|-------|-------|-------|-------|-------|
| Employee # | Type (AL, CTO, HOL, SICK, VACA) | Balance (hrs) | Index (1–5) | Accrual Start | Accrual End |

## File requirements

- **employee_list.csv** – Must include an `EmployeeNumber` column (e.g. 1020, 1025, …).
- **AccrualBalanceReport.xlsx** – Standard accrual report with columns: Employee, AL, COMP, HOLIDAY, SICK, VAC.
