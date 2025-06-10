import pandas as pd
import glob
import json
import os
import re

# Ensure target directory exists
# Changed output_dir to a local directory that should have write permissions
output_dir = "./js_data" # This will create 'js_data' folder in the current directory
os.makedirs(output_dir, exist_ok=True)

# Define the input file from the previous step
input_file = "js_data/cleaned_track_data.csv"

# Load the cleaned_track_data.csv file
try:
    df = pd.read_csv(input_file)
    print(f"Successfully loaded {input_file}. Shape: {df.shape}")
    print(f"Columns in loaded DataFrame: {df.columns.tolist()}")
except FileNotFoundError:
    print(f"Error: {input_file} not found. Please ensure it's in the same directory as the script.")
    exit()
except Exception as e:
    print(f"Error loading {input_file}: {e}")
    exit()

# --- Initial Column Mapping and Data Cleaning ---

# Strip whitespace from all string columns
str_cols = df.select_dtypes(include='object').columns
df[str_cols] = df[str_cols].apply(lambda x: x.str.strip() if isinstance(x, str) else x) 

# Check if 'Team' and 'Seed' columns exist after parsing and renaming
# (These would have been set in the previous code for cleaned_track_data.csv)
if 'Team' not in df.columns or 'Seed' not in df.columns:
    print("Error: 'Team' or 'Seed' columns not found in the input CSV. Please ensure the 'cleaned_track_data.csv' was generated correctly with these columns.")
    print(f"Current columns: {df.columns.tolist()}")
    exit()

# Map columns from cleaned_track_data.csv to expected names in the script
df = df.rename(columns={
    'Gender': 'Event_sex',
    'Team': 'Team_name',
    'Event Name': 'Event_name'
})


# Function to parse seed values for sorting
def parse_seed_for_sorting(seed_value, event_name):
    if pd.isna(seed_value) or not isinstance(seed_value, str):
        return None # Return None for NaN or non-string values

    seed_str = str(seed_value).strip().lower()

    # Rule 1: Handle times (MM:SS.ss or SS.ss)
    if ':' in seed_str:
        parts = seed_str.split(':')
        try:
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds # Times are in seconds (lower is better)
        except ValueError:
            pass # Fall through to other parsing

    # Rule 2: Handle distances/heights with units (e.g., 68.76m, 225-7, 17-9&frac12;)
    # This is a simplified approach. A full robust solution would handle all unit conversions
    # (e.g., convert feet/inches to meters, fractions to decimals).
    # For now, we try to extract the numeric part.
    if 'm' in seed_str or 'ft' in seed_str or '&frac' in seed_str: 
        # Remove common unit suffixes and fractions for numeric conversion
        # This will convert "17-9&frac12;" to "179" which is not ideal, but converts to a number.
        numeric_str = re.sub(r'[^\d\.\-]', '', seed_str) 
        try:
            return float(numeric_str) # Assume numeric value (higher is better for distances/heights)
        except ValueError:
            pass
    
    # Rule 3: Assume it's a plain number (seconds or generic)
    try:
        return float(seed_str) 
    except ValueError:
        return None # Cannot parse

# Categorize event types for sorting (lower value is better vs higher value is better)
# This mapping is crucial for correct ranking based on 'Seed' values.
# Add more events as needed based on your 'Event_name' data.
event_type_sorting_rules = {
    # Time events (lower value is better, ascending=True in rank)
    '4x100 M Relay': True, '1500 M': True, '110 M Hurdles': True, '100 M': True,
    '400 M': True, '800 M': True, '3000 M Steeple': True, '200 M': True,
    '10000 M': True, '4x400 M Relay': True, '4x100': True, '4x400': True,
    'Hept Women 800 M': True, # Part of Heptathlon, but is a time event
    
    # Field events (higher value is better, ascending=False in rank)
    'Hammer': False, 'Pole Vault': False, 'Javelin': False, 'Long Jump': False,
    'Shot Put': False, 'Discus': False, 'High Jump': False, 'Triple Jump': False,
}

# Apply parsing to create 'Seed_numeric'
df['Seed_numeric'] = df['Seed'].apply(lambda x: parse_seed_for_sorting(x, None)) # event_name not used in parser for sorting direction

# Determine 'is_lower_better' flag for each row based on event type
df['is_lower_better'] = df['Event_name'].apply(lambda x: event_type_sorting_rules.get(x, True)) 

