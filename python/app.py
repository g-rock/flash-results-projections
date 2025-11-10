import os
import asyncio
import json
import configparser
from tempfile import NamedTemporaryFile
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from google.api_core.exceptions import NotFound
from processors.startlist import process_merged_start_list
from processors.event import process_event
from processors.gcs import slugify, get_gcs_client, get_gcs_client, get_firestore_client

# GCS & Firestore clients
BUCKET_NAME = "projections-data"

# -----------------------------
# FastAPI app
# -----------------------------
origins = ["http://localhost:5173",  "http://localhost:8000"]

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
    csv_file: UploadFile = File(...),
    ini_file: UploadFile = File(...)
):
    """
    Upload a CSV and an INI file, process the CSV, parse the INI, and upload CSV to GCS.
    Extract meet_name, meet_year, and other info from the INI file.
    """

    # --- Validate file extensions ---
    if not csv_file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="csv_file must be a CSV")
    if not ini_file.filename.endswith(".ini"):
        raise HTTPException(status_code=400, detail="ini_file must be an INI")

    # --- Save files temporarily ---
    with NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv, \
         NamedTemporaryFile(delete=False, suffix=".ini") as tmp_ini:
        tmp_csv.write(await csv_file.read())
        tmp_ini.write(await ini_file.read())

        tmp_csv_path = tmp_csv.name
        tmp_ini_path = tmp_ini.name

    try:
        # --- Parse INI ---
        config = configparser.ConfigParser()
        config.read(tmp_ini_path)

        # --- Extract required fields ---
        required_fields = {
            "meet_name": ("index", "meet"),
            "meet_date": ("index", "meetdate"),
            "meet_location": ("index", "meetlocation"),
            "meet_venue": ("index", "meetvenue"),
            "meet_season": ("switch", "outdoor")
        }

        meet_info = {}
        missing_fields = []

        for key, (section, option) in required_fields.items():
            value = config.get(section, option, fallback=None)
            if not value:
                missing_fields.append(f"'{option}' in [{section}]")
            meet_info[key] = value

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"INI file missing required fields: {', '.join(missing_fields)}"
            )

        # --- Extract year from meet_date ---
        try:
            meet_info["meet_year"] = int(meet_info["meet_date"].split(",")[-1].strip())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot extract year from meetdate: {meet_info['meet_date']}"
            )
        
        # --- Map meet_season to indoor/outdoor ---
        season_mapping = {"on": "outdoor", "off": "indoor"}
        mapped_season = season_mapping.get(meet_info.get("meet_season", "").lower())

        if mapped_season is None:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid meet_season value: {meet_info.get('meet_season')}"
            )

        # Overwrite meet_season with mapped value
        meet_info["meet_season"] = mapped_season

        meet_id = slugify(meet_info["meet_name"])

        # --- Process CSV ---
        process_merged_start_list(
            file_path=tmp_csv_path,
            meet_year=meet_info["meet_year"],
            meet_id=meet_id,
            meet_name=meet_info["meet_name"],
            meet_season=meet_info["meet_season"],
            meet_date=meet_info["meet_date"],
            meet_location=meet_info["meet_location"]
        )

        # --- Upload CSV to GCS ---
        raw_blob_name = f"merged-start-lists/{meet_info['meet_year']}/{meet_id}"
        raw_bucket = get_gcs_client().bucket(BUCKET_NAME)
        raw_bucket.blob(raw_blob_name).upload_from_filename(tmp_csv_path)
        print(f"✅ Uploaded raw start list file to gs://{BUCKET_NAME}/{raw_blob_name}")

        return JSONResponse(
            content={
                "message": f"Files '{csv_file.filename}' and '{ini_file.filename}' uploaded and processed successfully.",
                "merged_start_list_file": f"gs://{BUCKET_NAME}/{raw_blob_name}",
                **meet_info,
                "meet_id": meet_id
            }
        )

    finally:
        os.remove(tmp_csv_path)
        os.remove(tmp_ini_path)


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

    await notify_clients({
      "type": "event_uploaded",
      "meet_id": meet_id,
      "meet_year": meet_year,
      "event_name": event_name,
      "gender": gender,
      "round_name": round_name,
      "timestamp": datetime.now().isoformat()
    })

    return JSONResponse(
        content={
            "message": f"File '{file.filename}' uploaded and processed to database successfully.",
            "event_file": f"gs://{BUCKET_NAME}/{raw_blob_name}",
            "meet_id": meet_id,
            "meet_year": meet_year,
            "event_name": event_name,
            "gender": gender,
            "round_name": round_name
        }
    )

@app.delete("/delete_meet/{meet_year}/{meet_id}")
async def delete_meet(meet_year: str, meet_id: str):
    """
    Delete all files in GCS and Firestore for a given meet_id under a specific year.
    Returns a simple message if the meet does not exist.
    """
    meet_id = meet_id.strip()
    meet_year = meet_year.strip()
    if not meet_id or not meet_year:
        raise HTTPException(status_code=400, detail="meet_id and meet_year must not be empty")

    gcs_client = get_gcs_client()
    firestore_client = get_firestore_client()
    bucket = gcs_client.bucket(BUCKET_NAME)

    # Reference to the meet document
    meet_ref = firestore_client.collection("years").document(meet_year).collection("meets").document(meet_id)

    # Check if meet exists
    if not meet_ref.get().exists:
        return JSONResponse(
            status_code=404,
            content={"message": f"Meet '{meet_id}' for year '{meet_year}' does not exist."}
        )

    # Delete GCS files
    prefixes = [
        f"merged-start-lists/{meet_year}/{meet_id}",
        f"events/{meet_year}/{meet_id}/",
    ]
    for prefix in prefixes:
        blobs = bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            try:
                blob.delete()
            except NotFound:
                continue

    # Delete Firestore subcollections recursively
    def delete_subcollections(doc_ref):
        for coll in doc_ref.collections():
            for doc in coll.stream():
                delete_subcollections(doc.reference)
                doc.reference.delete()

    delete_subcollections(meet_ref)
    meet_ref.delete()

    return JSONResponse(
        content={"message": f"Meet '{meet_id}' ({meet_year}) deleted successfully."}
    )

subscribers = []

async def notify_clients(payload: dict):
    """Send a message to all active subscribers."""
    for queue in subscribers:
        await queue.put(payload)

@app.get("/stream")
async def stream():
    """SSE endpoint that streams JSON updates."""
    queue = asyncio.Queue()
    subscribers.append(queue)
    print("🔌 Client connected")

    async def event_generator():
        try:
            while True:
                data = await queue.get()
                yield f"data: {json.dumps(data)}\n\n"
        except asyncio.CancelledError:
            print("❌ Client disconnected")
            subscribers.remove(queue)
            raise

    return StreamingResponse(event_generator(), media_type="text/event-stream")
