# Concert Database Project

Transform 35 years of concert data into a clean, searchable database and website.

## Project Overview

This project processes an Excel spreadsheet containing 1,292 concerts attended over 35 years, cleaning and normalizing the data to enable powerful queries like:
- "How many times has he seen Bruce Springsteen?"
- "What's his most-visited venue?"
- "Which artists has he seen the most?"

## Data Quality Issues Addressed

**Before cleaning:**
- 604 artist name variations (duplicates, typos, inconsistent capitalization)
- 263 venue variations (abbreviations, spelling differences)
- Opening acts mixed in with headliners
- Inconsistent date formats
- Missing data

**After cleaning:**
- Normalized artist and venue names
- Separated headliners from opening acts
- Standardized dates in ISO format
- Geographic data added to venues
- Relational database structure for powerful queries

## Project Structure

```
concert-website/
├── data/                    # Data files
│   ├── Original_List.xlsx   # Original Excel file
│   ├── raw_concerts.json    # Extracted raw data
│   ├── normalized_artists.json
│   ├── normalized_venues.json
│   └── cleaned_concerts.json
├── mappings/               # Name standardization mappings
│   ├── artist_mapping.csv  # Maps variations to canonical names
│   └── venue_mapping.csv   # Maps venues with location data
├── scripts/                # Data cleaning pipeline
│   ├── 1_extract_raw_data.py
│   ├── 2_normalize_artists.py
│   ├── 3_normalize_venues.py
│   ├── 4_validate_and_clean_dates.py
│   ├── 5_generate_database.py
│   └── run_all.py          # Run entire pipeline
├── database/               # Generated SQLite database
│   └── concerts.db
└── README.md
```

## Running the Data Cleaning Pipeline

### Prerequisites

- Python 3.7+
- Required packages: `pandas`, `openpyxl`

```bash
pip install pandas openpyxl
```

### Run All Steps

From the project root directory:

```bash
cd concert-website
python3 scripts/run_all.py
```

This will:
1. Extract data from Excel → `data/raw_concerts.json`
2. Normalize artist names → `data/normalized_artists.json`
3. Normalize venue names → `data/normalized_venues.json`
4. Validate and clean dates → `data/cleaned_concerts.json`
5. Generate SQLite database → `database/concerts.db`

### Run Individual Steps

You can also run steps individually:

```bash
python3 scripts/1_extract_raw_data.py
python3 scripts/2_normalize_artists.py
python3 scripts/3_normalize_venues.py
python3 scripts/4_validate_and_clean_dates.py
python3 scripts/5_generate_database.py
```

## Database Schema

### Tables

**artists**
- `id`: Primary key
- `canonical_name`: Standardized artist name

**artist_aliases**
- `artist_id`: Foreign key to artists
- `alias`: Variant spelling/name

**venues**
- `id`: Primary key
- `canonical_name`: Official venue name
- `short_name`: Common abbreviation (e.g., "MSG")
- `city`, `state`: Location
- `venue_type`: arena, theater, stadium, etc.

**concerts**
- `id`: Primary key
- `show_number`: Concert number in sequence
- `date`: ISO format date
- `date_unknown`: Boolean if date is uncertain
- `venue_id`: Foreign key to venues
- `opening_song`, `closing_song`: Set list bookends
- `attended`: Boolean (false for future concerts)

**concert_artists**
- `concert_id`, `artist_id`: Composite key
- `role`: 'headliner' or 'opener'
- `position`: Order for multiple artists

## Example Queries

Once the database is generated, you can query it:

```python
import sqlite3

conn = sqlite3.connect('database/concerts.db')
cursor = conn.cursor()

# How many times seen Bruce Springsteen?
cursor.execute('''
    SELECT COUNT(*)
    FROM concerts c
    JOIN concert_artists ca ON c.id = ca.concert_id
    JOIN artists a ON ca.artist_id = a.id
    WHERE a.canonical_name LIKE '%Bruce Springsteen%'
    AND ca.role = 'headliner'
''')
print(f"Bruce Springsteen concerts: {cursor.fetchone()[0]}")

# Most-visited venues
cursor.execute('''
    SELECT v.canonical_name, COUNT(*) as visit_count
    FROM concerts c
    JOIN venues v ON c.venue_id = v.id
    WHERE c.attended = 1
    GROUP BY v.id
    ORDER BY visit_count DESC
    LIMIT 10
''')
for venue, count in cursor.fetchall():
    print(f"{count:3d}x - {venue}")

conn.close()
```

## Customizing the Mappings

### Artist Mapping

Edit `mappings/artist_mapping.csv` to add or correct artist name mappings:

```csv
original_name,canonical_name,count,needs_review,notes
Bruce Springsteen & E Street Band,Bruce Springsteen & the E Street Band,16,NO,Standardized
```

### Venue Mapping

Edit `mappings/venue_mapping.csv` to add venue details:

```csv
original_name,canonical_name,short_name,city,state,venue_type,count,needs_review,notes
MSG,Madison Square Garden,MSG,New York,NY,arena,250,NO,Verified
```

After updating mappings, re-run the pipeline:

```bash
python3 scripts/run_all.py
```

## Next Steps

### Option 1: Simple Static Website

- Export database to JSON
- Build HTML/CSS/JavaScript interface
- Deploy to GitHub Pages

### Option 2: Flask Web App

- Python Flask backend
- SQLite database
- Search, filter, and statistics pages

### Option 3: Modern Web App

- React/Next.js frontend
- REST API backend
- Charts and visualizations
- Interactive timeline

## Statistics (Example)

After running the pipeline, you'll have access to insights like:

- **Total concerts attended**: 1,200+ (excluding future concerts)
- **Total unique artists**: 400+
- **Total unique venues**: 200+
- **Most-seen artist**: Billy Joel (65 times)
- **Most-visited venue**: Madison Square Garden (250 concerts)
- **Concert span**: 1994 - 2024

## Maintenance

To add new concerts:
1. Update `data/Original_List.xlsx`
2. Run `python3 scripts/run_all.py`
3. New artists/venues will be flagged for mapping review

## License

This is a personal project for organizing concert history.
