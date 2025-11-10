import os
import re
import pandas as pd
import csv
from processors.gcs import get_firestore_client, slugify
from .constants import POINTS_SYSTEM
def process_event(file_path: str, meet_year: str):
    """
    Process a single event CSV and upload the scored data to Firestore
    under years/{meet_year}/meets/{meet_id}/{gender}/{event_name}.
    """
    print(f"Processing file: {file_path}")

    # Parse the CSV
    df, meet_id, gender, event_name, round_name, round_status = parse_event(
        os.path.dirname(file_path),
        os.path.basename(file_path)
    )

    db = get_firestore_client()
    meet_doc_ref = db.collection("years").document(str(meet_year)) \
                      .collection("meets").document(meet_id)

    # Check if meet exists
    if not meet_doc_ref.get().exists:
      raise ValueError(f"Meet not found for meet_id='{meet_id}' and meet_year='{meet_year}'")

    clean_round_status = slugify(round_status)
    if clean_round_status in ['complete', 'official', 'scored']:
      # Score the data
      scored_data = score_ordered_df(df)
      db = get_firestore_client()
      event_ref = meet_doc_ref.collection(slugify(gender)).document(slugify(event_name))
      event_ref.set({
          slugify(round_name): {
              'round_results': scored_data.get(gender, {}).get(event_name),
              'round_status': clean_round_status
          }
      }, merge=True)
    else:
      raise ValueError(
          f"Round status '{round_status}' for event_name='{event_name}', "
          f"meet_id='{meet_id}' and meet_year='{meet_year}' "
          "will not be processed. Only 'complete', 'official', 'scored' rounds are allowed."
      )
        
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
        "raw_round": meta_row[3],
        "raw_status": meta_row[4],
        "timing": meta_row[5],
        "day_time": meta_row[6],
        "conditions": meta_row[7],
        "meet_name": meta_row[8],
        "meet_dates": meta_row[9],
        "meet_year": meta_row[10],
        "location": meta_row[11] if len(meta_row) > 11 else ""
    }

    # Clean round name for consistency
    if metadata["raw_round"] and "final" in metadata["raw_round"].lower():
        round_name = "final"
    else:
        round_name = metadata["raw_round"]

    data_rows = reader[1:]

    # Define headers manually (Flash Results style)
    headers = [
        "Place", "First", "Last", "Bib", "Yr", "Team_abbr", "Team_name", 
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
    df["Status"] = metadata["raw_status"]

    # Rename key columns to align with clean_and_score expectations
    df = df.rename(columns={
        "First": "Col_3",
        "Last": "Col_4",
        "Team_abbr": "Team_abbr",
        "Team_name": "Team_name",
        "Team": "Col_7",
        "Result": "Seed"
    })

    meet_id = slugify(metadata["meet_name"])
    return df, meet_id, gender, event_name, round_name, metadata["raw_status"]


def score_ordered_df(df):
    """
    Score a DataFrame that is already ordered by place.
    """
    df['place'] = df['Place'].astype(int)
    
    scored_rows = []
    grouped = df.groupby('place')
    for place, group in grouped:
        if place > 8:
            score = 0
        else:
            # Average points if tie
            num_tied = len(group)
            ranks_involved = list(range(place, place + num_tied))
            total_points = sum(POINTS_SYSTEM.get(r, 0) for r in ranks_involved)
            score = total_points / num_tied
        group = group.copy()
        group['score'] = score
        group['athlete'] = group['Col_3'] + ' ' + group['Col_4']
        group['team_abbr'] = group['Team_abbr']
        group['team_name'] = group['Team_name'].str.upper().str.strip()
        scored_rows.append(group)

    scored_df = pd.concat(scored_rows)

    # Nest by gender and event
    nested_data = {}
    for gender in scored_df['Gender'].unique():
        nested_data[gender] = {}
        events = scored_df[scored_df['Gender'] == gender]['Event Name'].unique()
        for event in events:
            event_df = scored_df[(scored_df['Gender'] == gender) & (scored_df['Event Name'] == event)]
            nested_data[gender][event] = event_df[['team_name', 'score', 'place', 'athlete']].to_dict(orient='records')

    return nested_data