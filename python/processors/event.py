import os
import re
import pandas as pd
import csv
from processors.gcs import get_firestore_client, slugify, parse_time_or_distance
from .constants import RELAY_EVENT_LIST
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
          f"meet_year='{metadata.get('meet_year')}'. Check that the meet exists."
      )
    
    # if metadata.get('event_round') in ['prelims']:
    #   raise ValueError(
    #   f"Event round '{metadata.get('event_round')}' for event_name='{metadata.get('event_name')}', "
    #   f"meet_id='{metadata.get('meet_id')}', meet_season='{metadata.get('meet_season')}', "
    #   f"meet_year='{metadata.get('meet_year')}' will not be processed."
    # )

    VALID_STATUSES = {'complete', 'official', 'scored', 'in-progress', 'scored-under-review', 'scored-protest', 'scheduled'}
    SCORING_STATUSES = {"scored", "scored-protest", "scored-under-review"}
    NON_RESULT_STATUSES = {"scheduled", "official", "complete", "in-progress"}
    
    status = metadata.get('event_status')
    event_round = metadata.get('event_round')
    
    # Treat prelims with scored-review statuses as in-progress
    if (
        event_round == "prelims"
        and status in {"scored-protest", "scored-under-review"}
    ):
      status = "in-progress"

    if status not in VALID_STATUSES:
        allowed = ", ".join(sorted(VALID_STATUSES))
        raise ValueError(
            f"Round status '{status}' for event_name='{metadata.get('event_name')}', "
            f"meet_id='{metadata.get('meet_id')}', meet_season='{metadata.get('meet_season')}', "
            f"meet_year='{metadata.get('meet_year')}' will not be processed. "
            f"Allowed statuses are: {allowed}."
        )
    
    event_ref = (
      meet_doc_ref
      .collection(metadata.get('event_gender'))
      .document(metadata.get('event_num'))
    )

    update_data = {
      "status": status
    }

    if status in SCORING_STATUSES:
      cleaned_data = clean_event(df, event_ref)
      update_data["scored"] = {
          "event_results": cleaned_data
              .get(metadata.get("event_gender"))
              .get(metadata.get("event_num")),
          "event_round": metadata.get("event_round"),
      }

    elif status in NON_RESULT_STATUSES:
      pass

    event_ref.set(update_data, merge=True)

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
    # Build partial metadata first (before slugify)
    partial_metadata = {
        "event_num": meta_row[0].lstrip("0") if len(meta_row) > 0 else None,
        "event_name": meta_row[2] if len(meta_row) > 2 else None,
        "event_round": meta_row[3] if len(meta_row) > 3 else None,
        "event_status": meta_row[4] if len(meta_row) > 4 else None,
        "meet_name": meta_row[8] if len(meta_row) > 8 else None,
        "meet_year": meta_row[10] if len(meta_row) > 10 else None,
        "meet_season": meta_row[12] if len(meta_row) > 12 else None,
    }

    try:
        # Slugify base fields
        metadata = {
            **partial_metadata,
            "meet_year": slugify(partial_metadata["meet_year"]),
            "meet_id": slugify(partial_metadata["meet_name"]),
            "meet_season": slugify(partial_metadata["meet_season"])
        }

        # Normalize
        event_gender = "Men" if "Men" in metadata["event_name"] else "Women"
        event_name = re.sub(r'\b(Men|Women)\b\s*', '', metadata["event_name"]).strip()
        event_round, event_status = normalize_round_and_status(
            metadata["event_round"],
            metadata["event_status"]
        )

        # Slugify normalized fields
        metadata.update({
            "event_gender": slugify(event_gender),
            "event_name": slugify(event_name),
            "event_round": slugify(event_round),
            "event_status": slugify(event_status)
        })

        return metadata

    except AttributeError as e:
        raise ValueError(
            f"Failed to parse standard event metadata. Parsed values so far: {partial_metadata}. "
            "Check that meet_name, meet_year, and meet_season exist and are valid strings."
        ) from e