print("Parsed 'Seed' to 'Seed_numeric' and determined sorting direction.")

# Calculate rank within each event (Event_sex, Event_name)
def get_rank_within_group(group):
    if group.empty:
        return pd.Series([], dtype='float64') 

    # All rows within a group should have the same 'is_lower_better' flag
    ascending = group['is_lower_better'].iloc[0]
    
    # Use na_option='bottom' to always put NaNs at the highest rank number
    return group['Seed_numeric'].rank(method='min', ascending=ascending, na_option='bottom')

# Apply ranking by grouping and then applying the function
df['Rank'] = df.groupby(['Event_sex', 'Event_name']).apply(get_rank_within_group).reset_index(level=[0,1], drop=True)

print(df.head())
print("Calculated 'Rank' for each entry.")

# Define scoring points based on rank
rank_points = {
    1.0: 10, # Use float keys as rank can be float initially due to ties
    2.0: 8,
    3.0: 6,
    4.0: 5,
    5.0: 4,
    6.0: 3,
    7.0: 2,
    8.0: 1
}

# Calculate score based on rank
df['score'] = df['Rank'].map(rank_points).fillna(0).astype(int)
print("Calculated 'score' based on 'Rank'.")


# === Build full team scores by event ===
pivot_df = (
    df.groupby(['Event_sex', 'Team_name', 'Event_name'])['score']
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)
print("Built pivot_df (team scores by event).")

# Add TOTAL column
pivot_df['TOTAL'] = pivot_df.drop(columns=['Event_sex', 'Team_name'], errors='ignore').sum(axis=1) # Use Team_name here
print("Added 'TOTAL' column to pivot_df.")

# Add Place (ranked by TOTAL within each gender)
pivot_df['Place'] = pivot_df.groupby('Event_sex')['TOTAL'].rank(method='min', ascending=False).astype(int)
print("Added 'Place' column to pivot_df.")

# Rename Team_name -> school
pivot_df = pivot_df.rename(columns={'Team_name': 'school'})
print("Renamed 'Team_name' to 'school' in pivot_df.")

# Split into men and women datasets
women_df = pivot_df[pivot_df['Event_sex'] == 'Women'].drop(columns=['Event_sex'])
men_df = pivot_df[pivot_df['Event_sex'] == 'Men'].drop(columns=['Event_sex'])
print("Split data into women_df and men_df.")

# Convert to records and save as JSON
women_data = women_df.to_dict(orient='records')
men_data = men_df.to_dict(orient='records')

print(f"Output directory: {output_dir}")
with open(os.path.join(output_dir, "womenData.json"), "w") as wf:
    json.dump(women_data, wf, indent=2)

with open(os.path.join(output_dir, "menData.json"), "w") as mf:
    json.dump(men_data, mf, indent=2)

print("✅ Exported womenData.json and menData.json.")

# Separate event fields for men and women
women_events = sorted(df[df['Event_sex'] == 'Women']['Event_name'].astype(str).unique())
men_events = sorted(df[df['Event_sex'] == 'Men']['Event_name'].astype(str).unique())
print("Collected unique event names for column definitions.")

def build_column_defs(event_list):
    defs = [{
        "headerName": "School",
        "field": "school",
        "pinned": "left",
        "width": 160
    }]
    # Add a Place column definition first, before individual events
    defs.append({
        "headerName": "Place",
        "field": "Place",
        "width": 80,
        "pinned": "left",
        "sort": "asc",
        "cellStyle": { "fontWeight": "bold" }
    })
    defs += [{"field": event} for event in event_list]
    defs.append({
        "field": "TOTAL",
        "headerName": "Total", # Ensure headerName for TOTAL
        "pinned": "right",
        "cellStyle": { "fontWeight": "bold" },
        "sort": "desc"
    })
    return defs

# Build column defs per gender
column_defs_women = build_column_defs(women_events)
column_defs_men = build_column_defs(men_events)
print("Built column definitions for women and men events.")

# Save both columnDefs
with open(os.path.join(output_dir, "columnDefs.women.json"), "w") as f:
    json.dump(column_defs_women, f, indent=2)

with open(os.path.join(output_dir, "columnDefs.men.json"), "w") as f:
    json.dump(column_defs_men, f, indent=2)

print("✅ Exported columnDefs.women.json and columnDefs.men.json.")