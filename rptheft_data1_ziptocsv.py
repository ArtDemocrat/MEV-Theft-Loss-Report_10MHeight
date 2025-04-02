import os
import gzip
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='local_paths.env')
parent_folder = os.getenv("SOURCE_PATH")

def extract_gz_files(folder_path):
    extracted_count = 0
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv.gz'):
            gz_path = os.path.join(folder_path, filename)
            csv_filename = filename.replace('.csv.gz', '.csv')
            csv_path = os.path.join(folder_path, csv_filename)
            # Skip if already extracted
            if os.path.exists(csv_path):
                continue
            with gzip.open(gz_path, 'rb') as f_in:
                with open(csv_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            extracted_count += 1
            print(f"✅ Extracted: {filename} → {csv_filename}")
    print(f"\n🎯 Extraction complete. {extracted_count} CSV files extracted to: {folder_path}")

if __name__ == "__main__":
    extract_gz_files(parent_folder)
