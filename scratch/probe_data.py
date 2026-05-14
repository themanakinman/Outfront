import duckdb
import os
import subprocess

print("--- Fetching a sample Parquet file using gcloud ---")
gcs_path = "gs://parking-data-lake-v1/processed/db/enriched_occupancy/data/*.parquet"
local_path = "/tmp/sample_occupancy.parquet"

try:
    # Get the list of parquet files
    res = subprocess.run(["gcloud", "storage", "ls", gcs_path], capture_output=True, text=True, check=True)
    files = [f for f in res.stdout.split('\n') if f.endswith('.parquet')]
    
    if not files:
        print("No parquet files found!")
        exit(1)
        
    sample_file = files[0]
    print(f"Downloading {sample_file} to {local_path}...")
    
    # Download the first one
    subprocess.run(["gcloud", "storage", "cp", sample_file, local_path], check=True, stdout=subprocess.DEVNULL)
    
except Exception as e:
    print(f"Failed to download using gcloud: {e}")
    exit(1)


print("\n--- Probing Schema ---")
con = duckdb.connect()

try:
    print(con.execute(f"DESCRIBE SELECT * FROM read_parquet('{local_path}')").df())
    
    print("\n--- Sample Data (First 5 rows) ---")
    print(con.execute(f"SELECT * FROM read_parquet('{local_path}') LIMIT 5").df())
except Exception as e:
    print(f"DuckDB Error: {e}")
finally:
    # Cleanup
    if os.path.exists(local_path):
        os.remove(local_path)

