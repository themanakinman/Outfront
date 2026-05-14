import requests
import json
import os
# pyrefly: ignore [missing-import]
from google.cloud import storage

BUCKET_NAME = os.getenv("BUCKET_NAME", "parking-data-lake-v1")
DATASET_ID = "s49e-q6j2"
URL = f"https://data.lacity.org/resource/{DATASET_ID}.json"

def upload_gcs(data, filename):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"static/{filename}")
    blob.upload_from_string(json.dumps(data), content_type='application/json')
    print(f"Uploaded {filename} to {BUCKET_NAME}/static/")

def ingest_inventory(): # parking meter inventory, geocoded locations, on-street, etc.

    params = {'$limit': 50000}
    res = requests.get(URL, params=params)
    
    if res.status_code != 200:
        print(f"Error fetching inventory: {res.status_code}")
        return
        
    upload_gcs(res.json(), "meter_inventory.json")

if __name__ == "__main__":
    ingest_inventory()
