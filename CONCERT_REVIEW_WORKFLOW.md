# Concert Review & Classification Workflow

## Overview

This workflow allows you to review all concerts, classify them by event type, and update the database in batch.

## Files Created

1. **concerts_for_review.csv** - Main review file (238KB, 1,275 concerts)
2. **scripts/export_concerts_for_review.py** - Generates the review CSV
3. **scripts/process_concert_updates.py** - Applies your changes to Firestore
4. **docs/EVENT_TYPE_CRITERIA.md** - Complete classification criteria guide

## CSV Structure

### Read-Only Columns (Current Data)

| Column | Description |
|--------|-------------|
| `concert_id` | Firestore document ID |
| `show_number` | Sequential concert number |
| `date` | Concert date (YYYY-MM-DD) |
| `venue_name` | Venue where concert took place |
| `city` | City |
| `state` | State code |
| `current_festival_name` | Current value in database |
| `has_setlist` | Whether setlist data exists |
| `attended` | Whether you attended |
| `artist_count` | Total number of artists |
| `headliner_count` | Number of headliners |
| `artists_list` | Comma-separated artist names |
| `artists_with_roles` | Artists with their roles shown |
| `suggested_event_type` | AI-suggested classification |
| `suggestion_confidence` | high, medium, low |
| `suggestion_reason` | Why this type was suggested |

### Editable Columns (Your Updates)

| Column | Description | Values |
|--------|-------------|--------|
| `NEW_event_type` | Event classification | `solo`, `tour`, `festival`, `multi_artist_show`, `other` |
| `NEW_event_name` | Name of event/festival | Free text (e.g., "Bonnaroo 2024", "Sandy Relief") |
| `NEW_tour_name` | Tour name if applicable | Free text (e.g., "2018 Summer Tour") |
| `NEW_notes` | Classification notes | Free text |
| `ACTION` | What to do with this row | `UPDATE`, `KEEP`, `REVIEW`, `DELETE` |

## Event Type Definitions

### solo
- Single headliner
- Regular concert (not part of tour/festival)
- May have opening acts
- **Example:** Billy Joel at Madison Square Garden

### tour
- Part of named tour series
- One or more headliners touring together
- Has official tour name
- **Example:** Rod Stewart & Cyndi Lauper "2018 North American Summer Tour"

### festival
- Multi-stage, multi-artist event
- Typically 10+ artists total
- Festival venue or outdoor space
- **Example:** Bonnaroo, Newport Folk Festival

### multi_artist_show
- 2+ headliners, NOT a tour
- Single venue/stage
- Often benefit or tribute shows
- **Example:** 12-12-12 Sandy Relief Concert

### other
- Doesn't fit above categories
- Residency shows, special formats
- **Example:** Billy Joel monthly MSG residency

## Step-by-Step Workflow

### Step 1: Generate CSV (Already Done!)
```bash
python3 scripts/export_concerts_for_review.py
```

Creates: `concerts_for_review.csv` ✅

### Step 2: Review in Excel/Google Sheets

1. **Open the CSV** in Excel, Google Sheets, or Numbers
2. **Sort/Filter** to focus on specific concerts:
   - Filter by `suggested_event_type = NEEDS_REVIEW` (7 concerts)
   - Filter by `suggested_event_type = multi_artist_show` (245 concerts)
   - Filter by `current_festival_name` to review specific events
3. **Review each concert** and fill in the editable columns
4. **Set ACTION column**:
   - `UPDATE` - Apply changes from NEW_* columns
   - `KEEP` - Leave as-is (no changes)
   - `REVIEW` - Flag for later review (no changes)
   - `DELETE` - Delete this concert (rare)

### Step 3: Test with Dry Run

Before applying changes, test what will happen:

```bash
python3 scripts/process_concert_updates.py concerts_for_review.csv --dry-run
```

This shows what would be updated WITHOUT making changes.

### Step 4: Apply Updates

When ready, apply changes to Firestore:

```bash
python3 scripts/process_concert_updates.py concerts_for_review.csv
```

This updates Firestore based on rows with `ACTION=UPDATE`.

### Step 5: Export & Deploy

After updating Firestore, export to JSON and deploy:

