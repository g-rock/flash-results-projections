import os
import re
import pandas as pd
from processors.gcs import get_firestore_client, slugify, parse_time_or_distance
from .constants import FIELD_EVENT_LIST, MULTI_EVENT_LIST, RELAY_EVENT_LIST

def process_merged_start_list(
    file_path: str,
    meet_year: str,
    meet_id: str,
    meet_name: str,
    meet_season: str,
    meet_date: str = None,
    meet_location: str = None
):
    """
    Processes a local CSV start list file, scores it, and uploads results to Firestore.

    Args:
        file_path: Path to the local CSV file.
        meet_year: Year of meet.
        meet_id: Slug of meet.
        meet_name: Name of meet.
        meet_season: 'indoor' or 'outdoor'
        meet_date: Full meet date string (optional).
        meet_location: Location of meet (optional).
    """
    print(f"Processing file: {file_path}")

    # --- Parse CSV and clean ---
    df_parsed = parse_start_list(os.path.dirname(file_path), os.path.basename(file_path))
    cleaned_data_by_gender = clean_start_list(df_parsed)

    # --- Firestore reference ---
    db = get_firestore_client()
    meet_year = str(meet_year)
    meet_ref = db.collection("meets") \
             .document(str(meet_year)) \
             .collection(meet_season) \
             .document(meet_id)

    # --- Set basic meet info ---
    meet_ref.set({
        "name": meet_name,
        "id": meet_id,
        "year": meet_year,
        "date": meet_date,
        "location": meet_location,
        "season": meet_season
    })

    # --- Upload cleaned start list data per gender and event ---
    for gender, events in cleaned_data_by_gender.items():
        gender_key = slugify(gender)
        gender_collection_ref = meet_ref.collection(gender_key)
        for event_num, event_data in events.items():
            event_num_key = slugify(event_num)
            event_doc_ref = gender_collection_ref.document(event_num_key)
            event_doc_ref.set({
                "event_gender": gender,
                "event_name": event_data.get('event_name'),
                "event_type": event_data.get('event_type'),
                "project_points_by_sb": True, # Use Season Best to determine points up until final is scored
                "sort_ascending": event_data.get('sort_ascending'),
                "in_progress": False,
                "projection": {
                    "event_results": event_data.get('event_results'),
                    "event_round": 'prelim'
                }
            })

    return "Upload complete"

