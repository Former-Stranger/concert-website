#!/usr/bin/env python3
"""
Step 1: Extract raw data from Excel and perform basic validation
"""

import pandas as pd
import json
from pathlib import Path

def extract_raw_data(excel_path, output_path):
    """Extract data from Excel and save as JSON"""

    print("=" * 80)
    print("STEP 1: EXTRACTING RAW DATA")
    print("=" * 80)

    # Read Excel file
    df = pd.read_excel(excel_path)

    # Drop the empty column
    df = df.drop(columns=['Unnamed: 6'], errors='ignore')

    # Basic stats
    print(f"\nTotal rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    # Check for null values
    print("\nNull values per column:")
    print(df.isnull().sum())

    # Convert to records
    records = df.to_dict('records')

    # Save as JSON for inspection
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, default=str)

    print(f"\nSaved raw data to: {output_file}")
    print(f"Total records: {len(records)}")

    return records

if __name__ == "__main__":
    # Get paths relative to script location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    excel_path = project_root / "data" / "Original_List.xlsx"
    output_path = project_root / "data" / "raw_concerts.json"

    records = extract_raw_data(excel_path, output_path)
    print("\n✓ Step 1 complete!")
