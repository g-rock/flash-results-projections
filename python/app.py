import os
import json
from tempfile import NamedTemporaryFile
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from google.cloud import storage, firestore

from pubsub_listener import PubSubManager
from processors import get_firestore_client, get_blob_json, process_merged_start_list

# -----------------------------
# Configuration & Clients
# -----------------------------
SERVICE_ACCOUNT_FILE = "GOOGLE_APPLICATION_CREDENTIALS.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE

# GCS & Firestore clients
gcs_client = storage.Client()
db_client = get_firestore_client(SERVICE_ACCOUNT_FILE)
BUCKET_NAME = "projections-data"

# Pub/Sub setup
# PROJECT_ID = "flash-results-projections"
# SUBSCRIPTION_MAP = {
#     # Explicit arguments: bucket_name and object_name will be passed from Pub/Sub
#     "merged_start_list_uploads_sub": lambda bucket, object_name: process_merged_start_list_file(
#         gcs_client=gcs_client,
#         db_client=db_client,
#         bucket_name=bucket,
#         object_name=object_name
#     )
# }
# pubsub_manager = PubSubManager(PROJECT_ID, SUBSCRIPTION_MAP)

# -----------------------------
# FastAPI app
# -----------------------------
origins = ["http://localhost:5173"]

app = FastAPI(
    title="Track Meet Processing API",
    version="1.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Lifecycle: Start Pub/Sub listeners
# -----------------------------
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     pubsub_manager.start_listeners()  # start threads
#     yield
#     print("FastAPI shutting down")

# app.router.lifespan_context = lifespan

# -----------------------------
# Endpoints
# -----------------------------

@app.post("/upload_merged_start_list")
async def upload_merged_start_list(file: UploadFile = File(...)):
    """Upload a CSV, clean it, and upload both raw + cleaned versions to GCS."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV")

    with NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        tmp_file.write(await file.read())
        tmp_file_path = tmp_file.name

    try:
        raw_blob_name = f"merged-start-lists/{file.filename}"
        raw_bucket = gcs_client.bucket(BUCKET_NAME)
        raw_bucket.blob(raw_blob_name).upload_from_filename(tmp_file_path)
        print(f"✅ Uploaded merged-start-list file to gs://{BUCKET_NAME}/{raw_blob_name}")

        df_cleaned = process_merged_start_list(tmp_file_path)

        with NamedTemporaryFile(delete=False, suffix=".csv") as out_file:
            print(df_cleaned)
            df_cleaned.to_csv(out_file.name, index=False)
            out_file_path = out_file.name

        cleaned_blob_name = f"cleaned-start-lists/{file.filename}"
        cleaned_bucket = gcs_client.bucket(BUCKET_NAME)
        cleaned_bucket.blob(cleaned_blob_name).upload_from_filename(out_file_path)
        print(f"✅ Uploaded cleaned file to gs://{BUCKET_NAME}/{cleaned_blob_name}")

    finally:
        os.remove(tmp_file_path)
        if "out_file_path" in locals() and os.path.exists(out_file_path):
            os.remove(out_file_path)

    return JSONResponse(
        content={
            "message": f"File '{file.filename}' uploaded and processed successfully.",
            "raw_file": f"gs://{BUCKET_NAME}/{raw_blob_name}",
            "cleaned_file": f"gs://{BUCKET_NAME}/{cleaned_blob_name}"
        }
    )

@app.get("/list_meets")
async def list_meets():
    """Return all meet names stored in Firestore."""
    try:
        docs = db_client.collection("meets").stream()
        meet_names = [doc.to_dict().get("meet_name") or doc.id for doc in docs]
        return {"meets": sorted(meet_names)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing meets: {str(e)}")


@app.delete("/delete_meet/{meet_name}")
async def delete_meet(meet_name: str):
    """Delete all files in GCS for a meet."""
    meet_name = meet_name.strip()
    if not meet_name:
        raise HTTPException(status_code=400, detail="meet_name must not be empty")

    try:
        blobs = list(gcs_client.list_blobs(bucket_name, prefix=f"{meet_name}/"))
        if not blobs:
            raise HTTPException(status_code=404, detail=f"No files found for meet '{meet_name}'")

        for blob in blobs:
            blob.delete()
            print(f"Deleted {blob.name}")

        return {"message": f"All files for meet '{meet_name}' have been deleted."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting meet: {str(e)}")


@app.get("/get_meet_data/{meet_name}/{data_type}")
def get_meet_data(meet_name: str, data_type: str):
    """Fetch processed meet data JSON from GCS."""
    blob_mapping = {
        "womenData": f"{meet_name}/womenData.json",
        "menData": f"{meet_name}/menData.json",
        "columnDefs.women": f"{meet_name}/columnDefs.women.json",
        "columnDefs.men": f"{meet_name}/columnDefs.men.json",
    }

    if data_type not in blob_mapping:
        raise HTTPException(status_code=400, detail=f"Invalid data_type: {data_type}")

    try:
        data = get_blob_json(gcs_client, bucket_name, blob_mapping[data_type])
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{data_type} not found for meet '{meet_name}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