```bash
# Export updated data
python3 scripts/export_to_web.py

# Deploy to website
firebase deploy --only hosting
```

## Quick Tips

### Focus on Priority Items

**High Priority (7 concerts):**
- Concerts with `suggested_event_type = NEEDS_REVIEW`
- These have multiple artists but no classification

**Medium Priority (245 concerts):**
- Concerts with `current_festival_name = Multi-Artist Show`
- Replace generic label with specific event names

**Low Priority (1,010 concerts):**
- Concerts with `suggested_event_type = solo`
- Most are already correctly classified

### Common Patterns to Look For

**Pattern 1: Co-Headliner Tours**
- Example: Rod Stewart & Cyndi Lauper (Concert 847)
- Set: `NEW_event_type = tour`
- Set: `NEW_tour_name = 2018 North American Summer Tour`
- Set: `ACTION = UPDATE`

**Pattern 2: Benefit Concerts**
- Example: 12-12-12 Sandy Relief
- Set: `NEW_event_type = multi_artist_show`
- Set: `NEW_event_name = 12-12-12 Concert For Sandy Relief`
- Set: `ACTION = UPDATE`

**Pattern 3: Festival Performances**
- Example: Great South Bay Music Festival
- Set: `NEW_event_type = festival`
- Set: `NEW_event_name = Great South Bay Music Festival 2008`
- Set: `ACTION = UPDATE`

### Example Edits

#### Concert 847 (Rod Stewart & Cyndi Lauper)
```
concert_id: 847
suggested_event_type: NEEDS_REVIEW
NEW_event_type: tour
NEW_tour_name: 2018 North American Summer Tour
ACTION: UPDATE
```

#### Concert 1215 (Stand Up for Heroes)
```
concert_id: 1215
suggested_event_type: NEEDS_REVIEW
NEW_event_type: multi_artist_show
NEW_event_name: Stand Up for Heroes 2024
ACTION: UPDATE
```

#### Concert 334 (Jackson Browne at Festival)
```
concert_id: 334
venue_name: Great South Bay Music Festival
NEW_event_type: festival
NEW_event_name: Great South Bay Music Festival 2008
ACTION: UPDATE
```

## Current Statistics

- **Total concerts:** 1,275
- **Suggested solo:** 1,010 (79%)
- **Suggested multi_artist_show:** 245 (19%)
- **Suggested festival:** 13 (1%)
- **Needs manual review:** 7 (<1%)

## Notes & Limitations

### Current Limitations

1. **tour_name field doesn't exist yet** in Firestore schema
   - Script will note tour names but not store them
   - Schema migration needed to add `tour_name` field
   - For now, tour info goes in notes

2. **event_type field doesn't exist yet** in Firestore schema
   - Script tracks this for future use
   - Currently only updates `festival_name` field
   - Schema migration planned

3. **Role changes not supported**
   - Can't change artist roles (headliner → festival_performer) via CSV
   - Would need separate script for role updates

### Best Practices

1. **Start small** - Update 10-20 concerts first, test, then continue
2. **Use dry-run** - Always test before applying changes
3. **Be specific** - Use actual event names, not generic labels
4. **Document unclear cases** - Use NEW_notes for ambiguous concerts
5. **Keep backups** - Original data preserved in Firestore

### Future Enhancements

Once schema is updated with `event_type` and `tour_name` fields:
- Processing script will update all fields
- Website can display event type badges/icons
- Can filter/search by event type
- Better analytics and statistics

## Troubleshooting

### CSV won't open properly
- Ensure UTF-8 encoding
- Try opening in Google Sheets (handles UTF-8 better)

### Process script errors
- Check Firestore credentials: `gcloud auth application-default login`
- Verify concert IDs exist in database
- Check for special characters in NEW_* columns

### Changes not appearing on website
- Run export script: `python3 scripts/export_to_web.py`
- Deploy to hosting: `firebase deploy --only hosting`
- Clear browser cache

## Contact

Questions about classification? Check:
- `docs/EVENT_TYPE_CRITERIA.md` - Complete classification guide
- `docs/FESTIVAL_TRACKING.md` - Festival tracking details
