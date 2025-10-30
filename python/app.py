import os
from tempfile import NamedTemporaryFile
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from processors.startlist import process_merged_start_list
from processors.event import process_event
from processors.gcs import slugify, get_gcs_client

# GCS & Firestore clients
BUCKET_NAME = "projections-data"

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
# Endpoints
# -----------------------------

@app.post("/upload_merged_start_list")
async def upload_merged_start_list(
  meet_name: str = Form(...),
  file: UploadFile = File(...)
):
  """Upload a CSV, clean it, and upload both raw + cleaned versions to GCS."""
  meet_name = meet_name.strip()
  if not meet_name:
      raise HTTPException(status_code=400, detail="meet_name must not be empty")
  
  meet_id = slugify(meet_name)
  meet_year = datetime.now().year

  if not file.filename.endswith(".csv"):
      raise HTTPException(status_code=400, detail="file must be a CSV")

  with NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
    tmp_file.write(await file.read())
    tmp_file_path = tmp_file.name

  try:
    process_merged_start_list(
      file_path=tmp_file_path,
      meet_year=meet_year, 
      meet_id=meet_id,
      meet_name=meet_name
    )

    raw_blob_name = f"merged-start-lists/{meet_year}/{meet_id}"
    raw_bucket = get_gcs_client().bucket(BUCKET_NAME)
    raw_bucket.blob(raw_blob_name).upload_from_filename(tmp_file_path)
    print(f"✅ Uploaded raw start list file to gs://{BUCKET_NAME}/{raw_blob_name}")

  finally:
    os.remove(tmp_file_path)

  return JSONResponse(
    content={
        "message": f"File '{file.filename}' uploaded and processed to database successfully.",
        "merged_start_list_file": f"gs://{BUCKET_NAME}/{raw_blob_name}"
    }
  )


@app.post("/upload_event")
async def upload_event(
    file: UploadFile = File(...)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="file must be a CSV")
    
    # Check for forbidden substring in filename
    if "splits" in file.filename.lower():
        raise HTTPException(status_code=400, detail='filename cannot contain "splits"')
    
    meet_year = datetime.now().year
    # meet_id = slugify(meet_name)
    # meet_gender = ...

    with NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
      tmp_file.write(await file.read())
      tmp_file_path = tmp_file.name
    
    try:
      meet_id, event_name, gender, round_name = process_event(file_path=tmp_file_path, meet_year=meet_year)

      raw_blob_name = f"events/{meet_year}/{meet_id}/{file.filename}"
      raw_bucket = get_gcs_client().bucket(BUCKET_NAME)
      raw_bucket.blob(raw_blob_name).upload_from_filename(tmp_file_path)
      print(f"✅ Uploaded raw event file to gs://{BUCKET_NAME}/{raw_blob_name}")

    finally:
      os.remove(tmp_file_path)
    return JSONResponse(
        content={
            "message": f"File '{file.filename}' uploaded and processed to database successfully.",
            "event_file": f"gs://{BUCKET_NAME}/{raw_blob_name}",
            "meet_id": meet_id,
            "event_name": event_name,
            "gender": gender,
            "round_name": round_name
        }
    )



from fastapi import HTTPException
from fastapi.responses import JSONResponse
from google.api_core.exceptions import NotFound
from processors.gcs import get_gcs_client, get_firestore_client

@app.delete("/delete_meet/{meet_id}")
async def delete_meet(meet_id: str):
    """
    Delete all files in GCS and Firestore for a given meet_id.
    """
    meet_id = meet_id.strip()
    if not meet_id:
        raise HTTPException(status_code=400, detail="meet_id must not be empty")

    gcs_client = get_gcs_client()
    firestore_client = get_firestore_client()
    bucket = gcs_client.bucket(BUCKET_NAME)

    deleted_files = []
    deleted_firestore_docs = []

    # Try to find meet_year dynamically from Firestore (fallback to current year)
    try:
        meet_doc = firestore_client.collection("meets").document(meet_id).get()
        meet_data = meet_doc.to_dict() if meet_doc.exists else {}
        meet_year = meet_data.get("year") or datetime.now().year
    except Exception:
        meet_year = datetime.now().year

    # -----------------------------
    # 1️⃣ Delete all related GCS files
    # -----------------------------
    prefixes = [
        f"merged-start-lists/{meet_year}/{meet_id}",
        f"events/{meet_year}/{meet_id}/",
    ]

    for prefix in prefixes:
        blobs = bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            try:
                blob.delete()
                deleted_files.append(blob.name)
            except NotFound:
                continue

    def delete_subcollections(doc_ref):
        collections = doc_ref.collections()
        for coll in collections:
            for doc in coll.stream():
                delete_subcollections(doc.reference)
                doc.reference.delete()
                deleted_firestore_docs.append(doc.reference.path)

    meet_ref = firestore_client.collection("meets").document(meet_id)
    delete_subcollections(meet_ref)
    meet_ref.delete()
    deleted_firestore_docs.append(meet_ref.path)

    return JSONResponse(
        content={
            "message": f"Meet '{meet_id}' deleted successfully.",
            "meet_year": meet_year,
            "deleted_files_count": len(deleted_files),
            "deleted_firestore_docs_count": len(deleted_firestore_docs),
            "deleted_files": deleted_files,
            "deleted_firestore_docs": deleted_firestore_docs,
        }
    )
 