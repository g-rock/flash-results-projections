import os
import asyncio
import json
import configparser
from tempfile import NamedTemporaryFile
from pydantic import BaseModel
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
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
origins = ["http://localhost:5173",  "https://flash-results-projections.web.app"]

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
    Upload a merged start list CSV and an INI file. This endpoint will process the CSV for initial score projections, parse the INI for meet information (date, year, meet name, location), and upload the CSV to GCS.
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

        metadata = {}
        missing_fields = []

        for key, (section, option) in required_fields.items():
            value = config.get(section, option, fallback=None)
            if not value:
                missing_fields.append(f"'{option}' in [{section}]")
            metadata[key] = value

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"INI file missing required fields: {', '.join(missing_fields)}"
            )

        # --- Extract year from meet_date ---
        try:
            metadata["meet_year"] = int(metadata["meet_date"].split(",")[-1].strip())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot extract year from meetdate: {metadata['meet_date']}"
            )
        
        # --- Map meet_season to indoor/outdoor ---
        season_mapping = {"on": "outdoor", "off": "indoor"}
        mapped_season = season_mapping.get(metadata.get("meet_season", "").lower())

        if mapped_season is None:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid meet_season value: {metadata.get('meet_season')}"
            )

        # Overwrite meet_season with mapped value
        metadata["meet_season"] = mapped_season

        metadata["meet_id"] = slugify(metadata["meet_name"])

        # --- Process CSV ---
        process_merged_start_list(
            file_path=tmp_csv_path,
            meet_year=metadata["meet_year"],
            meet_id=metadata["meet_id"],
            meet_name=metadata["meet_name"],
            meet_season=metadata["meet_season"],
            meet_date=metadata["meet_date"],
            meet_location=metadata["meet_location"]
        )

        # --- Upload CSV to GCS ---
        raw_bucket = get_gcs_client().bucket(BUCKET_NAME)

        # CSV blob
        csv_blob_name = f"merged-start-lists/{metadata['meet_year']}/{metadata['meet_season']}/{metadata['meet_id']}/start_list.csv"
        raw_bucket.blob(csv_blob_name).upload_from_filename(tmp_csv_path)

        # INI blob
        ini_blob_name = f"merged-start-lists/{metadata['meet_year']}/{metadata['meet_season']}/{metadata['meet_id']}/config.ini"
        raw_bucket.blob(ini_blob_name).upload_from_filename(tmp_ini_path)

        return JSONResponse(
            content={
                "message": f"Files '{csv_file.filename}' and '{ini_file.filename}' uploaded and processed successfully.",
                "merged_start_list_file": f"gs://{BUCKET_NAME}/{csv_blob_name}",
                "ini_file": f"gs://{BUCKET_NAME}/{ini_blob_name}",
                **metadata,
            }
        )

    finally:
        os.remove(tmp_csv_path)
        os.remove(tmp_ini_path)

@app.post("/upload_event")
async def upload_event(
    file: UploadFile = File(...)
):
    """
    Upload an event file. This endpoint will process the CSV for new score projections.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="file must be a CSV")
    
    # Check for forbidden substring in filename
    if "splits" in file.filename.lower():
        raise HTTPException(status_code=400, detail='filename cannot contain "splits"')
    
    with NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        tmp_file.write(await file.read())
        tmp_file_path = tmp_file.name
    
    try:
        # process_event now returns meet_year as well
        metadata = process_event(file_path=tmp_file_path)

        raw_blob_name = f"events/{metadata.get('meet_year')}/{metadata.get('meet_season')}/{metadata.get('meet_id')}/{file.filename}"
        raw_bucket = get_gcs_client().bucket(BUCKET_NAME)
        raw_bucket.blob(raw_blob_name).upload_from_filename(tmp_file_path)
        print(f"✅ Uploaded raw event file to gs://{BUCKET_NAME}/{raw_blob_name}")

    finally:
        os.remove(tmp_file_path)

    await notify_clients({
        "type": "event_uploaded",
        "meet_document_id": f"{metadata.get('meet_year')}/{metadata.get('meet_season')}/{metadata.get('meet_id')}",
        **metadata,
    })

    return JSONResponse(
        content={
            "message": f"File '{file.filename}' uploaded and processed to database successfully.",
            "event_file": f"gs://{BUCKET_NAME}/{raw_blob_name}",
            **metadata
        }
    )

class UpdateEventRequest(BaseModel):
    meetDocumentId: str
    gender: str
    eventId: str
    updates: Dict[str, Any]

@app.post("/update_event")
async def update_event(req: UpdateEventRequest):
    """
    Update any fields on a specific event document within a meet and gender.
    """
    db = get_firestore_client()
    try:
        doc_ref = (
            db.collection("meets")
            .document(req.meetDocumentId)
            .collection(req.gender)
            .document(req.eventId)
        )

        doc_ref.update(req.updates)

        await notify_clients({
          "type": "event_updated",
          "meet_document_id": req.meetDocumentId
        })

        return {"success": True, "updatedFields": req.updates}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete_meet")
async def delete_meet(database_id: str):
    """
    Delete all files in GCS and Firestore for a given meet document.
    The meet document is assumed to be at 'meets/{database_id}'.
    """
    document_id = database_id.strip()
    if not document_id:
        raise HTTPException(status_code=400, detail="document_id must not be empty")

    gcs_client = get_gcs_client()
    db = get_firestore_client()
    bucket = gcs_client.bucket(BUCKET_NAME)

    # Reference to the meet document
    meet_ref = db.collection("meets").document(document_id)

    # Check if meet exists
    if not meet_ref.get().exists:
        return JSONResponse(
            status_code=404,
            content={"message": f"Meet '{document_id}' does not exist."}
        )

    # Fetch the meet data for year (used in GCS paths)
    meet_doc = meet_ref.get().to_dict()
    meet_year = meet_doc.get("year", "unknown")
    meet_season = meet_doc.get("season", "unknown")
    meet_id = meet_doc.get("id", "unknown")

    # Delete GCS files
    prefixes = [
        f"merged-start-lists/{meet_year}/{meet_season}/{meet_id}",
        f"events/{meet_year}/{meet_season}/{meet_id}/",
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
        content={"message": f"Meet '{document_id}' deleted successfully."}
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
