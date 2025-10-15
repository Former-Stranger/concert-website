#!/usr/bin/env python3
"""
Master script to run all data cleaning and database generation steps
"""

import sys
import subprocess
from pathlib import Path

def run_script(script_name, description):
    """Run a Python script and handle errors"""
    print("\n" + "=" * 80)
    print(f"Running: {description}")
    print("=" * 80)

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {script_name} failed!")
        print(e.stdout)
        print(e.stderr)
        return False

def main():
    """Run all data cleaning steps in order"""

    print("=" * 80)
    print("CONCERT DATA CLEANING PIPELINE")
    print("=" * 80)

    scripts_dir = Path(__file__).parent

    steps = [
        ("1_extract_raw_data.py", "Step 1: Extract raw data from Excel"),
        ("2_normalize_artists.py", "Step 2: Normalize artist names"),
        ("3_normalize_venues.py", "Step 3: Normalize venue names"),
        ("4_validate_and_clean_dates.py", "Step 4: Validate and clean dates"),
        ("5_generate_database.py", "Step 5: Generate SQLite database"),
    ]

    for script, description in steps:
        script_path = scripts_dir / script
        if not script_path.exists():
            print(f"ERROR: Script not found: {script_path}")
            sys.exit(1)

        success = run_script(script_path, description)
        if not success:
            print(f"\n✗ Pipeline failed at: {description}")
            sys.exit(1)

    print("\n" + "=" * 80)
    print("✓ ALL STEPS COMPLETE!")
    print("=" * 80)
    print("\nDatabase generated at: concert-website/database/concerts.db")
    print("\nYou can now:")
    print("1. Query the database using SQLite")
    print("2. Build a web application to display the data")
    print("3. Generate statistics and visualizations")

if __name__ == "__main__":
    main()
