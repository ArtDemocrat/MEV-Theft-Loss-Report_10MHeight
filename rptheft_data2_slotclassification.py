"""
Script Goal: Clean, standardize, and enrich Ethereum slot-level CSV data as part of the Rocketpool MEV theft analysis project. It processes raw slot data files and produces cleaned, standardized CSV files that can be used for further analysis and visualization. Script: YYY

**What the Script Does**
- Reads raw CSV files from the SOURCE_PATH directory.
- Curates, classifies, and expands the slot information available in our datasources (see definitions in the section below).
- Exports processed data to the PROCESSED_PATH folder as new CSV files.

**Definitions Created in the Data Classification and Curation Process**
The dataset used in this analysis underwent a structured preparation and classification process to enable reliable downstream analysis. Specifically, the following data curation steps were applied:
- **Normalization of Ethereum Addresses**: All Ethereum addresses were standardized to lowercase to ensure consistency and avoid mismatches.
- **Relay Name Standardization**: Relay names were cleaned and mapped to standardized identifiers to consolidate different naming conventions used across our data sources.
- **Conversion of Values to ETH**: Key numerical fields, including transaction values, MEV rewards, and bids, originally recorded in wei units, were converted to ETH and rounded to eight decimal places.
- **Identification of Vanilla Blocks**: A classification column vanilla_block was added to flag slots without any recorded MEV rewards or fee recipients across our data sources.
- **MEV Theft Detection**: Two additional columns were created to flag slots that potentially exhibit MEV theft behavior:
  - sp_high-confidence_theft marks slots where the block proposer was part of the Rocketpool Smoothing Pool but no portion of the MEV reward was distributed to the smoothing pool contract address.
  - reg_high-confidence_theft marks slots outside the smoothing pool where the distributor address differs from all recorded MEV recipients across our data sources.
- Slot-level MEV Averaging: For contextual analysis, the average MEV bid for each slot was calculated based on two separate data sources (max_bid and mevmonitor_max_bid).
- All processed files were saved in a structured output folder and used as the standardized input for subsequent analyses (see sections below).
"""

import os
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='local_paths.env')
input_folder_path = os.getenv("SOURCE_PATH")
output_folder_path = os.getenv("PROCESSED_PATH")

# Ensure both folder paths are loaded
if not input_folder_path or not output_folder_path:
    raise ValueError("Please define LOCAL_PATH and PROCESSED_PATH in the .env file.")

print(f"Input folder path: {input_folder_path}")
print(f"Output folder path: {output_folder_path}")

# Ensure the output folder exists
os.makedirs(output_folder_path, exist_ok=True)

sp_address = "0xd4e96ef8eee8678dbff4d535e033ed1a4f7605b7".lower()

# Normalize Ethereum addresses
def normalize_address(addr):
    return addr.lower() if pd.notna(addr) else ""

# Flatten and normalize multiple addresses separated by ";"
def extract_normalized_addresses(column_value):
    if pd.notna(column_value):
        return [normalize_address(addr) for addr in column_value.split(";")]
    return []

# Convert specific columns from Wei to ETH and round to 8 decimals
def convert_wei_to_eth(df, columns, decimals=8):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].apply(lambda x: round(x / 10**18, decimals) if pd.notnull(x) else x)
    return df

# Standardize relay names
def standardize_relay_names(df, relay_columns):
    relay_map = {
        "Flashbots": "flashbots-relay",
        "bloXroute Max Profit": "bloxroute-max-profit-relay",
        "bloXroute Regulated": "bloxroute-regulated-relay",
        "Blocknative": "mainnet-relay.securerpc.com",
        "Eden Network": "relay.edennetwork.io",
        "Ultra Sound": "ultrasound-relay",
        "Aestus": "aestus-relay",
        "Titan Global": "agnostic-relay",
        "Titan Regional": "agnostic-relay",
        "bloxroute.max-profit.blxrbdn.com": "bloxroute-max-profit-relay",
        "boost-relay.flashbots.net": "flashbots-relay",
        "relay.ultrasound.money": "ultrasound-relay",
        "bloxroute.regulated.blxrbdn.com": "bloxroute-regulated-relay",
        "aestus.live": "aestus-relay",
        "mainnet-relay.securerpc.com": "mainnet-relay.securerpc.com",
        "relay.edennetwork.io": "relay.edennetwork.io",
        "agnostic-relay.net": "agnostic-relay"
    }

    for col in relay_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: ";".join([relay_map.get(r.strip(), r.strip()) for r in x.split(";")]) if pd.notna(x) else x)
    return df

