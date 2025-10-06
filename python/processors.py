import os
import re
import json
import pandas as pd
from google.cloud import storage
from google.cloud import firestore
from google.oauth2 import service_account
from tempfile import NamedTemporaryFile

# -----------------------------
# GCS functions
# -----------------------------

def get_firestore_client(service_account_path):
    """
    Returns a Firestore client. 
    
    If service_account_path is provided, uses that key.
    Otherwise, uses default credentials (e.g., Cloud Run / GCP environment).
    """
    if service_account_path and os.path.isfile(service_account_path):
        creds = service_account.Credentials.from_service_account_file(service_account_path)
        return firestore.Client(credentials=creds, project=creds.project_id)
    else:
        # Use default credentials (works on GCP)
        return firestore.Client()

def upload_file_to_gcs(client, bucket_name, local_file_path, blob_name):
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_file_path)
    print(f"Uploaded '{blob_name}' to bucket '{bucket_name}'.")

def upload_json_to_gcs(client, bucket_name, blob_name, data):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
    print(f"Uploaded '{blob_name}' to bucket '{bucket_name}'.")

def get_blob_json(client, bucket_name, blob_name):
    """
    Fetch JSON content from a GCS blob and return it as a Python object.
    Raises FileNotFoundError if the blob does not exist.
    """
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    if not blob.exists():
        raise FileNotFoundError(f"Blob '{blob_name}' not found in bucket '{bucket_name}'")
    content = blob.download_as_text()
    return json.loads(content)
# -----------------------------
# Track meet functions
# -----------------------------

def process_merged_start_list(file_path: str):
    """
    Processes a local CSV file directly (no GCS download).
    
    Args:
        file_path: Path to the local CSV file.
    """
    print(f"Processing file: {file_path}")

    df_parsed = parse_track_event_data(os.path.dirname(file_path), os.path.basename(file_path))
    df_cleaned = clean_and_score(df_parsed)

    return df_cleaned

def parse_track_event_data(input_dir, input_filename):
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
    if max_data_cols_found >= 8:
        data_column_names[7] = 'Team'
    if max_data_cols_found >= 9:
        data_column_names[8] = 'Seed'

    final_columns = data_column_names + ['Gender', 'Event Name']
    df = pd.DataFrame(final_cleaned_rows_padded, columns=final_columns)
    if 'Team' in df.columns:
        df['Team'] = df['Team'].apply(lambda x: str(x).split(' ')[0] if pd.notna(x) and str(x).strip() else '')
    return df

