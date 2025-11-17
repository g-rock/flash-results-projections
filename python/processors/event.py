import os
import re
import pandas as pd
import csv
from processors.gcs import get_firestore_client, slugify
from .constants import POINTS_SYSTEM
def process_event(file_path: str):
    """
    Process a single event CSV and upload the scored data to Firestore
    under meets/year/season/{meet_id}.
    """
    print(f"Processing file: {file_path}")

    # Parse the CSV
    metadata, raw_rows = parse_event_metadata(os.path.dirname(file_path), os.path.basename(file_path))
    if metadata.get('event_type') == 'standard':
      df = parse_standard_event_results(metadata, raw_rows)
    else:
      df = parse_multi_event_results(metadata, raw_rows)

    db = get_firestore_client()
    meet_doc_ref = (
      db.collection("meets")
        .document(metadata.get("meet_year"))
        .collection(metadata.get("meet_season"))
        .document(metadata.get("meet_id"))
    )

    # Check if meet exists
    if not meet_doc_ref.get().exists:
      raise ValueError(
          f"Meet not found for meet_id='{metadata.get('meet_id')}', "
          f"meet_season='{metadata.get('meet_season')}', "
          f"meet_year='{metadata.get('meet_year')}'"
      )
    
    if metadata.get('event_round') in ['prelims']:
      raise ValueError(
      f"Event round '{metadata.get('event_round')}' for event_name='{metadata.get('event_name')}', "
      f"meet_id='{metadata.get('meet_id')}', meet_season='{metadata.get('meet_season')}', "
      f"meet_year='{metadata.get('meet_year')}' will not be processed. "
    )

    if metadata.get('event_status') in ['complete', 'official', 'scored', 'in-progress']:
      # Score the data
      scored_data = score_event(df)
      db = get_firestore_client()
      event_ref = meet_doc_ref.collection(metadata.get('event_gender')).document(metadata.get('event_num'))
      event_ref.set({
          metadata.get('event_status'): {
              'event_results': scored_data.get(metadata.get('event_gender')).get(metadata.get('event_num')),
              'event_round': metadata.get('event_round')
          }
      }, merge=True)
    else:
      raise ValueError(
        f"Round status '{metadata.get('event_status')}' for event_name='{metadata.get('event_name')}', "
        f"meet_id='{metadata.get('meet_id')}', meet_season='{metadata.get('meet_season')}', "
        f"meet_year='{metadata.get('meet_year')}' will not be processed. "
        "Only 'complete', 'official', 'scored', and 'in-progress' statuses are allowed."
      )

        
    return metadata

def parse_event_metadata(input_dir: str, input_filename: str):
    """
    Reads a CSV, extracts the first-line metadata fields,
    returns metadata and raw data rows.
    """
    input_csv_path = os.path.join(input_dir, input_filename)

    if not os.path.exists(input_csv_path):
        raise FileNotFoundError(f"File not found: {input_csv_path}")
    
    with open(input_csv_path, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))

    if len(reader) < 2:
        raise ValueError("CSV appears to have no data rows")

    meta_row = reader[0]

    # --------------------------------------------------------
    # MULTI-EVENT DETECTION
    # --------------------------------------------------------
    is_multi_event = len(meta_row) < 13

    if is_multi_event:
        metadata = parse_multi_event_metadata(meta_row)
        metadata["event_type"] = 'multi'
    else:
        metadata = parse_standard_event_metadata(meta_row)
        metadata["event_type"] = 'standard'

    data_rows = reader[1:]
    return metadata, data_rows

def parse_standard_event_metadata(meta_row):
    metadata = {
        "event_num": meta_row[0].lstrip("0"),
        "event_name": meta_row[2],
        "event_round": meta_row[3],
        "event_status": meta_row[4],
        "meet_name": meta_row[8],
        "meet_year": slugify(meta_row[10]),
        "meet_season": slugify(meta_row[12]),
    }

    # Normalize
    event_gender = "Men" if "Men" in metadata["event_name"] else "Women"
    event_name = re.sub(r'\b(Men|Women)\b\s*', '', metadata["event_name"]).strip()
    event_round, event_status = normalize_round_and_status(
      metadata["event_round"],
      metadata["event_status"]
    )

    # Slugify normalized fields
    metadata["event_gender"] = slugify(event_gender)
    metadata["event_name"] = slugify(event_name)
    metadata["event_round"] = slugify(event_round)
    metadata["event_status"] = slugify(event_status)
    metadata["meet_year"] = slugify(metadata["meet_year"])
    metadata["meet_id"] = slugify(metadata["meet_name"])

    return metadata

def parse_multi_event_metadata(meta_row):
    """
    Parse metadata for multi-event CSVs, which have fewer columns.
    """

    metadata = {
        "event_num": meta_row[0].lstrip("0"),
        "event_name": meta_row[2],
        "event_round": meta_row[3],
        "event_status": meta_row[4],
        "meet_name": meta_row[6],
        "meet_year": slugify(meta_row[8]),
        "meet_season": slugify(meta_row[10]),
    }

    # Normalize 
    event_gender = infer_gender(metadata["event_name"], metadata["meet_season"])
    event_round, event_status = normalize_round_and_status(
      metadata["event_round"],
      metadata["event_status"]
    )

    print(event_round)
    print(event_status)
    
    metadata["event_gender"] = slugify(event_gender)
    metadata["event_round"] = slugify(event_round)
    metadata["event_status"] = slugify(event_status)
    metadata["meet_id"] = slugify(metadata["meet_name"])

    return metadata

