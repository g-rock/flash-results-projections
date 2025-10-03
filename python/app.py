import os
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from tempfile import NamedTemporaryFile
from google.cloud import storage
from fastapi.middleware.cors import CORSMiddleware

# Import processing functions from separate module
from processors import (
    parse_track_event_data,
    clean_and_score,
    build_column_defs,
    upload_file_to_gcs,
    upload_json_to_gcs,
    get_blob_json
)

# -----------------------------
# GCS & FastAPI setup
# -----------------------------
SERVICE_ACCOUNT_FILE = "helper-service-account.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
client = storage.Client()
bucket_name = "projections-data"
app = FastAPI(title="Track Meet Processing API", version="1.1")
origins = [
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------
# POST endpoint to upload CSV & process
# -----------------------------
@app.post("/process_meet_upload")
async def process_meet_upload(
    meet_name: str = Form(...),
    file: UploadFile = File(...)
):
    meet_name = meet_name.strip()
    if not meet_name:
        raise HTTPException(status_code=400, detail="meet_name must not be empty")
    
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV")
    
    output_dir = os.path.join("outputs", meet_name)
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Save uploaded CSV temporarily
        with NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
            tmp_file.write(await file.read())
            tmp_file_path = tmp_file.name

        # Step 1: Parse raw CSV
        df_cleaned = parse_track_event_data(os.path.dirname(tmp_file_path), os.path.basename(tmp_file_path))

        # Step 2: Clean, score, pivot
        df_scores, women_df, men_df = clean_and_score(df_cleaned)

        # Step 2a: Save per-athlete event scores locally & GCS
        per_athlete_file = os.path.join(output_dir, "per_athlete_event_scores.csv")
        df_scores.to_csv(per_athlete_file, index=False)
        upload_file_to_gcs(client, bucket_name, per_athlete_file, f"{meet_name}/per_athlete_event_scores.csv")

        # Step 3: Column definitions
        column_defs_women = build_column_defs(df_scores, 'Women')
        column_defs_men = build_column_defs(df_scores, 'Men')

        # Step 4: Save pivoted team JSON locally
        women_file = os.path.join(output_dir, "womenData.json")
        men_file = os.path.join(output_dir, "menData.json")
        with open(women_file, "w") as wf:
            json.dump(women_df.to_dict(orient='records'), wf, indent=2)
        with open(men_file, "w") as mf:
            json.dump(men_df.to_dict(orient='records'), mf, indent=2)

        # Upload JSON to GCS
        upload_json_to_gcs(client, bucket_name, f"{meet_name}/womenData.json", women_df.to_dict(orient='records'))
        upload_json_to_gcs(client, bucket_name, f"{meet_name}/menData.json", men_df.to_dict(orient='records'))

        # Step 5: Save columnDefs JSON locally
        col_defs_w_file = os.path.join(output_dir, "columnDefs.women.json")
        col_defs_m_file = os.path.join(output_dir, "columnDefs.men.json")
        with open(col_defs_w_file, "w") as wf:
            json.dump(column_defs_women, wf, indent=2)
        with open(col_defs_m_file, "w") as mf:
            json.dump(column_defs_men, mf, indent=2)

        # Upload columnDefs JSON to GCS
        upload_json_to_gcs(client, bucket_name, f"{meet_name}/columnDefs.women.json", column_defs_women)
        upload_json_to_gcs(client, bucket_name, f"{meet_name}/columnDefs.men.json", column_defs_men)

        # Clean up temporary CSV
        os.remove(tmp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing meet: {str(e)}")

    return JSONResponse(content={
        "message": f"Meet '{meet_name}' processed successfully",
        "meet_name": meet_name
    })
@app.get("/list_meets")
async def list_meets():
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # List all blobs and extract unique top-level prefixes
        blobs = client.list_blobs(bucket_name, delimiter='/')
        prefixes = set()
        for page in blobs.pages:
            if page.prefixes:
                prefixes.update(page.prefixes)

        # Clean prefix names (remove trailing '/')
        folder_names = [p.rstrip('/') for p in prefixes]

        return {"meets": sorted(folder_names)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing meets: {str(e)}")
@app.delete("/delete_meet/{meet_name}")
async def delete_meet(meet_name: str):
    meet_name = meet_name.strip()
    if not meet_name:
        raise HTTPException(status_code=400, detail="meet_name must not be empty")
    
    try:
        # List all blobs with the meet_name prefix
        blobs_to_delete = list(client.list_blobs(bucket_name, prefix=f"{meet_name}/"))

        if not blobs_to_delete:
            raise HTTPException(status_code=404, detail=f"No files found for meet '{meet_name}'")

        # Delete all blobs
        for blob in blobs_to_delete:
            blob.delete()
            print(f"Deleted {blob.name}")

        return {"message": f"All files for meet '{meet_name}' have been deleted."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting meet: {str(e)}")
@app.get("/get_meet_data/{meet_name}/{data_type}")
def get_meet_data(meet_name: str, data_type: str):
    """
    data_type: one of ['womenData', 'menData', 'columnDefs.women', 'columnDefs.men']
    """
    blob_mapping = {
        "womenData": f"{meet_name}/womenData.json",
        "menData": f"{meet_name}/menData.json",
        "columnDefs.women": f"{meet_name}/columnDefs.women.json",
        "columnDefs.men": f"{meet_name}/columnDefs.men.json",
    }

    if data_type not in blob_mapping:
        raise HTTPException(status_code=400, detail=f"Invalid data_type: {data_type}")

    try:
        data = get_blob_json(client, bucket_name, blob_mapping[data_type])
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"{data_type} not found for meet '{meet_name}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))