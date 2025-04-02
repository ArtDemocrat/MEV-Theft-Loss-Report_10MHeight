"""
What the script does: Slot Dataset Integrity & Quality Checks. 
It validates the completeness and data quality of the Ethereum slot-level dataset used in the Rocketpool MEV theft analysis project. 
It performs structural and continuity checks on all raw .csv files to ensure slot coverage, data quality, and integrity across millions of slot entries.
"""

import os
import pandas as pd
import numpy as np
import gzip
from tabulate import tabulate

# === CONFIGURATION ===
from dotenv import load_dotenv
load_dotenv(dotenv_path='local_paths.env')
DATA_FOLDER = os.getenv("SOURCE_PATH")
EXPECTED_SLOT_RANGE = (5203000, 9899999)
MIN_EXPECTED_FILE_SIZE_MB = 40  # adjust if needed

# === CORE FUNCTIONS ===

def read_csv_file(filepath):
    try:
        if filepath.endswith(".gz"):
            with gzip.open(filepath, 'rt') as f:
                df = pd.read_csv(f)
        else:
            df = pd.read_csv(filepath)
        return df
    except Exception as e:
        print(f"❗️ Could not read {os.path.basename(filepath)}: {e}")
        return None

def check_file_size(filepath):
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    return size_mb

def validate_slot_column(df, filename):
    non_numeric = df[~df['slot'].apply(lambda x: str(x).isdigit())]
    if not non_numeric.empty:
        print(f"⚠️ File {filename} has non-numeric slot entries: {non_numeric['slot'].tolist()[:5]} ...")
    return len(non_numeric)

def main():
    all_files = [os.path.join(DATA_FOLDER, f) for f in os.listdir(DATA_FOLDER) if f.endswith((".csv", ".csv.gz"))]
    if not all_files:
        print("❗️ No CSV or CSV.GZ files found.")
        return

    print(f"🔍 Found {len(all_files)} data files. Starting checks...\n")

    global_slot_set = set()
    duplicate_slots = []
    broken_files = []
    report_rows = []

    for file in sorted(all_files):
        filename = os.path.basename(file)
        file_size = check_file_size(file)

        # File size check
        size_anomaly = file_size < MIN_EXPECTED_FILE_SIZE_MB

        # Try reading
        df = read_csv_file(file)
        if df is None or "slot" not in df.columns:
            broken_files.append(filename)
            continue

        row_count = df.shape[0]

        # Slot format check
        non_numeric_count = validate_slot_column(df, filename)

        # Slot range in file
        min_slot = int(df['slot'].min()) if not df['slot'].isnull().all() else "N/A"
        max_slot = int(df['slot'].max()) if not df['slot'].isnull().all() else "N/A"

        # Duplicates check
        slot_counts = df['slot'].value_counts()
        duplicates = slot_counts[slot_counts > 1].index.tolist()
        duplicate_slots.extend(duplicates)

        # Global slot range accumulation
        global_slot_set.update(df['slot'].tolist())

        report_rows.append([
            filename,
            f"{row_count:,}",
            f"{file_size:.2f} MB",
            "⚠️ Yes" if size_anomaly else "✅ No",
            min_slot,
            max_slot,
            non_numeric_count
        ])

    # === Summary Section ===

    print("\n📄 **Per File Report:**\n")
    headers = ["File", "Row Count", "Size", "Size Anomaly", "Min Slot", "Max Slot", "Non-Numeric Slots"]
    print(tabulate(report_rows, headers=headers, tablefmt="github"))

    # Global Slot Range Check
    expected_slots = set(range(EXPECTED_SLOT_RANGE[0], EXPECTED_SLOT_RANGE[1] + 1))
    missing_slots = sorted(list(expected_slots - global_slot_set))

    print("\n📌 **Summary Report:**\n")
    print(f"🔸 Total Files Checked: {len(all_files)}")
    print(f"🔸 Broken / unreadable files: {len(broken_files)}")
    print(f"🔸 Total unique slots: {len(global_slot_set):,}")
    print(f"🔸 Expected slots: {EXPECTED_SLOT_RANGE[0]} to {EXPECTED_SLOT_RANGE[1]} ({len(expected_slots):,} slots)")
    print(f"🔸 Missing slots: {len(missing_slots):,}")
    print(f"🔸 Duplicate slots across files: {len(duplicate_slots):,}\n")

    if missing_slots:
        print(f"⚠️ Missing slot range examples: {missing_slots[:5]} ... {missing_slots[-5:]}")
    if duplicate_slots:
        print(f"⚠️ Duplicate slot examples: {duplicate_slots[:5]}")

    if broken_files:
        print(f"❗️ Broken files: {broken_files}")

if __name__ == "__main__":
    main()