def parse_multi_event_metadata(meta_row):
    """
    Parse metadata for multi-event CSVs, which have fewer columns.
    """
    partial_metadata = {
        "event_num": meta_row[0].lstrip("0") if len(meta_row) > 0 else None,
        "event_name": meta_row[2] if len(meta_row) > 2 else None,
        "event_round": meta_row[3] if len(meta_row) > 3 else None,
        "event_status": meta_row[4] if len(meta_row) > 4 else None,
        "meet_name": meta_row[6] if len(meta_row) > 6 else None,
        "meet_year": meta_row[8] if len(meta_row) > 8 else None,
        "meet_season": meta_row[10] if len(meta_row) > 10 else None,
    }

    try:
        metadata = {
            **partial_metadata,
            "meet_year": slugify(partial_metadata["meet_year"]),
            "meet_id": slugify(partial_metadata["meet_name"]),
            "meet_season": slugify(partial_metadata["meet_season"])
        }

        # Normalize
        event_gender = infer_gender(metadata["event_name"], metadata["meet_season"])
        event_round, event_status = normalize_round_and_status(
            metadata["event_round"],
            metadata["event_status"]
        )

        metadata.update({
            "event_gender": slugify(event_gender),
            "event_round": slugify(event_round),
            "event_status": slugify(event_status)
        })

        return metadata

    except AttributeError as e:
        raise ValueError(
            f"Failed to parse multi-event metadata. Parsed values so far: {partial_metadata}. "
            "Check that meet_name, meet_year, and meet_season exist and are valid strings."
        ) from e
def parse_standard_event_results(metadata: dict, data_rows: list):
    """
    Build results DataFrame for standard events.
    """
    headers = [
        "Place", "First", "Last", "ID", "Yr", "Team_abbr", "Team_name",
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
    base_headers = ["Place", "First", "Last", "Team_abbr", "Team_name", "Result", "Trailing_points", "ID", "Class", "Blank"]

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
    
def clean_event(df, event_ref):
    """
    Processes an event DataFrame into the same nested structure as score_event(),
    but without assigning scores. Also enriches each athlete with sb_numeric
    from the 'projection' event document if available.
    """

    nested_data = {}
    genders = df['Event Gender'].unique()

    # Fetch the event document once
    event_doc = event_ref.get()
    event_data = event_ref.get().to_dict() if event_doc.exists else {}
    event_sort_ascending = event_data["sort_ascending"] 

    for gender in genders:
        nested_data[gender] = {}
        events = df[df['Event Gender'] == gender]['Event Num'].unique()

        for event in events:
            event_df = df[(df['Event Gender'] == gender) & (df['Event Num'] == event)]

            # --- Build sb_lookup by athlete_id ---
            sb_lookup = {}
            if event_doc.exists and "projection" in event_data:
                proj = event_data["projection"]
                event_results = proj.get("event_results", [])
                for r in event_results:
                    athlete_id = r.get("athlete_id")
                    sb_val = r.get("sb_numeric")
                    if athlete_id is not None:
                        sb_lookup[athlete_id] = sb_val

            event_type = None
            if event_doc.exists and "event_type" in event_data:
                event_type = event_data["event_type"]

            event_records = []
            for _, row in event_df.iterrows():
              raw_id = str(row["ID"]).strip()
              athlete_id = int(raw_id) if raw_id.isdigit() else None
              athlete_name = f"{row['First']} {row['Last']}".strip()

              seed_val = parse_time_or_distance(row["Result"])
              sb_val = sb_lookup.get(athlete_id)

              # Update sb_numeric if seed is better than current sb
              if seed_val is not None:
                  if sb_val is None:
                    sb_val = seed_val
                  else:
                      # Running / relay events: lower is better (sort_ascending=True)
                      if event_sort_ascending and seed_val < sb_val:
                          sb_val = seed_val
                      # Field / multi events: higher is better (sort_ascending=False)
                      elif not event_sort_ascending and seed_val > sb_val:
                          sb_val = seed_val
              rec = {
                  "team_name": row["Team_name"].strip() if isinstance(row["Team_name"], str) else None,
                  "team_abbr": row["Team_abbr"],
                  "athlete_id": athlete_id,
                  "athlete_name": athlete_name,
                  "seed_numeric": seed_val,
                  "sb_numeric": sb_val
              }

              # Relay fix
              if event_type == 'relay':
                  rec["team_name"] = athlete_name

              rec["team_name"] = rec["team_name"].strip().upper() if isinstance(rec["team_name"], str) and rec["team_name"].strip() else ""
              event_records.append(rec)

            nested_data[gender][event] = event_records

    return nested_data