# Function to identify vanilla blocks
def identify_vanilla_blocks(df):
    df['vanilla_block'] = df.apply(
        lambda row: "TRUE" if all(pd.isna(row[col]) for col in [
            'mev_reward', 'mev_reward_relay', 'relay_fee_recipient', 
            'beaconcha_mev_reward', 'beaconcha_mev_reward_relay', 
            'beaconcha_fee_recipient', 'mevmonitor_mev_reward', 
            'mevmonitor_mev_reward_relay'
        ]) else "", axis=1
    )
    return df

# Function to calculate the average MEV for 2 blocks before and after
def calculate_surrounding_mev(df, index):
    max_bid_values = df.loc[max(0, index-2):min(len(df)-1, index+2), ['max_bid', 'mevmonitor_max_bid']].mean().mean()
    return round(max_bid_values, 8) if pd.notna(max_bid_values) else 0

# Function to identify MEV theft
def identify_mev_theft(df):
    df['sp_high-confidence_theft'] = ""
    df['reg_high-confidence_theft'] = ""

    def check_theft_logging(row):
        recipient_columns = ['relay_fee_recipient', 'mevmonitor_fee_recipient', 'beaconcha_fee_recipient', 'last_tx_recipient']
        recipients = [addr for col in recipient_columns for addr in extract_normalized_addresses(row.get(col, ""))]
        distributor = normalize_address(row['distributor_address'])
        in_smoothing_pool = str(row['in_smoothing_pool']).strip().lower() == "true"

        #print(f"Slot: {row['slot']}")
        #print(f"In Smoothing Pool: {in_smoothing_pool}")
        #print(f"Distributor Address: {distributor if distributor else 'Empty'}")
        #print(f"Recipients: {recipients}")

        # Check smoothing pool theft
        if in_smoothing_pool:
            if all(sp_address not in recipient for recipient in recipients):
                row['sp_high-confidence_theft'] = "TRUE"
                print(f"Slot: {row['slot']}"+" - Smoothing Pool Theft: High Confidence")
        elif distributor:
            if all(distributor not in recipient for recipient in recipients):
                row['reg_high-confidence_theft'] = "TRUE"
                print(f"Slot: {row['slot']}"+" - Regular Theft: High Confidence")

        #print(f"Smoothing Pool Theft: {row['sp_high-confidence_theft']}")
        #print(f"Regular Theft: {row['reg_high-confidence_theft']}")
        #print("----")
        
        return row

    df = df.apply(check_theft_logging, axis=1)
    return df

# Process CSV files in the input folder and save to output folder
def process_csv_files(input_folder, output_folder):
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            input_file_path = os.path.join(input_folder, filename)
            print(f"Processing {filename}...")

            # Read CSV file into DataFrame
            df = pd.read_csv(input_file_path)

            # Process data (e.g., convert, standardize, identify vanilla blocks, identify theft, calculate missed MEV)
            # Convert from wei to ETH for specified columns
            wei_columns = [
                'last_tx_value', 'priority_fees', 'eth_collat_ratio',
                'max_bid', 'mev_reward', 'beaconcha_mev_reward',
                'mevmonitor_max_bid', 'mevmonitor_mev_reward'
            ]
            df = convert_wei_to_eth(df, wei_columns, decimals=8)

            # Standardize relay names
            relay_columns = [
                'max_bid_relay', 'mev_reward_relay',
                'beaconcha_mev_reward_relay', 'mevmonitor_max_bid_relay',
                'mevmonitor_mev_reward_relay'
            ]
            df = standardize_relay_names(df, relay_columns)

            # Identify vanilla blocks
            df = identify_vanilla_blocks(df)

            # Identify MEV theft
            df = identify_mev_theft(df)

            # Save the processed DataFrame to a new CSV file in the output folder
            output_file_path = os.path.join(output_folder, f"processed_{filename}")
            df.to_csv(output_file_path, index=False)
            print(f"Processed data saved to {output_file_path}\n")

# Main function
def main():
    process_csv_files(input_folder_path, output_folder_path)

if __name__ == "__main__":
    main()
