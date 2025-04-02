"""
What the script does: Plots in a scater chart the cases (split by SP and Opt-out Operators) where theft happened.
Generates summary table with all theft cases (i.e. misusage of protocol-defined fee recipients), split by those which did receive an MEV reward (outright theft) and those where the MEV Rward = 0 (no theft, but incurred in fee distributor misusage).
Plots 2 tables listing 1) all of the SP-related theft slots and rewards stolen and 2) all of the Opt-out Operators theft slots and rewards stolen.
Lists all the node operator addresses which incurred in MEV theft, the number of events where it happened, and the ETH amount stolen as well as the % of the total ETH theft.
Counts the number of slots where MEV rewards were sent to the rETH contract, and the ETH amounts related to those events.
"""

import os
import pandas as pd
from dotenv import load_dotenv
from tabulate import tabulate
import matplotlib.pyplot as plt

# === CONFIG ===
load_dotenv(dotenv_path='local_paths.env')
folder_path = os.getenv("PROCESSED_PATH")
print(f"Loaded folder path: {folder_path}")

# === FUNCTIONS ===

def combine_processed_files(folder_path):
    all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.startswith("processed_")]
    if not all_files:
        raise FileNotFoundError(f"No files found in {folder_path}")
    return pd.concat((pd.read_csv(file) for file in all_files), ignore_index=True)

def preprocess_columns(df):
    for col in ['mev_reward', 'beaconcha_mev_reward', 'mevmonitor_mev_reward', 'max_bid', 'mevmonitor_max_bid']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    for col in ['sp_high-confidence_theft', 'reg_high-confidence_theft']:
        df[col] = df[col].astype(str).str.lower()
    return df

def calculate_metrics(df):
    df['average_mev_reward'] = df[['mev_reward', 'beaconcha_mev_reward', 'mevmonitor_mev_reward']].mean(axis=1)
    df['average_max_bid'] = df[['max_bid', 'mevmonitor_max_bid']].mean(axis=1)
    return df

def theft_summary(df):
    summary_rows = []

    for theft_col, label in [('sp_high-confidence_theft', 'Smoothing Pool Theft'),
                             ('reg_high-confidence_theft', 'Regular Theft')]:
        flagged = df[df[theft_col] == "true"]
        reward_zero = flagged[flagged['average_mev_reward'] == 0]
        reward_nonzero = flagged[flagged['average_mev_reward'] > 0]

        total_flagged = flagged.shape[0]
        reward_zero_count = reward_zero.shape[0]
        reward_nonzero_count = reward_nonzero.shape[0]
        reward_zero_pct = (reward_zero_count / total_flagged) * 100 if total_flagged > 0 else 0
        reward_nonzero_pct = (reward_nonzero_count / total_flagged) * 100 if total_flagged > 0 else 0

        sum_mev_reward = reward_nonzero['average_mev_reward'].sum()
        sum_estimated_missed = reward_zero['average_max_bid'].sum()

        summary_rows.append({
            "Theft Type": label,
            "Total Flagged": f"{total_flagged:,}",
            "Reward = 0": f"{reward_zero_count:,} ({reward_zero_pct:.2f}%)",
            "Reward > 0": f"{reward_nonzero_count:,} ({reward_nonzero_pct:.2f}%)",
            "Sum of MEV Reward (ETH)": f"{sum_mev_reward:.4f}",
            "Estimated Missed Revenue (ETH)": f"{sum_estimated_missed:.4f}"
        })

    print("\n📄 **Theft Summary:**\n")
    print(tabulate(summary_rows, headers="keys", tablefmt="github"))

def display_full_theft_tables(df):
    print("\n🔍 FULL Theft Tables (Only rows with MEV Reward > 0):\n")

    for theft_col, label in [('sp_high-confidence_theft', 'Smoothing Pool Theft'),
                             ('reg_high-confidence_theft', 'Regular Theft')]:
        filtered = df[(df[theft_col] == "true") & (df['average_mev_reward'] > 0)]
        filtered = filtered[['slot', 'average_mev_reward']].reset_index(drop=True)
        filtered['slot'] = filtered['slot'].astype(int)
        filtered['average_mev_reward'] = filtered['average_mev_reward'].map(lambda x: f"{x:.4f}")

        print(f"\n🧾 {label} Events (Count: {filtered.shape[0]}):")
        print(tabulate(filtered, headers='keys', tablefmt='github'))

