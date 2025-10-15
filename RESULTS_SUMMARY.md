# Data Cleaning Results Summary

## Pipeline Successfully Completed! ✓

All 5 steps of the data cleaning pipeline have been executed successfully.

## Results Overview

### Database Statistics

- **Total unique artists**: 590 (normalized from 604+ variations)
- **Total unique venues**: 241 (normalized from 263+ variations)
- **Total concerts attended**: 1,288
- **Future concerts planned**: 4
- **Concert span**: 1994 - 2025 (31 years)

### Top 15 Most-Seen Artists (as headliner)

1. **Bruce Springsteen & the E Street Band** - 72 concerts
2. **Billy Joel** - 65 concerts
3. **Bruce Springsteen** - 29 concerts (solo/acoustic)
4. **Elton John** - 22 concerts
5. **Jimmy Buffett** - 20 concerts
6. **Dave Matthews Band** - 20 concerts
7. **Dead & Company** - 19 concerts
8. **U2** - 18 concerts
9. **Allman Brothers Band** - 18 concerts
10. **Keith Urban** - 17 concerts
11. **Will Hoge** - 14 concerts
12. **KISS** - 14 concerts
13. **John Fogerty** - 14 concerts
14. **Bon Jovi** - 14 concerts
15. **Pearl Jam** - 13 concerts

**Note**: Bruce Springsteen total = 101 concerts (72 with E Street Band + 29 solo)

### Top 15 Most-Visited Venues

1. **Madison Square Garden** (New York, NY) - 251 concerts
2. **Jones Beach Theater** (Wantagh, NY) - 100 concerts
3. **Capitol Theatre** (Port Chester, NY) - 76 concerts
4. **Beacon Theatre** (New York, NY) - 71 concerts
5. **Radio City Music Hall** (New York, NY) - 35 concerts
6. **Nassau Coliseum** (Uniondale, NY) - 35 concerts
7. **Giants Stadium** (East Rutherford, NJ) - 34 concerts
8. **Barclays Center** (Brooklyn, NY) - 28 concerts
9. **Izod Center** (East Rutherford, NJ) - 27 concerts
10. **MetLife Stadium** (East Rutherford, NJ) - 26 concerts
11. **NYCB Theatre at Westbury** (Westbury, NY) - 24 concerts
12. **Ridgefield Playhouse** (Ridgefield, CT) - 23 concerts
13. **Citi Field** (Queens, NY) - 23 concerts
14. **Tarrytown Music Hall** (Tarrytown, NY) - 22 concerts
15. **PNC Bank Arts Center** (Holmdel, NJ) - 20 concerts

### Concert Activity by Year (Recent)

| Year | Concerts |
|------|----------|
| 2024 | 91 |
| 2018 | 85 |
| 2019 | 76 |
| 2016 | 73 |
| 2022 | 71 |
| 2017 | 69 |
| 2023 | 64 |
| 2025 | 55 (planned) |
| 2021 | 32 |
| 2020 | 5 (COVID-19) |

**Busiest year**: 2024 with 91 concerts!

## Data Quality Improvements

### Artists
- **Before**: 604 artist name variations
- **After**: 590 unique canonical artists
- **Mapped**: 80 most common variations automatically corrected
- **Unmapped**: ~520 less-common artists (appear 1-6 times each)

### Venues
- **Before**: 263 venue name variations
- **After**: 241 unique venues with location data
- **Mapped**: 62 major venues with full details (city, state, type)
- **Unmapped**: ~200 smaller venues (need manual addition)

### Dates
- **Clean dates**: 1,284 (99.4%)
- **Date issues**: 8 (0.6%)
  - 2 marked as "TBD"
  - 1 ambiguous date ("3/18,20 or 24")
  - 1 malformed date ("7/_/07")
  - 4 future concerts without dates

### Opening Acts
- **Concerts with opening acts**: 67
- All successfully parsed and linked as separate artist relationships

## Files Generated

