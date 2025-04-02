"""
What the script does: plotting a cumulative distribution function ("CDF") for the maximum bids on all Ethereum slots (blue dots/line) and another one for RP blocks (orange dots/line). 
Generates CDF chart with this information. 
Besides creating a visual evaluation for each of the cohorts, it plots the Kolmogorov-Smirnov (K-S) and p-value statistical evaluation on the entire distribution.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import ks_2samp
from dotenv import load_dotenv
import warnings

# Suppress specific warnings for cleaner logs
warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

# Load environment variables for folder paths
load_dotenv(dotenv_path="local_paths.env")
folder_path = os.getenv("PROCESSED_PATH")

def combine_processed_files(folder_path):
    # List all matching files
    all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.startswith("processed_")]

    # Check if no files are found
    if not all_files:
        raise FileNotFoundError(f"No files found in the folder '{folder_path}' matching the expected pattern.")

    # Combine all files
    combined_df = pd.concat((pd.read_csv(file) for file in all_files), ignore_index=True)
    return combined_df

def clean_and_prepare_data(df):
    print(f"Step 1: Full dataset created: {df.shape[0]} rows, {df.shape[1]} columns")

    # Dropping rows with missing validator index
    initial_rows = df.shape[0]
    df = df.dropna(subset=['proposer_index'])
    print(f"Step 2: Dropped rows due to missed blocks (validator index empty): {initial_rows - df.shape[0]} rows")

    # Ensure numeric conversion
    df['max_bid'] = pd.to_numeric(df['max_bid'], errors='coerce')
    df['mevmonitor_max_bid'] = pd.to_numeric(df['mevmonitor_max_bid'], errors='coerce')

    # Calculate average or use single value when one is missing
    df['max_bid_eth'] = df[['max_bid', 'mevmonitor_max_bid']].mean(axis=1, skipna=True)

    # Dropping rows with missing max_bid_eth
    rows_after_proposer_index = df.shape[0]
    df = df.dropna(subset=['max_bid_eth'])
    print(f"Step 3: Dropped rows due to missing max_bid values: {rows_after_proposer_index - df.shape[0]} rows")

    # Standardize the `is_rocketpool` column
    rows_after_max_bid = df.shape[0]
    df['is_rocketpool'] = df['is_rocketpool'].astype(str).str.lower()
    df = df[df['is_rocketpool'].isin(['true', 'false'])]
    print(f"Step 4: Dropped rows due to invalid `is_rocketpool` values: {rows_after_max_bid - df.shape[0]} rows")

    print(f"Step 5: Final dataset size: {df.shape[0]} rows, {df.shape[1]} columns")
    return df

def calculate_cdf(data):
    sorted_data = np.sort(data)
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    return sorted_data, cdf

def plot_cdf(rocketpool_data, non_rocketpool_data, A, B):
    # Filter data within the range
    rocketpool_filtered = rocketpool_data[(rocketpool_data >= A) & (rocketpool_data <= B)]
    non_rocketpool_filtered = non_rocketpool_data[(non_rocketpool_data >= A) & (non_rocketpool_data <= B)]

    # Print summary statistics
    print(f"Total number of rows being plotted between {A:.2e} ETH and {B:.2e} ETH: {len(rocketpool_filtered) + len(non_rocketpool_filtered)}")
    print(f"Number of 'Is RocketPool: TRUE' datapoints: {len(rocketpool_filtered)}")
    print(f"Number of 'Is RocketPool: FALSE' datapoints: {len(non_rocketpool_filtered)}")

    # Calculate K-S statistic
    if len(rocketpool_filtered) > 0 and len(non_rocketpool_filtered) > 0:
        ks_stat, p_value = ks_2samp(rocketpool_filtered, non_rocketpool_filtered)
        print(f"K-S statistic: {ks_stat:.4f}")
        print(f"p-value: {p_value:.4e}")
    else:
        print("Not enough data points for K-S test.")

    # Calculate CDF
    rocketpool_values, rocketpool_cdf = calculate_cdf(rocketpool_filtered)
    non_rocketpool_values, non_rocketpool_cdf = calculate_cdf(non_rocketpool_filtered)

    # Plot the CDF
    plt.figure(figsize=(10, 6))
    plt.loglog(non_rocketpool_values, non_rocketpool_cdf, 'o-', label='Is RocketPool: FALSE', linewidth=0.5, markersize=3)
    plt.loglog(rocketpool_values, rocketpool_cdf, 'o-', label='Is RocketPool: TRUE', linewidth=1, markersize=2)

    plt.xlabel('Max Bid Value (in ETH)')
    plt.ylabel('Proportion of Slots with at least X Axis Max Bid')
    plt.title('Cumulative Distribution of Max Bid Values')
    plt.grid(which='major', linestyle='-', linewidth=0.5)
    plt.legend()
    plt.show()

def main():
    # Combine all processed files
    combined_df = combine_processed_files(folder_path)

    # Clean and prepare data
    combined_df = clean_and_prepare_data(combined_df)

    # Separate RocketPool and non-RocketPool data
    rocketpool_data = combined_df[combined_df['is_rocketpool'] == "true"]['max_bid_eth']
    non_rocketpool_data = combined_df[combined_df['is_rocketpool'] == "false"]['max_bid_eth']

    # Define X-axis limits
    A = 10**-5  # Lower limit (e.g., 0.01 ETH)
    B = 10**5   # Upper limit (e.g., 1000 ETH)

    # Plot CDF
    plot_cdf(rocketpool_data, non_rocketpool_data, A, B)

if __name__ == "__main__":
    main()
