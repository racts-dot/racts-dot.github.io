#!/usr/bin/env python
"""Put the June Sales Tracker spreadsheet into the live Google Sheet.

The phone app's "Mark Sold" button writes single rows into a Google Sheet.
This puts the whole history in there first, so the Sheet is the real record
instead of an almost-empty page.

    python import_excel_to_sheet.py --preview     # writes nothing, shows what would go
    python import_excel_to_sheet.py --write       # actually fills the Sheet

Needs ~/.secrets/sheets-bot-key.json and the Sheet shared with
sheets-bot@gen-lang-client-0626840434.iam.gserviceaccount.com as Editor.
"""
import argparse, csv, datetime, os, sys, pathlib

XLSX = os.environ.get("JUNE_XLSX", str(pathlib.Path.home() / "Library/CloudStorage/GoogleDrive-jiwan2603@gmail.com/My Drive/01 BUSINESS & CREATION/Ecommerce integration/racts-tracker-backup/June Sales Tracker.xlsx"))
SHEET_ID = os.environ.get("RESALE_SHEET_ID", "1ZUvi_jA--rzVlR6fWKVEx3jecCa8jGKeRDOr72dUjXI")
TAB = "Sales"
KEY = os.environ.get("SHEETS_BOT_KEY", str(pathlib.Path.home() / ".secrets/sheets-bot-key.json"))

# The column order the Apps Script connector expects. Do not reorder.
HEADER = ['#','Item','Category','Channel','Status','Order date','Sold date','Week',
          'Cost','Received','Net','Account','Recipient/Buyer','Supplier',
          'Carrier & Tracking','Order ID','Batch','Notes']

# xlsx column name -> our column name
FROM_XLSX = {'#':'#','Item':'Item','Status':'Status','Order date':'Order date',
             'Sold date':'Sold date','Wk':'Week','Cost':'Cost','Received':'Received',
             'Net':'Net','Device / email':'Account','Ship-to / Buyer':'Recipient/Buyer',
             'Supplier':'Supplier','Carrier & Tracking':'Carrier & Tracking',
             'Supplier order ID':'Order ID','Notes':'Notes'}

EPOCH = datetime.date(1899, 12, 30)  # Excel's day zero


def as_date(v):
    """Excel stores dates as a count of days. Turn that back into a date."""
    if v is None or v == "":
        return ""
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.strftime("%Y-%m-%d")
    try:
        n = float(v)
    except (TypeError, ValueError):
        return str(v)
    if 20000 < n < 60000:
        return (EPOCH + datetime.timedelta(days=int(n))).isoformat()
    return str(v)


def as_text(v):
    if v is None:
        return ""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v).replace("\n", " ").strip()


def channel_of(status):
    """Work out where it sold from the wording of the Status column."""
    s = (status or "").lower()
    if s.startswith("personal"):
        return "Personal"
    if "ebay" in s:
        return "eBay"
    if "marketplace" in s or "facebook" in s or " fb" in s:
        return "Facebook"
    return ""


def category_of(status):
    """The app splits rows into 'personal' and 'fb'. Keep that split."""
    return "personal" if (status or "").lower().startswith("personal") else "fb"


def read_rows():
    import openpyxl
    ws = openpyxl.load_workbook(XLSX, data_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    head = [as_text(c) for c in rows[0]]
    idx = {name: head.index(name) for name in FROM_XLSX if name in head}
    missing = [n for n in FROM_XLSX if n not in idx]
    out, batch, skipped = [], "", 0
    for r in rows[1:]:
        cell = [as_text(c) for c in r]
        num = cell[idx['#']] if '#' in idx else ""
        # A section header row carries a batch name in the # column and no cost.
        if num and not num.replace('.', '').isdigit():
            batch = num
            skipped += 1
            continue
        if not num:
            skipped += 1
            continue
        rec = {k: "" for k in HEADER}
        for xname, ours in FROM_XLSX.items():
            if xname in idx:
                rec[ours] = cell[idx[xname]]
        for d in ("Order date", "Sold date"):
            raw = r[idx[{'Order date': 'Order date', 'Sold date': 'Sold date'}[d]]] if d in FROM_XLSX.values() else None
            rec[d] = as_date(raw)
        rec['Batch'] = batch
        rec['Channel'] = channel_of(rec['Status'])
        rec['Category'] = category_of(rec['Status'])
        out.append([rec[h] for h in HEADER])
    return out, missing, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--csv", default="")
    a = ap.parse_args()

    rows, missing, skipped = read_rows()
    print(f"read {len(rows)} item rows from the spreadsheet "
          f"({skipped} header/blank rows skipped)")
    if missing:
        print("columns not found in the spreadsheet:", missing)
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(HEADER); w.writerows(rows)
        print("wrote", a.csv)
    if a.preview or not a.write:
        for r in rows[:3]:
            print("   ", r[:8])
        print("PREVIEW ONLY - nothing was sent to Google.")
        return

    import gspread
    from google.oauth2 import service_account
    creds = service_account.Credentials.from_service_account_file(
        KEY, scopes=["https://www.googleapis.com/auth/spreadsheets",
                     "https://www.googleapis.com/auth/drive.file"])
    sh = gspread.authorize(creds).open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(TAB)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(TAB, rows=len(rows) + 50, cols=len(HEADER))
    existing = ws.get_all_values()
    live = sum(1 for r in existing[1:] if any(x.strip() for x in r))
    if live:
        print(f"REFUSED: the Sales tab already holds {live} rows. "
              f"Clear it by hand first, or this would double everything up.")
        sys.exit(2)
    ws.update(values=[HEADER] + rows, range_name="A1")
    print(f"wrote {len(rows)} rows into '{TAB}'.")


if __name__ == "__main__":
    main()