def plot_mev_theft(df):
    smoothing_pool = df[(df['sp_high-confidence_theft'] == "true") & (df['average_mev_reward'] > 0)]
    regular_theft = df[(df['reg_high-confidence_theft'] == "true") & (df['average_mev_reward'] > 0)]

    plt.figure(figsize=(12, 8))
    plt.scatter(smoothing_pool['slot'], smoothing_pool['average_mev_reward'],
                label="In Smoothing Pool: TRUE", color="orange", alpha=0.8)
    plt.scatter(regular_theft['slot'], regular_theft['average_mev_reward'],
                label="In Smoothing Pool: FALSE", color="blue", alpha=0.8)

    plt.title("Stolen MEV Reward per Slot by Smoothing Pool Status")
    plt.xlabel("Slot")
    plt.ylabel("MEV Reward (in ETH)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

def node_address_summary(df):
    print("\n📄 **Node Address Summary (MEV Reward > 0, RocketPool Slots, All Theft Types):**\n")

    # Filter only Rocketpool slots with theft flagged and MEV reward > 0
    theft_rows = df[
        (df['is_rocketpool'].astype(str).str.lower() == "true") &
        (
            (df['sp_high-confidence_theft'] == "true") |
            (df['reg_high-confidence_theft'] == "true")
        ) &
        (df['average_mev_reward'] > 0)
    ]

    if theft_rows.empty:
        print("⚠️ No theft events with MEV reward > 0 detected in RocketPool slots.\n")
        return

    # Group by node_address and calculate summary
    node_summary = theft_rows.groupby('node_address').agg(
        theft_events=('slot', 'count'),
        total_mev_reward=('average_mev_reward', 'sum')
    ).reset_index()

    # Calculate percentage
    total_events = node_summary['theft_events'].sum()
    node_summary['% of total theft'] = (node_summary['theft_events'] / total_events * 100).round(2)

    # Sort by number of theft events descending
    node_summary = node_summary.sort_values(by='theft_events', ascending=False)

    # Formatting for CLI
    node_summary['theft_events'] = node_summary['theft_events'].map('{:,}'.format)
    node_summary['total_mev_reward'] = node_summary['total_mev_reward'].map('{:,.4f}'.format)
    node_summary['% of total theft'] = node_summary['% of total theft'].map('{:.2f}%'.format)

    # Display
    print(tabulate(node_summary, headers='keys', tablefmt='github'))

def reth_contract_summary(df):
    reth_address = "0x33894ea0c25295cb48068019d999a9e190540bf7"  # lowercase

    recipient_columns = [
        'relay_fee_recipient',
        'mevmonitor_fee_recipient',
        'beaconcha_fee_recipient',
        'last_tx_recipient'
    ]

    # Create a boolean mask across all recipient columns
    mask = pd.Series(False, index=df.index)
    for col in recipient_columns:
        if col in df.columns:
            mask = mask | df[col].fillna("").str.lower().str.contains(reth_address)

    # Get count & sum of MEV reward
    count = mask.sum()
    total_mev = df.loc[mask, 'average_mev_reward'].sum()

    print(f"\n🚀 **rETH Contract Summary:**")
    print(f"🔸 Slots where MEV sent to rETH contract: {count:,}")
    print(f"🔸 Total MEV Reward sent to rETH contract: {total_mev:.4f} ETH")


# === MAIN ===

def main():
    df = combine_processed_files(folder_path)
    df = preprocess_columns(df)
    df = calculate_metrics(df)
    theft_summary(df)
    display_full_theft_tables(df)
    plot_mev_theft(df)
    node_address_summary(df)
    reth_contract_summary(df)

if __name__ == "__main__":
    main()
