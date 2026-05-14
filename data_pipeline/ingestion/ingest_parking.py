import requests
import json
import os
# pyrefly: ignore [missing-import]
from google.cloud import storage
from datetime import datetime

BUCKET_NAME = os.getenv("BUCKET_NAME")
DATASET_ID = "e7h6-4a3e"
URL = f"https://data.lacity.org/resource/{DATASET_ID}.json"

def upload_gcs(data, filename):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"raw/{filename}")
    blob.upload_from_string(json.dumps(data), content_type='application/json')
    print(f"Uploaded {filename} to {BUCKET_NAME}")

def ingest_parking(limit=1000):
    p = {'$limit': limit, '$order': 'eventtime DESC'}
    res = requests.get(URL, params=p)
    if res.status_code != 200:
        print(f"Unable to connect to API. Status code: {res.status_code}")
        return None
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"parking_data_{timestamp}.json"
    upload_gcs(res.json(), filename)

ingest_parking()