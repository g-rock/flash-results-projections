import pandas as pd
import glob
import json
import os

# Ensure target directory exists
output_dir = "../javascript/src/data"
os.makedirs(output_dir, exist_ok=True)

# Load and combine all input files
input_files = glob.glob("inputs/*.txt")
all_dfs = []

for file in input_files:
    df = pd.read_csv(file)

    # Strip whitespace from all string columns
    str_cols = df.select_dtypes(include='object').columns
    df[str_cols] = df[str_cols].apply(lambda x: x.str.strip())

    # Rename score column if needed
    if 'ind_score' in df.columns:
        df = df.rename(columns={'ind_score': 'score'})
    elif 'rel_score' in df.columns:
        df = df.rename(columns={'rel_score': 'score'})

    # Rename specific event names
    df['Event_name'] = df['Event_name'].replace({
        '400': '4x100',
        '1600': '4x400'
    })

    all_dfs.append(df)

# Combine all data into a single DataFrame
combined_df = pd.concat(all_dfs, ignore_index=True)

# If Stroke_name == 'H', append 'H' to Event_name
combined_df['Event_name'] = combined_df.apply(
    lambda row: f"{row['Event_name']}H" if str(row.get('Stroke_name', '')).strip() == 'H' else row['Event_name'],
    axis=1
)

# === Build full team scores by event ===
pivot_df = (
    combined_df.groupby(['Event_sex', 'Team_name', 'Event_name'])['score']
    .sum()
    .unstack(fill_value=0)
    .reset_index()
)

# Add TOTAL column
pivot_df['TOTAL'] = pivot_df.drop(columns=['Event_sex', 'Team_name']).sum(axis=1)

# Add Place (ranked by TOTAL within each gender)
pivot_df['Place'] = pivot_df.groupby('Event_sex')['TOTAL'].rank(method='min', ascending=False).astype(int)

# Rename Team_name -> school
pivot_df = pivot_df.rename(columns={'Team_name': 'school'})

# Split into men and women datasets
women_df = pivot_df[pivot_df['Event_sex'] == 'W'].drop(columns=['Event_sex'])
men_df = pivot_df[pivot_df['Event_sex'] == 'M'].drop(columns=['Event_sex'])

# Convert to records and save as JSON
women_data = women_df.to_dict(orient='records')
men_data = men_df.to_dict(orient='records')

print(output_dir)
with open(os.path.join(output_dir, "womenData.json"), "w") as wf:
    wf.write('hello')
    json.dump(women_data, wf, indent=2)

with open(os.path.join(output_dir, "menData.json"), "w") as mf:
    json.dump(men_data, mf, indent=2)

print("✅ Exported womenData.json and menData.json.")

# Separate event fields for men and women
women_events = sorted(combined_df[combined_df['Event_sex'] == 'W']['Event_name'].astype(str).unique())
men_events = sorted(combined_df[combined_df['Event_sex'] == 'M']['Event_name'].astype(str).unique())

def build_column_defs(event_list):
    defs = [{
        "headerName": "School",
        "field": "school",
        "pinned": "left",
        "width": 160
    }]
    defs += [{"field": event} for event in event_list]
    defs.append({
        "field": "TOTAL",
        "pinned": "right",
        "cellStyle": { "fontWeight": "bold" },
        "sort": "desc"
    })
    return defs

# Build column defs per gender
column_defs_women = build_column_defs(women_events)
column_defs_men = build_column_defs(men_events)

# Save both columnDefs
with open(os.path.join(output_dir, "columnDefs.women.json"), "w") as f:
    json.dump(column_defs_women, f, indent=2)

with open(os.path.join(output_dir, "columnDefs.men.json"), "w") as f:
    json.dump(column_defs_men, f, indent=2)

print("✅ Exported columnDefs.women.json and columnDefs.men.json.")