def clean_and_score(df):
    df = df.rename(columns={
        'Gender': 'Event_sex',
        'Team': 'Team_name',
        'Event Name': 'Event_name',
        'Col_11': 'multi_event_points'
    })

    DECATHLON_FIRST_EVENT_SUFFIX = '100 M'
    HEPTATHLON_FIRST_EVENT_SUFFIX = '100 M Hurdles'

    is_decathlon = df['Event_name'].str.contains(r'^Dec ', na=False)
    is_heptathlon = df['Event_name'].str.contains(r'^Hept ', na=False)

    keep_mask = (
        (~is_decathlon & ~is_heptathlon) |
        (is_decathlon & df['Event_name'].str.contains(f'Dec .*{DECATHLON_FIRST_EVENT_SUFFIX}', regex=True, na=False)) |
        (is_heptathlon & df['Event_name'].str.contains(f'Hept .*{HEPTATHLON_FIRST_EVENT_SUFFIX}', regex=True, na=False))
    )
    df = df[keep_mask].copy()
    df.loc[df['Event_name'].str.contains(f'Dec .*{DECATHLON_FIRST_EVENT_SUFFIX}', regex=True, na=False), 'Event_name'] = 'Decathlon'
    df.loc[df['Event_name'].str.contains(f'Hept .*{HEPTATHLON_FIRST_EVENT_SUFFIX}', regex=True, na=False), 'Event_name'] = 'Heptathlon'
    df['Event_name'] = df['Event_name'].str.replace(r'\b(Men|Women)\b\s*', '', regex=True).str.strip()

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

    df['Seed_numeric'] = df['Seed'].apply(parse_seed)

    # Sorting rules
    event_type_sorting_rules = {
        '4x100 M Relay': True, '1500 M': True, '110 M Hurdles': True, '100 M': True,
        '400 M': True, '800 M': True, '3000 M Steeple': True, '200 M': True,
        '10000 M': True, '4x400 M Relay': True, '4x100': True, '4x400': True,
        'Heptathlon': False, 'Decathlon': False,
        'Hammer': False, 'Pole Vault': False, 'Javelin': False, 'Long Jump': False,
        'Shot Put': False, 'Discus': False, 'High Jump': False, 'Triple Jump': False,
    }
    df['is_lower_better'] = df['Event_name'].apply(lambda x: event_type_sorting_rules.get(x, True))

    # Scoring
    POINTS_SYSTEM = {1: 10, 2: 8, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
    def assign_scores(group):
        if group.empty:
            return group
        ascending = group['is_lower_better'].iloc[0]
        group = group.sort_values(by='Seed_numeric', ascending=ascending).copy()
        group['Rank'] = group['Seed_numeric'].rank(method='min', ascending=ascending, na_option='bottom')
        scores = []
        grouped_by_rank = group.groupby('Rank')
        for rank_value, tied_rows in grouped_by_rank:
            rank_value = int(rank_value)
            if rank_value > 8:
                score = 0
            else:
                num_tied = len(tied_rows)
                ranks_involved = list(range(rank_value, rank_value + num_tied))
                total_points = sum(POINTS_SYSTEM.get(r, 0) for r in ranks_involved)
                score = total_points / num_tied
            scores.extend([score] * len(tied_rows))
        group['score'] = scores
        return group

    df = df.groupby(['Event_sex', 'Event_name'], group_keys=False).apply(assign_scores)

    # Build team totals
    pivot_df = df.groupby(['Event_sex', 'Team_name', 'Event_name'])['score'].sum().unstack(fill_value=0).reset_index()
    pivot_df['TOTAL'] = pivot_df.drop(columns=['Event_sex', 'Team_name'], errors='ignore').sum(axis=1)
    pivot_df['Place'] = pivot_df.groupby('Event_sex')['TOTAL'].rank(method='min', ascending=False).astype(int)
    pivot_df = pivot_df.rename(columns={'Team_name': 'school'})
    all_event_cols = [col for col in pivot_df.columns if col not in ['Event_sex', 'school', 'TOTAL', 'Place']]

    # Wrap projected/actual
    # def wrap_with_projected(df, event_cols):
    #     for col in event_cols:
    #         df[col] = df[col].apply(lambda x: {"projected": float(x) if pd.notna(x) else 0, "actual": 0})
    #     for col in ["TOTAL", "Place"]:
    #         df[col] = df[col].apply(lambda x: {"projected": float(x) if pd.notna(x) else 0, "actual": 0})
    #     return df

    # women_df = wrap_with_projected(pivot_df[pivot_df['Event_sex'] == 'Women'].copy(), [c for c in all_event_cols if c in df[df['Event_sex']=='Women']['Event_name'].unique()])
    # men_df = wrap_with_projected(pivot_df[pivot_df['Event_sex'] == 'Men'].copy(), [c for c in all_event_cols if c in df[df['Event_sex']=='Men']['Event_name'].unique()])

    return df

def build_column_defs(df, gender):
    events = sorted(df[df['Event_sex'] == gender]['Event_name'].unique())
    def strip_gender(name):
        return re.sub(r'\b(Men|Women)\b\s*', '', name, flags=re.IGNORECASE).strip()
    defs = [
        {"headerName": "School", "field": "school", "pinned": "left", "width": 80},
        {"headerName": "Place", "field": "Place", "width": 80, "pinned": "left"},
        {"field": "TOTAL", "headerName": "Points", "pinned": "left", "cellStyle": {"fontWeight": "bold"}, "sort": "desc", "width": 100, "valueFormatter": "x.toFixed(1)"}
    ]
    defs += [{"field": e, "headerName": strip_gender(e), "valueFormatter": "x.toFixed(1)"} for e in events]
    return defs