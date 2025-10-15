#!/usr/bin/env python3
"""
Step 4: Validate and clean dates
"""

import json
from pathlib import Path
from datetime import datetime

def clean_date(date_value):
    """
    Clean and standardize date values.
    Returns: (iso_date_string, has_issue, issue_note)
    """
    if not date_value or (isinstance(date_value, float) and pd.isna(date_value)):
        return None, True, "Missing date"

    date_str = str(date_value)

    # Handle TBD
    if date_str.upper() == 'TBD':
        return None, True, "Date TBD"

    # Handle ambiguous dates
    if ',' in date_str or ' or ' in date_str:
        return None, True, f"Ambiguous date: {date_str}"

    # Try to parse date
    try:
        # If already in ISO format from pandas
        if 'T' in date_str or len(date_str) == 19:
            dt = datetime.fromisoformat(date_str.replace(' ', 'T').split('.')[0])
            return dt.date().isoformat(), False, None

        # Try other formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.date().isoformat(), False, None
            except ValueError:
                continue

        # Could not parse
        return None, True, f"Could not parse: {date_str}"

    except Exception as e:
        return None, True, f"Parse error: {str(e)}"

def validate_dates(input_path, output_path):
    """Validate and clean all dates"""

    print("=" * 80)
    print("STEP 4: VALIDATING AND CLEANING DATES")
    print("=" * 80)

    # Load data
    with open(input_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    # Track issues
    clean_dates = 0
    issues = []
    future_concerts = 0
    today = datetime.now().date()

    # Process each record
    for idx, record in enumerate(records):
        date_value = record.get('DATE')

        clean, has_issue, note = clean_date(date_value)

        record['date_clean'] = clean
        record['date_has_issue'] = has_issue

        if has_issue:
            record['date_issue'] = note
            issues.append({
                'row': idx,
                'original': date_value,
                'issue': note
            })
        else:
            record['date_issue'] = None
            clean_dates += 1

            # Check if future concert
            if clean:
                concert_date = datetime.fromisoformat(clean).date()
                if concert_date > today:
                    future_concerts += 1
                    record['attended'] = False
                else:
                    record['attended'] = True

    # Save cleaned data
    output_file = Path(output_path)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, default=str)

    print(f"\nDate validation complete:")
    print(f"  Clean dates: {clean_dates}")
    print(f"  Dates with issues: {len(issues)}")
    print(f"  Future concerts: {future_concerts}")

    if issues:
        print(f"\nDate issues found:")
        for issue in issues[:10]:
            print(f"  Row {issue['row']}: {issue['original']} - {issue['issue']}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more")

    print(f"\nSaved cleaned data to: {output_file}")

    return records

if __name__ == "__main__":
    import pandas as pd
    from pathlib import Path

    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    input_path = project_root / "data" / "normalized_venues.json"
    output_path = project_root / "data" / "cleaned_concerts.json"

    records = validate_dates(input_path, output_path)
    print("\n✓ Step 4 complete!")
