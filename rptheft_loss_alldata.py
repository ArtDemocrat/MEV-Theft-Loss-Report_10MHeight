"""
What the script does: Counts and quantifies (in ETH terms) all vanilla blocks, split by smoothing pool and non-opt in blocks, and calculates rations out of all RP blocks which receive MEV bids.
Quantifies vanilla block incidence in smoothing pool vs non-smoothing pool blocks.
Quantifies the "bid gap" opportunity out of receiving MEV offers lower than the max bid registered from a relayer.
Quantifies vanilla block incidence in Rocket Pool vs all Non-Rocketpool blocks.
Lists top 20 node operators ranked by ETH loss related to processing vanilla blocks.
Lists top 20 node operators ranked by ETH loss related to not accepting the max bid available for a slot.
Plots a scatter chart with all vanilla blocks, split by smoothing pool vs non-smoothing pool blocks.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from tabulate import tabulate
import warnings

# === CONFIG ===
warnings.filterwarnings("ignore")
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
    df['is_rocketpool'] = df['is_rocketpool'].astype(str).str.lower()
    df['vanilla_block'] = df['vanilla_block'].astype(str).str.upper()
    return df

def calculate_metrics(df):
    df['average_mev_reward'] = df[['mev_reward', 'beaconcha_mev_reward', 'mevmonitor_mev_reward']].mean(axis=1)
    df['average_max_bid'] = df[['max_bid', 'mevmonitor_max_bid']].mean(axis=1)
    return df

def vanilla_block_summary(df):
    # Filter only RP slots with at least one max bid
    rp_slots = df[(df['is_rocketpool'] == "true") & (df[['max_bid', 'mevmonitor_max_bid']].sum(axis=1) > 0)]
    total_rp_slots = rp_slots.shape[0]

    # Vanilla blocks strict logic
    vanilla_blocks = rp_slots[rp_slots['vanilla_block'] == "TRUE"]
    total_vanilla = vanilla_blocks.shape[0]

    sp_vanilla = vanilla_blocks[rp_slots['in_smoothing_pool'] == True]
    non_sp_vanilla = vanilla_blocks[rp_slots['in_smoothing_pool'] == False]

    sp_loss = sp_vanilla['average_max_bid'].sum()
    non_sp_loss = non_sp_vanilla['average_max_bid'].sum()

    sp_pct = (sp_vanilla.shape[0] / total_rp_slots) * 100
    non_sp_pct = (non_sp_vanilla.shape[0] / total_rp_slots) * 100

    total_rewards = rp_slots['average_mev_reward'].sum()
    total_max = rp_slots['average_max_bid'].sum()
    missed_opportunity = total_max - total_rewards

    print("\n📄 **Vanilla Block Summary (Strict Logic, Max Bid Slots Only):**\n")
    print(f"Total RP Slots with max bid: {total_rp_slots:,}")
    print(f"Number of RP Vanilla Blocks: {total_vanilla:,}")
    print(f" - In Smoothing Pool: {sp_vanilla.shape[0]:,}")
    print(f" - Not in Smoothing Pool: {non_sp_vanilla.shape[0]:,}")
    print(f"Total ETH neglect in smoothing pool: {sp_loss:.4f} ETH")
    print(f"Total ETH neglect outside smoothing pool: {non_sp_loss:.4f} ETH")
    print(f"% of MEV-neglect slots within smoothing pool: {sp_pct:.2f}%")
    print(f"% of MEV-neglect slots outside smoothing pool: {non_sp_pct:.2f}%\n")
    print(f"Total ETH rewards accepted by RP validators: {total_rewards:.4f} ETH")
    print(f"Total ETH rewards offered to RP validators: {total_max:.4f} ETH")
    print(f"Total missed opportunity (MEV reward gap): {missed_opportunity:.4f} ETH")

    return vanilla_blocks

def additional_summary(df, vanilla_blocks):
    rp_total = df[(df['is_rocketpool'] == "true") & (df[['max_bid', 'mevmonitor_max_bid']].sum(axis=1) > 0)]
    rp_vanilla = vanilla_blocks
    rp_pct = (rp_vanilla.shape[0] / rp_total.shape[0]) * 100

    non_rp = df[(df['is_rocketpool'] == "false") & (df['proposer_index'].notnull()) & (df[['max_bid', 'mevmonitor_max_bid']].sum(axis=1) > 0)]
    non_rp_vanilla = non_rp[non_rp['vanilla_block'] == "TRUE"]
    non_rp_pct = (non_rp_vanilla.shape[0] / non_rp.shape[0]) * 100

    print("\n📄 **Vanilla Block % Summary (Max Bid Slots Only):**\n")
    print(f"Rocketpool Vanilla Block %: {rp_pct:.2f}% ({rp_vanilla.shape[0]} out of {rp_total.shape[0]} slots)")
    print(f"Non-Rocketpool Vanilla Block %: {non_rp_pct:.2f}% ({non_rp_vanilla.shape[0]} out of {non_rp.shape[0]} slots)")

def top_vanilla_loss(df, vanilla_blocks):
    node_summary = vanilla_blocks.groupby('node_address').agg(
        vanilla_block_count=('slot', 'count'),
        eth_mev_loss=('average_max_bid', 'sum')
    ).sort_values(by='eth_mev_loss', ascending=False).head(20)

    total_loss = node_summary['eth_mev_loss'].sum()
    node_summary['% of total loss'] = (node_summary['eth_mev_loss'] / total_loss * 100).map(lambda x: f"{x:.2f}%")
    node_summary.reset_index(inplace=True)

    print("\n📄 **Top 20 Node Operators (Vanilla Block Losses):**\n")
    print(tabulate(node_summary, headers='keys', tablefmt='github'))

def top_bid_gap_loss(df):
    rp = df[(df['is_rocketpool'] == "true") & (df[['max_bid', 'mevmonitor_max_bid']].sum(axis=1) > 0)]
    bid_gap = rp[rp['average_mev_reward'] > 0].copy()
    bid_gap['gap'] = bid_gap['average_max_bid'] - bid_gap['average_mev_reward']
    bid_gap = bid_gap[bid_gap['gap'] > 0]

    node_summary = bid_gap.groupby('node_address').agg(
        blocks_with_gap=('slot', 'count'),
        eth_gap_to_maxbid=('gap', 'sum')
    ).sort_values(by='eth_gap_to_maxbid', ascending=False).head(20)

    total_loss = node_summary['eth_gap_to_maxbid'].sum()
    node_summary['% of total loss'] = (node_summary['eth_gap_to_maxbid'] / total_loss * 100).map(lambda x: f"{x:.2f}%")
    node_summary.reset_index(inplace=True)

    print("\n📄 **Top 20 Node Operators (Bid Gap Losses):**\n")
    print(tabulate(node_summary, headers='keys', tablefmt='github'))

def plot_vanilla_blocks(vanilla_blocks):
    print("\n📊 Generating Vanilla Block Scatter Plot...")

    smoothing_pool = vanilla_blocks[vanilla_blocks['in_smoothing_pool'] == True]
    non_smoothing_pool = vanilla_blocks[vanilla_blocks['in_smoothing_pool'] == False]

    plt.figure(figsize=(16, 6))
    plt.scatter(non_smoothing_pool['slot'], non_smoothing_pool['average_max_bid'],
                label="In Smoothing Pool: False", color='blue', alpha=0.7, s=10)
    plt.scatter(smoothing_pool['slot'], smoothing_pool['average_max_bid'],
                label="In Smoothing Pool: True", color='orange', alpha=0.7, s=10)

    plt.title("Neglected MEV Reward per Slot by Smoothing Pool Status (Slots with Max Bid)")
    plt.xlabel("Slot")
    plt.ylabel("MEV Reward (in ETH)")
    plt.yscale("log")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

# === MAIN ===

def main():
    df = combine_processed_files(folder_path)
    df = preprocess_columns(df)
    df = calculate_metrics(df)

    vanilla_blocks = vanilla_block_summary(df)
    additional_summary(df, vanilla_blocks)
    top_vanilla_loss(df, vanilla_blocks)
    top_bid_gap_loss(df)
    plot_vanilla_blocks(vanilla_blocks)

if __name__ == "__main__":
    main()