```
concert-website/
├── data/
│   ├── Original_List.xlsx           # Source data
│   ├── raw_concerts.json            # Step 1: Extracted
│   ├── normalized_artists.json      # Step 2: Artists normalized
│   ├── normalized_venues.json       # Step 3: Venues normalized
│   └── cleaned_concerts.json        # Step 4: Dates validated
├── mappings/
│   ├── artist_mapping.csv           # 80 artist name mappings
│   └── venue_mapping.csv            # 62 venue mappings with locations
├── database/
│   └── concerts.db                  # Step 5: SQLite database
└── README.md                        # Full documentation
```

## Database Schema

The database uses a normalized relational structure:

- **artists** - Canonical artist names
- **artist_aliases** - Maps variations to canonical names
- **venues** - Venue details (name, location, type)
- **concerts** - Concert records (date, venue, songs, attendance)
- **concert_artists** - Many-to-many relationships (headliner/opener)

## Next Steps

### Option 1: Expand Mappings (Recommended)
To achieve 100% mapping coverage:

1. **Artists**: Add remaining ~520 artists to `artist_mapping.csv`
   - Focus on artists seen 2+ times first
   - Many are likely already correct and just need confirmation

2. **Venues**: Add remaining ~200 venues to `venue_mapping.csv`
   - Research official names and locations
   - Add venue types (arena, theater, stadium, club)

3. **Re-run pipeline**: `python3 scripts/run_all.py`

### Option 2: Build Website

Choose your approach:

**Simple Static Site**:
- Export database to JSON
- HTML/CSS/JavaScript frontend
- Host on GitHub Pages (free)
- Fast and simple

**Flask Web App**:
- Python Flask backend
- SQLite database
- Search, filter, statistics pages
- Can run locally or deploy

**Modern React App**:
- Next.js/React frontend
- REST API backend
- Interactive charts (Chart.js, D3.js)
- Timeline visualization
- Map of venues

### Option 3: Generate Statistics

Use the database to create:
- PDF report with charts
- Year-by-year analysis
- Artist discovery timeline
- Venue heat map
- Concert frequency patterns

## Example Queries

The database is ready to answer questions like:

```sql
-- How many times seen Bruce Springsteen (any version)?
SELECT a.canonical_name, COUNT(*) as count
FROM concerts c
JOIN concert_artists ca ON c.id = ca.concert_id
JOIN artists a ON ca.artist_id = a.id
WHERE a.canonical_name LIKE '%Bruce Springsteen%'
AND ca.role = 'headliner'
GROUP BY a.canonical_name;

-- What's the longest gap between concerts?
SELECT
    date as concert_date,
    LAG(date) OVER (ORDER BY date) as prev_date,
    JULIANDAY(date) - JULIANDAY(LAG(date) OVER (ORDER BY date)) as days_between
FROM concerts
WHERE attended = 1 AND date IS NOT NULL
ORDER BY days_between DESC
LIMIT 5;

-- Which artists has he seen at MSG?
SELECT a.canonical_name, COUNT(*) as times
FROM concerts c
JOIN venues v ON c.venue_id = v.id
JOIN concert_artists ca ON c.id = ca.concert_id
JOIN artists a ON ca.artist_id = a.id
WHERE v.short_name = 'MSG' AND ca.role = 'headliner'
GROUP BY a.id
ORDER BY times DESC;
```

## Interesting Facts

- **MSG is king**: 251 concerts at Madison Square Garden (19.5% of all concerts!)
- **Century Club**: Bruce Springsteen seen 101 times total
- **Busiest recent year**: 2024 with 91 concerts
- **COVID impact**: Only 5 concerts in 2020 (vs 76 in 2019)
- **Concert frequency**: Average of ~41 concerts per year (31 years)
- **NYC dominance**: Top 6 venues are all in the NY/NJ/CT area
- **Opening acts**: 67 concerts included notable opening acts

## Contact/Questions

For questions about using the database or building the website, refer to:
- `README.md` - Full documentation
- `DATA_CLEANING_PLAN.md` - Detailed cleaning strategy
- Scripts in `scripts/` directory - Well-commented Python code
