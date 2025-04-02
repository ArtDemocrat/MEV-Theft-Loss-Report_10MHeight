"""
What the script does: runs statistical analysis for the maximum bids on all Ethereum slots (blue dots/line) and another one for RP blocks (orange dots/line). 
Creates a table for different MEV reward sizes/ranges, and it summaries the Kolmogorov-Smirnov (K-S) and p-value statistical evaluation on each distribution.
"""

import os
import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
from dotenv import load_dotenv
from tabulate import tabulate
import warnings

# Suppress specific warnings for cleaner logs
warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

# Load environment variables for folder paths
load_dotenv(dotenv_path="local_paths.env")
folder_path = os.getenv("PROCESSED_PATH")

def combine_processed_files(folder_path):
    all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.startswith("processed_")]
    if not all_files:
        raise FileNotFoundError(f"No files found in the folder '{folder_path}' matching the expected pattern.")
    return pd.concat((pd.read_csv(file) for file in all_files), ignore_index=True)

def clean_and_prepare_data(df):
    print(f"Step 1: Full dataset created: {df.shape[0]} rows, {df.shape[1]} columns")

    # Add `max_bid_eth` column before filtering
    df['max_bid'] = pd.to_numeric(df['max_bid'], errors='coerce')
    df['mevmonitor_max_bid'] = pd.to_numeric(df['mevmonitor_max_bid'], errors='coerce')
    df['max_bid_eth'] = df[['max_bid', 'mevmonitor_max_bid']].mean(axis=1, skipna=True)

    # Identify rows with no max bid or missed blocks
    no_max_bid_or_missed = df[(df['proposer_index'].isna()) | (df['max_bid'].isna() & df['mevmonitor_max_bid'].isna())]
    df_cleaned = df.drop(no_max_bid_or_missed.index)

    print(f"Step 2: Dropped rows with no max bid or missed blocks: {no_max_bid_or_missed.shape[0]} rows")

    # Standardize the `is_rocketpool` column
    df_cleaned['is_rocketpool'] = df_cleaned['is_rocketpool'].astype(str).str.lower()
    invalid_rp_rows = (~df_cleaned['is_rocketpool'].isin(['true', 'false'])).sum()
    df_cleaned = df_cleaned[df_cleaned['is_rocketpool'].isin(['true', 'false'])]
    print(f"Step 3: Dropped rows due to invalid `is_rocketpool` values: {invalid_rp_rows} rows")

    print(f"Step 4: Final dataset size: {df_cleaned.shape[0]} rows, {df_cleaned.shape[1]} columns")
    return df_cleaned

def calculate_metrics(cleaned_df, ranges):
    metrics = []

    for lower, upper in ranges:
        range_filter = (cleaned_df['max_bid_eth'] >= lower) & (cleaned_df['max_bid_eth'] < upper)
        range_cleaned_df = cleaned_df[range_filter]

        total_slots = range_cleaned_df.shape[0]
        rp_slots = range_cleaned_df[range_cleaned_df['is_rocketpool'] == "true"].shape[0]
        non_rp_slots = range_cleaned_df[range_cleaned_df['is_rocketpool'] == "false"].shape[0]

        # K-S test
        if rp_slots > 0 and non_rp_slots > 0:
            ks_stat, p_value = ks_2samp(
                range_cleaned_df[range_cleaned_df['is_rocketpool'] == "true"]['max_bid_eth'],
                range_cleaned_df[range_cleaned_df['is_rocketpool'] == "false"]['max_bid_eth'],
            )
            ks_stat = f":{'warning:' if ks_stat > 0.05 else 'white_check_mark:'} {ks_stat:.10f}"
            p_value = f":{'white_check_mark:' if p_value > 0.05 else 'warning:'} {p_value:.10f}"
        else:
            ks_stat = "-"
            p_value = "-"

        metrics.append({
            "Range": f"{lower}-{upper} ETH" if upper != float('inf') else f">{lower} ETH",
            "# of Slots": total_slots,
            "# of RP Slots": rp_slots,
            "# of non-RP Slots": non_rp_slots,
            "K-S statistic": ks_stat,
            "p-value": p_value,
        })

    # Add totals
    total_rp = cleaned_df[cleaned_df['is_rocketpool'] == "true"]
    total_non_rp = cleaned_df[cleaned_df['is_rocketpool'] == "false"]

    if not total_rp.empty and not total_non_rp.empty:
        ks_stat, p_value = ks_2samp(
            total_rp['max_bid_eth'],
            total_non_rp['max_bid_eth'],
        )
        ks_stat = f":{'warning:' if ks_stat > 0.05 else 'white_check_mark:'} {ks_stat:.10f}"
        p_value = f":{'white_check_mark:' if p_value > 0.05 else 'warning:'} {p_value:.10f}"
    else:
        ks_stat = "-"
        p_value = "-"

    metrics.append({
        "Range": "Total",
        "# of Slots": cleaned_df.shape[0],
        "# of RP Slots": total_rp.shape[0],
        "# of non-RP Slots": total_non_rp.shape[0],
        "K-S statistic": ks_stat,
        "p-value": p_value,
    })
    return metrics

def main():
    original_df = combine_processed_files(folder_path)
    cleaned_df = clean_and_prepare_data(original_df)

    ranges = [(0, 0.01), (0.01, 0.1), (0.1, 1), (1, 10), (10, float('inf'))]
    metrics = calculate_metrics(cleaned_df, ranges)

    print(tabulate(metrics, headers="keys", tablefmt="github"))

if __name__ == "__main__":
    main()
