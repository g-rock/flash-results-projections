import pandas as pd
import json
import os
import re

# Ensure target directory exists
output_dir = "./outputs"
js_dir = '../javascript/src/data'
os.makedirs(output_dir, exist_ok=True)
os.makedirs(js_dir, exist_ok=True)

# Define input file
input_file = "outputs/clean_start_list.csv"

# Load CSV
try:
    df = pd.read_csv(input_file)
    print(f"Successfully loaded {input_file}. Shape: {df.shape}")
except FileNotFoundError:
    print(f"Error: {input_file} not found.")
    exit()
except Exception as e:
    print(f"Error loading {input_file}: {e}")
    exit()

# Strip whitespace from all string columns
str_cols = df.select_dtypes(include='object').columns
df[str_cols] = df[str_cols].apply(lambda x: x.str.strip() if isinstance(x, str) else x)

# Rename columns
df = df.rename(columns={
    'Gender': 'Event_sex',
    'Team': 'Team_name',
    'Event Name': 'Event_name',
    'Col_11': 'multi_event_points'
})

# --- Keep only first multi-event subevents ---
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
print(f"Filtered to only the first Decathlon and Heptathlon events (if present). Remaining shape: {df.shape}")

# Rename first multi-events to "Heptathlon" and "Decathlon"
df.loc[df['Event_name'].str.contains(f'Dec .*{DECATHLON_FIRST_EVENT_SUFFIX}', regex=True, na=False), 'Event_name'] = 'Decathlon'
df.loc[df['Event_name'].str.contains(f'Hept .*{HEPTATHLON_FIRST_EVENT_SUFFIX}', regex=True, na=False), 'Event_name'] = 'Heptathlon'

# Strip Men/Women from Event_name for consistency
df['Event_name'] = df['Event_name'].str.replace(r'\b(Men|Women)\b\s*', '', regex=True).str.strip()

# --- Parse seed column ---
def parse_seed_for_sorting(seed_value, event_name):
    if pd.isna(seed_value) or not isinstance(seed_value, str):
        return None
    seed_str = seed_value.strip().lower()
    if ':' in seed_str:
        parts = seed_str.split(':')
        try:
            return float(parts[0]) * 60 + float(parts[1])
        except ValueError:
            pass
    if 'm' in seed_str or 'ft' in seed_str or '&frac' in seed_str:
        numeric_str = re.sub(r'[^\d\.\-]', '', seed_str)
        try:
            return float(numeric_str)
        except ValueError:
            pass
    try:
        return float(seed_str)
    except ValueError:
        return None

df['Seed_numeric'] = df['Seed'].apply(lambda x: parse_seed_for_sorting(x, None))


# Sorting rules (True = lower is better)
event_type_sorting_rules = {
    '4x100 M Relay': True, '1500 M': True, '110 M Hurdles': True, '100 M': True,
    '400 M': True, '800 M': True, '3000 M Steeple': True, '200 M': True,
    '10000 M': True, '4x400 M Relay': True, '4x100': True, '4x400': True,
    'Heptathlon': False,
    'Decathlon': False,
    'Hammer': False, 'Pole Vault': False, 'Javelin': False, 'Long Jump': False,
    'Shot Put': False, 'Discus': False, 'High Jump': False, 'Triple Jump': False,
}

df['is_lower_better'] = df['Event_name'].apply(lambda x: event_type_sorting_rules.get(x, True))
print("Parsed 'Seed' to 'Seed_numeric' and determined sorting direction.")

# Scoring system
POINTS_SYSTEM = {1: 10, 2: 8, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}

def assign_scores_with_ties(group):
    if group.empty:
        return pd.DataFrame()
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

print("Assigning scores with tie averaging logic...")
df = df.groupby(['Event_sex', 'Event_name'], group_keys=False).apply(assign_scores_with_ties)
print("✅ Score assignment with tie handling complete.")

# Output per-athlete event scores before pivoting
df.to_csv(os.path.join(output_dir, "per_athlete_event_scores.csv"), index=False)
print("✅ Exported per_athlete_event_scores.csv for review.")

# Build team totals
pivot_df = (
    df.groupby(['Event_sex', 'Team_name', 'Event_name'])['score']
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)
pivot_df['TOTAL'] = pivot_df.drop(columns=['Event_sex', 'Team_name'], errors='ignore').sum(axis=1)
pivot_df['Place'] = pivot_df.groupby('Event_sex')['TOTAL'].rank(method='min', ascending=False).astype(int)
pivot_df = pivot_df.rename(columns={'Team_name': 'school'})

# Filter gendered event columns strictly
all_event_cols = [col for col in pivot_df.columns if col not in ['Event_sex', 'Team_name', 'school', 'TOTAL', 'Place']]
core_cols = ['school', 'Place', 'TOTAL']

women_event_cols = [col for col in all_event_cols if col in df[df['Event_sex'] == 'Women']['Event_name'].unique()]
men_event_cols = [col for col in all_event_cols if col in df[df['Event_sex'] == 'Men']['Event_name'].unique()]

women_df = pivot_df[pivot_df['Event_sex'] == 'Women'].copy()
women_df = women_df[core_cols + women_event_cols]

men_df = pivot_df[pivot_df['Event_sex'] == 'Men'].copy()
men_df = men_df[core_cols + men_event_cols]

# Column definitions for AG Grid
women_events = sorted(df[df['Event_sex'] == 'Women']['Event_name'].unique())
men_events = sorted(df[df['Event_sex'] == 'Men']['Event_name'].unique())

def strip_gender(event_name):
    return re.sub(r'\b(Men|Women)\b\s*', '', event_name, flags=re.IGNORECASE).strip()
    
def build_column_defs(event_list, raw_event_list):
    defs = [{
        "headerName": "School",
        "field": "school",
        "pinned": "left",
        "width": 80
    }, {
        "headerName": "Place",
        "field": "Place",
        "width": 80,
        "pinned": "left",
    }, {
        "field": "TOTAL",
        "headerName": "Points",
        "pinned": "left",
        "cellStyle": { "fontWeight": "bold" },
        "sort": "desc",
        "width": 100,
        "valueFormatter": "x.toFixed(1)"
    }]
    
    defs += [{
        "field": raw, 
        "headerName": strip_gender(raw),
        "valueFormatter": "x.toFixed(1)"
    } for raw in raw_event_list]

    return defs

# Match display names to raw event columns
raw_women_events = sorted(df[df['Event_sex'] == 'Women']['Event_name'].unique())
raw_men_events = sorted(df[df['Event_sex'] == 'Men']['Event_name'].unique())

column_defs_women = build_column_defs(women_events, raw_women_events)
column_defs_men = build_column_defs(men_events, raw_men_events)


# Export JSON data
with open(os.path.join(js_dir, "womenData.json"), "w") as wf:
    json.dump(women_df.to_dict(orient='records'), wf, indent=2)
with open(os.path.join(js_dir, "menData.json"), "w") as mf:
    json.dump(men_df.to_dict(orient='records'), mf, indent=2)
with open(os.path.join(js_dir, "columnDefs.women.json"), "w") as f:
    json.dump(column_defs_women, f, indent=2)
with open(os.path.join(js_dir, "columnDefs.men.json"), "w") as f:
    json.dump(column_defs_men, f, indent=2)