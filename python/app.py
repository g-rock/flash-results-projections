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
    