import os
import re
import pandas as pd
from google.cloud import storage
from google.cloud import firestore
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = "GOOGLE_APPLICATION_CREDENTIALS.json"

def slugify(text: str) -> str:
    """Generate a slug from a string."""
    text = text.lower().strip()
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_|]+', '-', text)
    # Remove all non-alphanumeric and non-hyphen characters
    text = re.sub(r'[^a-z0-9-]', '', text)
    return text


def get_firestore_client():
    """
    Returns a Firestore client. 
    
    If service_account_path is provided, uses that key.
    Otherwise, uses default credentials (e.g., Cloud Run / GCP environment).
    """
    if os.path.isfile(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
        return firestore.Client(credentials=creds, project=creds.project_id)
    else:
        # Use default credentials (works on GCP)
        return firestore.Client()
    

def get_gcs_client():
    """
    Returns a Google Cloud client. 
    """
    if os.path.isfile(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
        return storage.Client(credentials=creds, project=creds.project_id)
    else:
        # Use default credentials (works on GCP)
        return storage.Client()
    

def upload_file_to_gcs(client, bucket_name, local_file_path, blob_name):
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_file_path)
    print(f"Uploaded '{blob_name}' to bucket '{bucket_name}'.")

def parse_time_or_distance(seed_value):
    if pd.isna(seed_value) or not isinstance(seed_value, str):
        return None
    seed_str = seed_value.strip().lower()
    if ':' in seed_str:
        parts = seed_str.split(':')
        try:
            return float(parts[0]) * 60 + float(parts[1])
        except ValueError:
            return None
    if 'm' in seed_str or 'ft' in seed_str or '&frac' in seed_str:
        numeric_str = re.sub(r'[^\d\.\-]', '', seed_str)
        try:
            return float(numeric_str)
        except ValueError:
            return None
    try:
        return float(seed_str)
    except ValueError:
        return None