def parse_start_list(input_dir, input_filename):

    input_csv_path = os.path.join(input_dir, input_filename)
    cleaned_rows = []
    max_data_cols_found = 0

    if not os.path.exists(input_csv_path):
        raise FileNotFoundError(f"File not found: {input_csv_path}")

    with open(input_csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_gender = None
    current_event_name = None
    current_event_num = None
    in_header_block = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # --- Detect new event header ---
        if line.startswith(";;StartList"):
            in_header_block = True
            current_gender = None
            current_event_name = None
            current_event_num = None
            continue

        # --- Inside header block ---
        if in_header_block:
            parts = [p.strip() for p in line.split(',')]
            if not parts:
                continue

            # Skip notes, meet info, collegiate info, etc.
            if parts[0] in ['R', 'N']:
                continue

            # This is the first actual line that contains the event info
            current_event_num = parts[0].lstrip("0") if parts else "Unknown"

            # Detect gender in the event description (usually in column 2)
            gender_words = ["Men", "Women"]
            found_gender = None
            if len(parts) > 2:
                words = parts[2].split()
                for idx, w in enumerate(words):
                    if w in gender_words:
                        found_gender = w
                        gender_index = idx
                        break

                if found_gender:
                    current_gender = found_gender
                    # Build event name
                    event_name_words = words[:gender_index + 1]
                    for w in words[gender_index + 1:]:
                        if w in ["Prelims", "Finals", "Semifinals", "Heats", "Qualifying"] \
                                or re.match(r'\d{1,2}:\d{2}', w):
                            break
                        event_name_words.append(w)
                    current_event_name = " ".join(event_name_words).strip()
                else:
                    current_gender = "Unknown"
                    current_event_name = "Unknown Event"
            else:
                current_gender = "Unknown"
                current_event_name = "Unknown Event"

            # Header finished, next lines are data rows
            in_header_block = False
            continue

        # --- Athlete/data rows ---
        if current_gender and current_event_name and current_event_num:
            parts = [p.strip() for p in line.split(',')]
            # Skip any stray R or N rows in the middle
            if parts and parts[0] not in ['R', 'N']:
                if len(parts) > max_data_cols_found:
                    max_data_cols_found = len(parts)
                cleaned_rows.append(parts + [current_gender, current_event_name, current_event_num])

    # --- Pad rows to same length ---
    final_cleaned_rows_padded = []
    for row in cleaned_rows:
        data_parts = row[:-3]  # last 3 are gender, event_name, event_num
        gender, event_name, event_num = row[-3], row[-2], row[-1]
        padded_data_parts = data_parts + [''] * (max_data_cols_found - len(data_parts))
        final_cleaned_rows_padded.append(padded_data_parts + [gender, event_name, event_num])

    # --- Column names ---
    data_column_names = [f"Col_{idx+1}" for idx in range(max_data_cols_found)]
    if max_data_cols_found >= 5:
        data_column_names[4] = 'Class_name'
    if max_data_cols_found >= 6:
        data_column_names[5] = 'Athlete_id'
    if max_data_cols_found >= 8:
        data_column_names[7] = 'Team_abbr'
    if max_data_cols_found >= 9:
        data_column_names[8] = 'SB'
    if max_data_cols_found >= 11:
        data_column_names[10] = 'PB'

    final_columns = data_column_names + ['Gender', 'Event_name', 'Event_num']
    df = pd.DataFrame(final_cleaned_rows_padded, columns=final_columns)

    # --- Normalize team columns ---
    if 'Team_abbr' in df.columns:
        df['Team_abbr'] = df['Team_abbr'].apply(lambda x: str(x) if pd.notna(x) and str(x).strip() else '')
    if 'Team_name' in df.columns:
        df['Team_name'] = df['Team_name'].apply(lambda x: str(x).upper() if pd.notna(x) and str(x).strip() else '')

    return df

def clean_start_list(df):
    df = df.rename(columns={
        'Athlete_id': 'athlete_id',
        'Gender': 'event_gender',
        'Event_name': 'event_name',
        'Event_num': 'event_num',
        'Team_abbr': 'team_abbr',
        'Team_name': 'team_name',
        'Class_name': 'class_name',
        'Col_3': 'first_name',
        'Col_4': 'last_name',
        'Col_7': 'team_name',
        'Col_11': 'multi_event_points',
    })

    # --- Normalize gender ---
    df['event_gender'] = df['event_gender'].astype(str).str.strip().str.title()

    # --- Combined events flags ---
    is_pentathlon = df['event_name'].str.startswith('Pen', na=False)
    is_decathlon = df['event_name'].str.startswith('Dec', na=False)
    is_heptathlon = df['event_name'].str.startswith('Hept', na=False)

    def get_first_event(df, mask):
        if not mask.any():
            return None
        first_idx = df.index[mask].min()
        return df.loc[first_idx, 'event_name']

    first_pentathlon_event = get_first_event(df, is_pentathlon)
    first_decathlon_event = get_first_event(df, is_decathlon)
    first_heptathlon_event = get_first_event(df, is_heptathlon)

    # --- Keep only first event entry for combined events ---
    keep_mask = (
        (~is_decathlon & ~is_heptathlon & ~is_pentathlon) |
        (is_decathlon & (df['event_name'] == first_decathlon_event)) |
        (is_heptathlon & (df['event_name'] == first_heptathlon_event)) |
        (is_pentathlon & (df['event_name'] == first_pentathlon_event))
    )
    df = df[keep_mask].copy()

    # --- Rename first events ---
    if first_decathlon_event:
        df.loc[df['event_name'] == first_decathlon_event, 'event_name'] = 'Decathlon'
    if first_heptathlon_event:
        df.loc[df['event_name'] == first_heptathlon_event, 'event_name'] = 'Heptathlon'
    if first_pentathlon_event:
        df.loc[df['event_name'] == first_pentathlon_event, 'event_name'] = 'Pentathlon'

    # --- Strip gender from event_name ---
    df['event_name'] = df['event_name'].str.replace(
        r'\b(Men|Women)\b\s*', '', regex=True
    ).str.strip()

    df['sb_numeric'] = df['SB'].apply(parse_time_or_distance)
    df['pb_numeric'] = df['PB'].apply(parse_time_or_distance)

    # --- Build nested_data (raw, no scoring) ---
    nested_data = {}

    for gender in df['event_gender'].unique():
        nested_data[gender] = {}
        gender_df = df[df['event_gender'] == gender]

        for event_num in gender_df['event_num'].unique():
            event_df = gender_df[gender_df['event_num'] == event_num]
            event_name = event_df['event_name'].iloc[0].strip()
            event_type = get_event_type(event_name)

            # Determine sorting for event
            if event_name in MULTI_EVENT_LIST:
              sort_ascending = False  # for multi-events, higher total points are better
            elif event_name in FIELD_EVENT_LIST:
              sort_ascending = False  # for field events, higher distance/height is better
            else:
              # Running events: lower times are better
              sort_ascending = True

            records = []
            # Raw rows output (no ranks, no scores)
            for _, row in event_df.iterrows():
              athlete_name = f"{row['first_name']} {row['last_name']}".strip()
              rec = {
                  "team_name": row["team_name"].upper().strip() if isinstance(row["team_name"], str) else None,
                  "team_abbr": row["team_abbr"],
                  "athlete_id": int(row["athlete_id"]) if str(row["athlete_id"]).strip().isdigit() else None,
                  "athlete_name": athlete_name,
                  "sb_numeric": row["sb_numeric"],
                  "pb_numeric": row["pb_numeric"]
              }

              # Relay fix - for relays, team name becomes the full athlete name
              if event_type == 'relay':
                rec["team_name"] = athlete_name

              records.append(rec)

            nested_data[gender][event_num] = {
                'event_name': event_name,
                'event_type': event_type,
                'sort_ascending': sort_ascending,
                'event_results': records
            }

    return nested_data

def get_event_type(event_name: str) -> str:
    """
    Determine the type of event based on its name.

    Args:
        event_name: Name of the event (e.g., '60 Meter Dash', 'Shot Put', 'Decathlon').

    Returns:
        'running', 'field', or 'multi'
    """
    event_name_lower = event_name.lower()
    # Multi-events first
    for multi_event in MULTI_EVENT_LIST:
      if multi_event.lower() in event_name_lower:
        return 'multi'

    # Field events
    for field_event in FIELD_EVENT_LIST:
      if field_event.lower() in event_name_lower:
        return 'field'
        
    if 'relay' in event_name_lower or 'medley' in event_name_lower or 'dmr' in event_name_lower:
      return 'relay'

    # Otherwise, assume running
    return 'running'