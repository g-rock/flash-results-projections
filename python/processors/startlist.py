import os
import re
import pandas as pd
from processors.gcs import get_firestore_client, slugify
from .constants import HIGHER_MARK_BETTER_LIST, POINTS_SYSTEM

def process_merged_start_list(
    file_path: str,
    meet_year: str,
    meet_id: str,
    meet_name: str,
    meet_season: str = None,
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

    # --- Parse CSV and score ---
    df_parsed = parse_start_list(os.path.dirname(file_path), os.path.basename(file_path))
    scored_data_by_gender = clean_and_score_start_list(df_parsed)

    # --- Firestore reference ---
    db = get_firestore_client()
    meet_year = str(meet_year)
    meet_ref = db.collection("years").document(meet_year).collection("meets").document(meet_id)

    # --- Set basic meet info ---
    meet_ref.set({
        "name": meet_name,
        "id": meet_id,
        "year": meet_year,
        "date": meet_date,
        "location": meet_location,
        "season": meet_season
    })

    # --- Upload scored data per gender and event ---
    for gender, events in scored_data_by_gender.items():
        gender_key = slugify(gender)
        gender_collection_ref = meet_ref.collection(gender_key)
        for event_name, event_data in events.items():
            event_name_key = slugify(event_name)
            event_doc_ref = gender_collection_ref.document(event_name_key)
            event_doc_ref.set({
                "gender": gender,
                "event_name": event_name,
                "projections": {
                    "round_results": event_data,
                    "round_status": 'official'
                }
            })

    return "Upload complete"


def parse_start_list(input_dir, input_filename):
    input_csv_path = os.path.join(input_dir, input_filename)
    cleaned_rows = []
    current_gender = None
    current_event_name = None
    header_block_size = 5
    in_header_block = False
    header_lines_processed_in_block = 0

    if not os.path.exists(input_csv_path):
      raise FileNotFoundError(f"File not found: {input_csv_path}")

    with open(input_csv_path, 'r', encoding='utf-8') as f:
      lines = f.readlines()

    i = 0
    max_data_cols_found = 0

    while i < len(lines):
        raw_line_stripped = lines[i].strip()
        normalized_for_header_check = ' '.join(raw_line_stripped.split()).strip()

        # Detect header
        if normalized_for_header_check.startswith(";;StartList"):
            in_header_block = True
            header_lines_processed_in_block = 0
            current_gender = None
            current_event_name = None
            i += 1
            continue

        if in_header_block:
            header_lines_processed_in_block += 1
            if header_lines_processed_in_block == 1:
                # Extract event name and gender
                parts_by_comma = raw_line_stripped.split(',')
                event_description_cell = None
                if len(parts_by_comma) > 2:
                    event_description_cell = ' '.join(parts_by_comma[2].split()).strip()
                if event_description_cell:
                    words_in_cell = event_description_cell.split()
                    gender_word_index = -1
                    potential_gender = None
                    for k, word_in_cell in enumerate(words_in_cell):
                        if word_in_cell in ["Men", "Women"]:
                            potential_gender = word_in_cell
                            gender_word_index = k
                            break
                    if gender_word_index != -1:
                        current_gender = potential_gender
                        full_event_name_parts = words_in_cell[:gender_word_index + 1]
                        for k in range(gender_word_index + 1, len(words_in_cell)):
                            if words_in_cell[k] in ["Prelims", "Finals", "Semifinals", "Heats", "Qualifying"] or re.match(r'\d{1,2}:\d{2}', words_in_cell[k]):
                                break
                            full_event_name_parts.append(words_in_cell[k])
                        current_event_name = " ".join(full_event_name_parts).strip()
                    else:
                        current_gender = "Unknown"
                        current_event_name = event_description_cell
                else:
                    current_gender = "Unknown"
                    current_event_name = "Unknown Event"
            if header_lines_processed_in_block >= header_block_size - 1:
                in_header_block = False
            i += 1
            continue

        # Process data row
        if not in_header_block and raw_line_stripped and current_gender and current_event_name:
            row_data_parts = [item.strip() for item in raw_line_stripped.split(',')]
            if len(row_data_parts) > max_data_cols_found:
                max_data_cols_found = len(row_data_parts)
            cleaned_rows.append(row_data_parts + [current_gender, current_event_name])

        i += 1

    # Pad rows to same length
    final_cleaned_rows_padded = []
    for row in cleaned_rows:
        data_parts = row[:-2]
        gender, event_name = row[-2], row[-1]
        padded_data_parts = data_parts + [''] * (max_data_cols_found - len(data_parts))
        final_cleaned_rows_padded.append(padded_data_parts + [gender, event_name])

    # Column names
    data_column_names = [f"Col_{idx+1}" for idx in range(max_data_cols_found)]
    if max_data_cols_found >= 5:
        data_column_names[4] = 'Team_name'
    if max_data_cols_found >= 8:
        data_column_names[7] = 'Team_abbr'
    if max_data_cols_found >= 9:
        data_column_names[8] = 'Seed'

    final_columns = data_column_names + ['Gender', 'Event Name']
    df = pd.DataFrame(final_cleaned_rows_padded, columns=final_columns)
    if 'Team_abbr' in df.columns:
      df['Team_abbr'] = df['Team_abbr'].apply(lambda x: str(x) if pd.notna(x) and str(x).strip() else '')
    if 'Team_name' in df.columns:
      df['Team_name'] = df['Team_name'].apply(lambda x: str(x).upper() if pd.notna(x) and str(x).strip() else '')
    df = df[df['Col_1'] != 'N']
    return df

def clean_and_score_start_list(df):
    # Rename columns
    df = df.rename(columns={
        'Gender': 'event_gender',
        'Team_abbr': 'team_abbr',
        'Team_name': 'team_name',
        'Event Name': 'event_name',
        'Col_3': 'first_name',
        'Col_4': 'last_name',
        'Col_7': 'team_name',
        'Col_11': 'multi_event_points',
    })

    is_pentathlon = df['event_name'].str.startswith('Pen', na=False)
    is_decathlon = df['event_name'].str.startswith('Dec', na=False)
    is_heptathlon = df['event_name'].str.startswith('Hept', na=False)

    def get_first_event(df, mask):
        if not mask.any():
            return None
        # Get the first row where the mask is True
        first_idx = df.index[mask].min()
        return df.loc[first_idx, 'event_name']

    first_pentathlon_event = get_first_event(df, is_pentathlon)
    first_decathlon_event = get_first_event(df, is_decathlon)
    first_heptathlon_event = get_first_event(df, is_heptathlon)

    # Keep only the first event for combined events, or all other events
    keep_mask = (
        (~is_decathlon & ~is_heptathlon & ~is_pentathlon) |
        (is_decathlon & (df['event_name'] == first_decathlon_event)) |
        (is_heptathlon & (df['event_name'] == first_heptathlon_event)) |
        (is_pentathlon & (df['event_name'] == first_pentathlon_event))
    )

    df = df[keep_mask].copy()

    # Rename the first events of combined events to the general event name
    df.loc[df['event_name'] == first_decathlon_event, 'event_name'] = 'Decathlon'
    df.loc[df['event_name'] == first_heptathlon_event, 'event_name'] = 'Heptathlon'
    df.loc[df['event_name'] == first_pentathlon_event, 'event_name'] = 'Pentathlon'
    
    df['event_name'] = df['event_name'].str.replace(r'\b(Men|Women)\b\s*', '', regex=True).str.strip()

    # Parse Seed
    def parse_seed(seed_value):
        if pd.isna(seed_value) or not isinstance(seed_value, str):
            return None
        seed_str = seed_value.strip().lower()
        if ':' in seed_str:
            parts = seed_str.split(':')
            try:
                return float(parts[0]) * 60 + float(parts[1])
            except ValueError:
                return None
        if 'm' in seed_str or 'ft' in seed_str or '&frac' in seed_str:
            numeric_str = re.sub(r'[^\d\.\-]', '', seed_str)
            try:
                return float(numeric_str)
            except ValueError:
                return None
        try:
            return float(seed_str)
        except ValueError:
            return None

    df['seed_numeric'] = df['Seed'].apply(parse_seed)

    # Sorting rules
    df['is_lower_better'] = df['event_name'].apply(lambda x: False if x in HIGHER_MARK_BETTER_LIST else True)
    # Assign rank and score
    def assign_scores(group):
      ascending = group['is_lower_better'].iloc[0]
      group = group.sort_values(by='seed_numeric', ascending=ascending).copy()
      
      # Drop exact duplicate athlete rows
      group = group.drop_duplicates(subset=['first_name', 'last_name', 'team_name'])
      
      # Assign places
      group['place'] = group['seed_numeric'].rank(
          method='min', ascending=ascending, na_option='bottom'
      ).astype(int)
      
      # Assign scores
      scores = []
      grouped_by_place = group.groupby('place')
      for place, tied_rows in grouped_by_place:
          if place > 8:
              score = 0
          else:
              num_tied = len(tied_rows)
              ranks_involved = list(range(place, place + num_tied))
              total_points = sum(POINTS_SYSTEM.get(r, 0) for r in ranks_involved)
              score = total_points / num_tied
          scores.extend([score] * len(tied_rows))
      group['score'] = scores
      
      # Create athlete full name
      group['athlete'] = group['first_name'] + ' ' + group['last_name']
      
      return group[['team_name', 'team_abbr', 'score', 'place', 'athlete']]

    nested_data = {}
    for gender in df['event_gender'].unique():
        nested_data[gender] = {}
        events = df[df['event_gender'] == gender]['event_name'].unique()
        for event in events:
          # Filter by both gender and event name
          event_df = df[(df['event_gender'] == gender) & (df['event_name'] == event)]
          scored_df = assign_scores(event_df)

          # Convert to list of dicts
          records = scored_df.to_dict(orient='records')

          for r in records:
              # If it's a relay, set team_name = athlete
              if 'relay' in event.lower():
                  r['team_name'] = r.get('athlete', '').strip()
              # Always make team_name uppercase
              if 'team_name' in r and isinstance(r['team_name'], str):
                  r['team_name'] = r['team_name'].upper().strip()

          nested_data[gender][event] = records
    return nested_data
