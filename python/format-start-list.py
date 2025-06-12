import pandas as pd
import re
import os

def parse_track_event_data(input_dir, input_filename, output_csv_path):
    """
    Parses a track event file, extracting Gender and Event Name from
    header rows and cleaning the data.
    - Header identification: `;;StartList` line.
    - Header data line (2nd of 5): comma-separated.
    - Data rows: comma-separated, with fields potentially containing spaces or quotes.

    Args:
        input_dir (str): The directory where the input file is located.
        input_filename (str): The name of the input file.
        output_csv_path (str): The path to save the cleaned output CSV file.
    """
    input_csv_path = os.path.join(input_dir, input_filename)

    cleaned_rows = []
    current_gender = None
    current_event_name = None
    header_block_size = 5 # Total number of header rows for each event
    
    in_header_block = False
    header_lines_processed_in_block = 0 

    print(f"Attempting to open file: {input_csv_path}")
    if not os.path.exists(input_csv_path):
        print(f"Error: File not found at '{input_csv_path}'. Please check the path and ensure the 'inputs' directory exists if you're using it.")
        return

    try:
        with open(input_csv_path, 'r', encoding='utf-8') as f: 
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file '{input_csv_path}': {e}")
        return

    print(f"Successfully read {len(lines)} lines from the file.")

    i = 0
    max_data_cols_found = 0 # Track max columns ONLY for the actual data part
    
    while i < len(lines):
        raw_line_stripped = lines[i].strip()

        # Debug prints are commented out for cleaner output, but can be re-enabled if needed
        # print(f"\n--- Processing line {i} ---")
        # print(f"Raw line (stripped): '{raw_line_stripped}'")
        
        # For header identification: normalize whitespace first
        normalized_for_header_check = ' '.join(raw_line_stripped.split()).strip()

        if normalized_for_header_check.startswith(";;StartList"):
            # print(f"MATCH: Found ';;StartList' at line {i}. Starting new header block.")
            in_header_block = True
            header_lines_processed_in_block = 0 
            current_gender = None 
            current_event_name = None 
            i += 1 
            continue 

        if in_header_block:
            header_lines_processed_in_block += 1
            # print(f"  Inside header block. Processed lines so far: {header_lines_processed_in_block}")
            
            # This is the second logical line of the 5-row header block (after `;;StartList`)
            if header_lines_processed_in_block == 1: 
                # print(f"  IDENTIFYING EVENT: Parsing event details from header line {i}: '{raw_line_stripped}'")
                
                # This header line is consistently comma-separated.
                parts_by_comma = raw_line_stripped.split(',')
                
                event_description_cell = None
                if len(parts_by_comma) > 2: # Check if the 3rd column (index 2) exists
                    # Normalize spacing within the cell content before splitting by space for gender/event name
                    event_description_cell = ' '.join(parts_by_comma[2].split()).strip()

                if event_description_cell:
                    words_in_cell = event_description_cell.split() 
                    
                    gender_word_index = -1
                    potential_gender = None

                    # Find the position of the gender word ("Men" or "Women")
                    for k, word_in_cell in enumerate(words_in_cell):
                        if word_in_cell == "Men":
                            potential_gender = "Men"
                            gender_word_index = k
                            break
                        elif word_in_cell == "Women":
                            potential_gender = "Women"
                            gender_word_index = k
                            break
                    
                    if gender_word_index != -1: # If gender word is found
                        current_gender = potential_gender
                        
                        full_event_name_parts = []
                        
                        # Add words before the gender word (e.g., "Dec", "Hept")
                        full_event_name_parts.extend(words_in_cell[:gender_word_index])
                        
                        # Add the gender word itself
                        full_event_name_parts.append(words_in_cell[gender_word_index])
                        
                        # Add words after gender word until a stop word (phase/time)
                        for k in range(gender_word_index + 1, len(words_in_cell)):
                            word_after_gender = words_in_cell[k]
                            if word_after_gender in ["Prelims", "Finals", "Semifinals", "Heats", "Qualifying"] or re.match(r'\d{1,2}:\d{2}', word_after_gender):
                                break # Stop at phase/time indicator
                            full_event_name_parts.append(word_after_gender)
                        
                        current_event_name = " ".join(full_event_name_parts).strip()
                    else: # Gender word not found, fallback
                        current_gender = "Unknown" 
                        event_name_parts_fallback = []
                        for word in words_in_cell:
                            if word in ["Prelims", "Finals", "Semifinals", "Heats", "Qualifying"] or re.match(r'\d{1,2}:\d{2}', word):
                                break
                            event_name_parts_fallback.append(word)
                        current_event_name = " ".join(event_name_parts_fallback).strip() or event_description_cell 
                else:
                    current_gender = "Unknown"
                    current_event_name = "Unknown Event"
                
                # print(f"  Extracted Gender: '{current_gender}', Event Name: '{current_event_name}'")

                if not current_gender or not current_event_name:
                    print(f"  WARNING: Could not fully extract gender or event name from line '{raw_line_stripped}'")


            # After processing the necessary header lines, set in_header_block to False
            if header_lines_processed_in_block >= header_block_size - 1:
                in_header_block = False
                # print(f"  END HEADER BLOCK: Finished processing header block at line {i}. Next lines will be data.")
            
            i += 1
            continue 
        
        # If not in a header block, and line is not empty, and we have event details, it's a data row
        if not in_header_block and raw_line_stripped and current_gender and current_event_name:
            # Data rows are confirmed to be comma-separated.
            row_data_parts = [item.strip() for item in raw_line_stripped.split(',')]
            
            if len(row_data_parts) > max_data_cols_found:
                max_data_cols_found = len(row_data_parts)

            cleaned_rows.append(row_data_parts + [current_gender, current_event_name])
            # print(f"  DATA ROW: Added data row (first 3 parts): {row_data_parts[:3]}... with '{current_gender}', '{current_event_name}'")
        
        i += 1

    if not cleaned_rows:
        print(f"\n--- FINAL RESULT ---")
        print(f"No data was extracted from '{input_csv_path}'. Check file format and parsing logic or provided sample.")
        return

    # After processing all rows, go back and pad all rows to the `max_data_cols_found`
    final_cleaned_rows_padded = []
    for row_original in cleaned_rows:
        data_parts_from_split = row_original[:-2] 
        gender = row_original[-2]
        event_name = row_original[-1]
        
        padded_data_parts = data_parts_from_split + [''] * (max_data_cols_found - len(data_parts_from_split))
        
        final_cleaned_rows_padded.append(padded_data_parts + [gender, event_name])

    data_column_names = [f"Col_{idx+1}" for idx in range(max_data_cols_found)] 
      
    # Rename specific columns as requested
    if max_data_cols_found >= 8:  
        data_column_names[7] = 'Team' 
    else: 
        print(f"Warning: Not enough columns found to rename Col_8 to 'Team'. Max data columns: {max_data_cols_found}") 

    if max_data_cols_found >= 9:  
        data_column_names[8] = 'Seed' 
    else: 
        print(f"Warning: Not enough columns found to rename Col_9 to 'Seed'. Max data columns: {max_data_cols_found}") 
      
    # Do NOT rename Col_6 to 'Result' here. 'Result' will be handled in the second script.
    
    final_columns = data_column_names + ['Gender', 'Event Name'] 

    df = pd.DataFrame(final_cleaned_rows_padded, columns=final_columns) 
      
    # Clean the 'Team' column: keep only the first word 
    if 'Team' in df.columns: 
        df.loc[:, 'Team'] = df['Team'].apply(lambda x: str(x).split(' ')[0] if pd.notna(x) and str(x).strip() else '') 
    else: 
        print(f"\n'Team' column not found for cleaning. This might be due to previous warnings about column count.") 

    # Save to CSV. Pandas will automatically handle quoting fields that contain commas.
    df.to_csv(output_csv_path, index=False)
    print(f"\n--- SCRIPT 1 RESULT ---")
    print(f"Cleaned data saved to '{output_csv_path}'")
    print(f"Total rows extracted: {len(df)}")
    print(f"First 5 rows of cleaned data:\n{df.head()}")
# Example usage:
# Assuming 'mergedStartList.csv' is in the same directory as your Python script.
input_directory = 'inputs' 
input_file_name = 'mergedStartList.csv'
output_file = 'outputs/clean_start_list.csv'

parse_track_event_data(input_directory, input_file_name, output_file)