def parse_standard_event_results(metadata: dict, data_rows: list):
    """
    Build results DataFrame for standard events.
    """
    headers = [
        "Place", "First", "Last", "Bib", "Yr", "Team_abbr", "Team_name",
        "Result", "AltResult", "Q", "Wind", "Heat", "Lane"
    ]

    normalized_rows = []
    for row in data_rows:
        if not row or not row[0].strip().isdigit():
            continue
        padded_row = row[:len(headers)] + [""] * (len(headers) - len(row))
        normalized_rows.append(padded_row[:len(headers)])

    df = pd.DataFrame(normalized_rows, columns=headers)

    # Add metadata columns
    df["Event Num"] = metadata["event_num"]
    df["Event Name"] = metadata["event_name"]
    df["Event Status"] = metadata["event_status"]
    df["Event Gender"] = metadata["event_gender"]
    df["Meet Name"] = metadata["meet_name"]
    df["Meet Season"] = metadata["meet_season"]
    df["Meet Year"] = metadata["meet_year"]

    return df

def parse_multi_event_results(metadata: dict, data_rows: list):
    """
    Build results DataFrame for multi-events dynamically.
    Each event contributes 4 columns: time, distance, event_points, total_points
    """
    # Base metadata columns
    base_headers = ["Place", "First", "Last", "Team_abbr", "Team_name", "Total_points", "Trailing_points", "Bib", "Class", "Blank"]

    # Extract event names from first row, skipping base columns
    raw_event_headers = data_rows[0]
    event_names = [val.strip() for val in raw_event_headers if val.strip() != ""]
    # Build event-specific headers: 4 columns per event
    event_headers = []
    for event in event_names:
        event_headers.extend([
            f"{event}_Time",
            f"{event}_Distance",
            f"{event}_Points",
            f"{event}_Total"
        ])

    # Combine headers
    headers = base_headers + event_headers

    normalized_rows = []
    for row in data_rows[1:]:  # skip first row
        if not row or not row[0].strip().isdigit():
            continue
        # pad row to match headers length
        padded_row = row[:len(headers)] + [""] * (len(headers) - len(row))
        normalized_rows.append(padded_row[:len(headers)])

    df = pd.DataFrame(normalized_rows, columns=headers)

    # Add metadata columns
    df["Event Num"] = metadata["event_num"]
    df["Event Name"] = metadata["event_name"]
    df["Event Status"] = metadata["event_status"]
    df["Event Gender"] = metadata["event_gender"]
    df["Meet Name"] = metadata["meet_name"]
    df["Meet Season"] = metadata["meet_season"]
    df["Meet Year"] = metadata["meet_year"]

    return df

def normalize_round_and_status(event_round: str, event_status: str):
    # --- Normalize round ---
    if event_round and "final" in event_round.lower():
        round_name = "final"
    else:
        round_name = event_round

    # --- Normalize status ---
    if event_status and "progress" in event_status.lower():
        status_name = "in-progress"
    else:
        status_name = event_status

    return round_name, status_name

def infer_gender(event_name: str, meet_season: str) -> str:
    name = event_name.lower()
    season = meet_season.lower()

    # Outdoor rules
    if season == "outdoor":
        if "decathlon" in name:
            return "Men"
        if "heptathlon" in name:
            return "Women"

    # Indoor rules
    if season == "indoor":
        if "heptathlon" in name:
            return "Men"
        if "pentathlon" in name:
            return "Women"
    

def score_event(df):
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
        group['athlete'] = group['First'] + ' ' + group['Last']
        group['team_abbr'] = group['Team_abbr']
        group['team_name'] = group['Team_name'].str.upper().str.strip()
        scored_rows.append(group)

    scored_df = pd.concat(scored_rows)

    # Nest by gender and event
    nested_data = {}
    for gender in scored_df['Event Gender'].unique():
        nested_data[gender] = {}
        events = scored_df[scored_df['Event Gender'] == gender]['Event Num'].unique()
        for event in events:
            event_df = scored_df[(scored_df['Event Gender'] == gender) & (scored_df['Event Num'] == event)]
            event_name = event_df['Event Name'].iloc[0]
            event_lower = event_name.lower()
            records = event_df[['team_name', 'team_abbr', 'score', 'place', 'athlete']].to_dict(orient='records')
            for r in records:
              if 'relay' in event_lower or 'medley' in event_lower:
                  # team_name comes from athlete name for relays
                  if isinstance(r.get("athlete"), str):
                      r['team_name'] = r['athlete'].strip()

              # normalize the name always
              if isinstance(r.get('team_name'), str):
                  r['team_name'] = r['team_name'].upper().strip()
            nested_data[gender][event] = records
            
    return nested_data