import os
import re
import pandas as pd
import csv
from processors.gcs import get_firestore_client
from processors.gcs import slugify

def process_event(file_path: str, meet_year: str):

  print(f"Processing file: {file_path}")
  df, meet_id, gender, event_name, round_name = parse_event(os.path.dirname(file_path), os.path.basename(file_path))
  db = get_firestore_client()

  meets_ref = db.collection("meets")
  query = meets_ref.where("id", "==", meet_id).where("year", "==", meet_year)
  results = list(query.stream())

  if not results:
      raise ValueError(f"Meet not found for meet_id='{meet_id}' and meet_year='{meet_year}'")

  meet_doc_ref = results[0].reference
  gender_ref = meet_doc_ref.collection("events").document(gender)
  event_ref = gender_ref.collection("events").document(event_name)

  event_ref.set({
      "round_name": round_name,
  }, merge=True)
  return meet_id, event_name, gender, round_name

def parse_event(input_dir, input_filename):
    input_csv_path = os.path.join(input_dir, input_filename)

    if not os.path.exists(input_csv_path):
        raise FileNotFoundError(f"File not found: {input_csv_path}")
    
    with open(input_csv_path, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
    
    if len(reader) < 2:
        raise ValueError("CSV appears to have no data rows")

    # --- Parse metadata from first line ---
    meta_row = reader[0]
    metadata = {
        "event_code": meta_row[0],
        "round_num": meta_row[1],
        "event_name": meta_row[2],
        "round_name": meta_row[3],
        "status": meta_row[4],
        "timing": meta_row[5],
        "day_time": meta_row[6],
        "conditions": meta_row[7],
        "meet_name": meta_row[8],
        "meet_dates": meta_row[9],
        "meet_year": meta_row[10],
        "location": meta_row[11] if len(meta_row) > 11 else ""
    }

    data_rows = reader[1:]

    # Define headers manually (Flash Results style)
    headers = [
        "Place", "First", "Last", "Bib", "Yr", "Team_abbr", "Team", 
        "Result", "AltResult", "Q", "Wind", "Heat", "Lane"
    ]

    # Build DataFrame, pad rows if short
    normalized_rows = []
    for row in data_rows:
        if not row or not row[0].strip().isdigit():
            continue  # skip blanks or invalid lines
        padded_row = row[:len(headers)] + [""] * (len(headers) - len(row))
        normalized_rows.append(padded_row[:len(headers)])

    df = pd.DataFrame(normalized_rows, columns=headers)

    # --- Add metadata columns for consistency ---
    gender = "Men" if "Men" in metadata["event_name"] else "Women"
    event_name = re.sub(r'\b(Men|Women)\b\s*', '', metadata["event_name"]).strip()
    df["Event Name"] = event_name
    df["Gender"] = gender
    df["Meet"] = metadata["meet_name"]
    df["Date"] = metadata["meet_dates"]
    df["Location"] = metadata["location"]
    df["Status"] = metadata["status"]

    # Rename key columns to align with clean_and_score expectations
    df = df.rename(columns={
        "First": "Col_3",
        "Last": "Col_4",
        "Team_abbr": "Team_abbr",
        "Team": "Col_7",
        "Result": "Seed"
    })

    meet_id = slugify(metadata["meet_name"])
    return df, meet_id, gender, event_name, metadata["round_name"]
