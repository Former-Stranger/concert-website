# Concert Website Python Scripts Documentation

## Overview
Total Scripts: 84 Python files in the `/scripts` directory

These scripts are organized into 5 main categories based on their purpose and usage frequency.

---

## CATEGORY 1: CORE/PRODUCTION SCRIPTS
### Actively used in production workflows

#### Data Pipeline & Export

1. **export_to_web.py**
   - Purpose: Export concert database from Firestore to JSON format for static website
   - Usage: `python3 scripts/export_to_web.py`
   - Frequency: Regular (after database updates)
   - Key Function: Exports all concert data to JSON files for website deployment

2. **add_concert.py** (Executable)
   - Purpose: Add a new concert directly to Firestore via interactive prompt
   - Usage: `python3 scripts/add_concert.py`
   - Frequency: As needed (when adding new concerts)
   - Prompts for: Date, Artist, Support act, Festival name, Venue, City, State

3. **fetch_setlists_enhanced.py**
   - Purpose: Enhanced setlist fetcher that handles co-headliners automatically
   - Usage: `python3 scripts/fetch_setlists_enhanced.py`
   - Frequency: Regular (fetches setlist data from setlist.fm)
   - Features: Handles single artists and co-headliners with separate document IDs

4. **analyze_setlists.py**
   - Purpose: Analyze setlist data to answer interesting questions about patterns
   - Usage: `python3 scripts/analyze_setlists.py [artist_name]`
   - Frequency: On-demand (analysis tool)
   - Queries: Most common songs, opening/closing songs, encore patterns, artist statistics

#### Admin & Maintenance

5. **apply_artist_corrections.py** (Executable)
   - Purpose: Apply artist name corrections from review CSV back to Firestore
   - Usage: `python3 scripts/apply_artist_corrections.py website/data/headliners_to_review.csv`
   - Frequency: As needed (batch corrections)
   - Updates: Artist names in concert documents based on CSV input

6. **check_submission.py** (Executable)
   - Purpose: Check status of a concert's setlist submission
   - Usage: Hardcoded with concert_id=1275 (modifiable)
   - Frequency: On-demand
   - Shows: Submission status, submitter, processing status, errors

7. **setup_admins.py**
   - Purpose: Setup admin users in Firestore
   - Usage: `python3 scripts/setup_admins.py`
   - Frequency: One-time or as needed for admin management
   - Manages: User admin access control

8. **cleanup_old_admins.py**
   - Purpose: Clean up old admin documents (email-based IDs) from previous setup
   - Usage: `python3 scripts/cleanup_old_admins.py`
   - Frequency: One-time maintenance
   - Removes: Old email-based admin IDs, keeps UID-based documents

#### Utilities & Tools

9. **setlistfm_client.py**
   - Purpose: Setlist.fm API Client - Core library for API interactions
   - Usage: Imported by other scripts (not run directly)
   - Frequency: Used by many scripts
   - Features: Rate limiting (2 req/sec), search setlists, fetch concert data

10. **submit_setlist.py**
    - Purpose: Script to submit a setlist from setlist.fm for admin approval
    - Usage: `python3 scripts/submit_setlist.py`
    - Frequency: User-facing tool for submissions
    - Saves: Submissions to Firestore pending collection

---

## CATEGORY 2: DATA PIPELINE SCRIPTS
### Initial data setup/one-time import scripts

1. **1_extract_raw_data.py**
   - Purpose: Extract raw data from Excel and perform basic validation
   - Step: 1 of 5 in initial pipeline
   - Input: `data/Original_List.xlsx`
   - Output: `data/raw_concerts.json`
   - Usage: `python3 scripts/1_extract_raw_data.py`

2. **2_normalize_artists.py**
   - Purpose: Normalize artist names using the mapping file
   - Step: 2 of 5 in initial pipeline
   - Input: `data/raw_concerts.json`, `mappings/artist_mapping.csv`
   - Output: `data/normalized_artists.json`
   - Features: Handles festivals, multi-artist shows, openers (w/ notation)

3. **3_normalize_venues.py**
   - Purpose: Normalize venue names using the mapping file
   - Step: 3 of 5 in initial pipeline
   - Input: `data/normalized_artists.json`, `mappings/venue_mapping.csv`
   - Output: `data/normalized_venues.json`
   - Features: Maps venues to canonical names, adds city/state/type info

4. **4_validate_and_clean_dates.py**
   - Purpose: Validate and clean dates
   - Step: 4 of 5 in initial pipeline
   - Input: `data/normalized_venues.json`
   - Output: `data/cleaned_concerts.json`
   - Validates: Date formats, handles TBD dates, marks future concerts

5. **5_generate_database.py**
   - Purpose: Generate SQLite database from cleaned data
   - Step: 5 of 5 in initial pipeline
   - Input: `data/cleaned_concerts.json`
   - Output: `database/concerts.db`
   - Creates: Artists, venues, concerts tables with proper relationships

6. **run_all.py**
   - Purpose: Master script to run all data cleaning and database generation steps
   - Usage: `python3 scripts/run_all.py`
   - Executes: Steps 1-5 automatically in sequence
   - Error Handling: Stops if any step fails

7. **migrate_to_firestore.py**
   - Purpose: One-time migration script to copy all data from SQLite to Firestore
   - Usage: `python3 migrate_to_firestore.py [--dry-run]`
   - Transfers: Artists, venues, concerts, setlists from SQLite to Firestore

8. **add_setlists_schema.py**
   - Purpose: Add setlist tables to SQLite database
   - Usage: `python3 scripts/add_setlists_schema.py`
   - Creates: Tables for storing setlist metadata and individual songs

9. **parse_festivals.py**
   - Purpose: Parse festival and multi-artist entries into individual searchable artists
   - Used by: 2_normalize_artists.py
   - Handles: Festival detection, multi-artist shows

10. **parse_venue_notes.py**
    - Purpose: Parse venue notes and extract city, state, and venue_type information
    - Utility: Data extraction helper

---

## CATEGORY 3: MAINTENANCE/FIX SCRIPTS
### One-time fixes for specific data issues

#### Specific Concert Fixes

1. **fix_concert_1003.py**
   - Purpose: Fix Concert 1003 - John Henry's Friends Benefit
   - Status: One-time fix (completed)
   - Changes: Corrects festival/artist data for this specific concert

2. **fix_concert_1220.py**
   - Purpose: Fix concert 1220 to have Dave Matthews Band as artist and SOULSHINE as festival
   - Status: One-time fix (completed)

3. **fix_concert_1274.py**
   - Purpose: Fix concert 1274 (Mumford & Sons with Lucius opener)
   - Status: One-time fix (completed)
   - Template: Used as basis for fix_concert_512.py

4. **fix_concert_512.py**
   - Purpose: Fix concert 512 to have Mumford & Sons as headliner and Dawes as opener
   - Status: One-time fix (completed)

#### Artist Data Fixes

5. **fix_dead_and_company.py**
   - Purpose: Fix Dead and Company artist name
   - Status: One-time fix (completed)

6. **fix_dead_and_company_v2.py**
   - Purpose: Fix Dead and Company multi-artist entries
   - Status: One-time fix (completed)
   - Replaces: v1 with improved logic

7. **fix_artist_656.py**
   - Purpose: Fix artist 656 - another Dead and Company instance
   - Status: One-time fix (completed)

8. **fix_mumford_artist.py**
   - Purpose: Fix Mumford & Sons artist name in Firestore
   - Status: One-time fix (completed)

9. **fix_artist_names.py** (Executable)
   - Purpose: Fix artist name issues in concerts collection
   - Usage: `python3 scripts/fix_artist_names.py`
   - Status: Maintenance script

10. **find_artist_issues.py** (Executable)
    - Purpose: Find artist name issues in concerts collection
    - Usage: `python3 scripts/find_artist_issues.py`
    - Status: Diagnostic script

#### Phil Lesh & Friends Fixes

11. **merge_phil_lesh_artists.py**
    - Purpose: Merge Phil Lesh artist variations into one canonical artist
    - Status: One-time fix (completed)

12. **fix_phil_lesh_friends.py**
    - Purpose: Remove duplicate "Friends" artists from Phil Lesh & Friends concerts
    - Status: One-time fix (completed)

13. **fix_phil_lesh_guests.py**
    - Purpose: Remove guest artists from Phil Lesh & Friends concerts
    - Status: One-time fix (completed)

#### Co-Headliner & Setlist Fixes

14. **fix_co_headliners.py** (Executable)
    - Purpose: Fix concerts with co-headliners stored as single artist with "/" separator
    - Usage: `python3 scripts/fix_co_headliners.py`
    - Status: Maintenance script

15. **create_coheadliner_setlists_847.py**
    - Purpose: Create co-headliner setlists for Concert 847 (Rod Stewart / Cyndi Lauper)
    - Status: One-time fix (completed)

16. **create_coheadliner_setlists_847_auto.py**
    - Purpose: Automated version of co-headliner setlist creation
    - Status: One-time fix (completed)

#### Setlist Flag/Data Fixes

17. **fix_has_setlist_flags.py**
    - Purpose: Fix has_setlist flags in concerts collection to match actual setlist existence
    - Usage: `python3 scripts/fix_has_setlist_flags.py`
    - Status: Maintenance script

18. **fix_setlist_document_ids.py**
    - Purpose: Fix setlist document IDs to use concert_id instead of random IDs
    - Status: One-time fix (completed)

19. **fix_false_positive_setlists.py**
    - Purpose: Fix only false positive setlist flags - concerts marked as having setlists but don't
    - Status: One-time fix (completed)

20. **fix_festival_data.py**
    - Purpose: Fix festival data structure issues
    - Status: Maintenance script

#### Data Synchronization Fixes

21. **sync_has_setlist_with_actual_data.py**
    - Purpose: Sync has_setlist flags in Firestore to match actual concert_details file existence
    - Status: Maintenance script

22. **sync_firestore_submissions.py**
    - Purpose: Script to sync pending setlist submissions from Firestore to SQLite database
    - Status: Maintenance script

#### Venue Consolidation

23. **consolidate_duplicates.py**
    - Purpose: Consolidate duplicate canonical venue names
    - Example: "Daryls House" + "Daryl's House" → "Daryl's House"
    - Status: One-time fix (completed)

24. **merge_venue_additions.py**
    - Purpose: Merge venue additions from template into main venue_mapping.csv
    - Status: Maintenance script

25. **merge_all_remaining_venues.py**
    - Purpose: Merge all remaining venues from the template into main venue_mapping.csv
    - Status: Maintenance script

#### Normalization Utilities

26. **normalize_artist_names.py**
    - Purpose: Normalize artist names in the concerts collection
    - Status: Utility script

---

## CATEGORY 4: TESTING/DEBUG SCRIPTS
### Diagnostic and testing tools

1. **debug_missing_setlists.py**
   - Purpose: Debug why specific concerts aren't being found on setlist.fm
   - Usage: `python3 scripts/debug_missing_setlists.py [show_number]`
   - Default: Tests show #1187 if no argument provided
   - Tests: 4 progressively lenient search strategies

2. **detect_missing_openers.py** (Executable)
   - Purpose: Automated Opener Detection Script using setlist.fm API
   - Usage: `python3 scripts/detect_missing_openers.py [options]`
   - Options: --concert-id, --limit, --output, --api-key
   - Analyzes: Concerts with single headliners to detect potential openers
   - Confidence Levels: HIGH, MEDIUM, LOW based on heuristics

3. **discover_opener_logic.py**
   - Purpose: Test script to discover opener detection logic
   - Status: Research/prototype script
   - Tests: Smart opener detection strategy (artist+date → exact venue → all performers)

4. **test_kip_moore.py**
   - Purpose: Test the exact example from the documentation
   - Status: Example/verification script

5. **test_single_fetch.py**
   - Purpose: Test fetching setlists for multiple concerts to see success rate
   - Status: Performance/reliability testing

6. **fetch_single_concert.py** (Executable)
   - Purpose: Fetch setlist for a single concert by ID
   - Usage: `python3 scripts/fetch_single_concert.py`
   - Status: Diagnostic/utility script

7. **inspect_setlist_api.py**
   - Purpose: Inspect raw setlist.fm API response for a specific concert
   - Status: Debugging/exploration tool

8. **inspect_festival_setlist.py**
   - Purpose: Inspect setlist.fm API response for a festival performance to identify festival fields
   - Status: Research script

9. **show_full_setlist_data.py**
   - Purpose: Display all available setlist.fm data for concert 847 in readable format
   - Status: Inspection tool

#### Search/Browse Tools

10. **search_artists.py**
    - Purpose: Search for artist records in Firestore
    - Status: Utility tool

11. **search_bonnaroo.py**
    - Purpose: Search for Bonnaroo setlists and inspect the data structure
    - Status: Research/verification tool

12. **search_great_south_bay.py**
    - Purpose: Search for Great South Bay Music Festival 2008 setlists
    - Status: Research tool

13. **fetch_jackson_browne_festival.py**
    - Purpose: Fetch Jackson Browne at Great South Bay Music Festival - April 6, 2008
    - Status: One-time fetch script

#### Review & Analysis Tools

14. **review_data.py**
    - Purpose: Interactive data review tool
    - Status: Manual review utility

15. **review_setlist_submissions.py**
    - Purpose: Script to review and approve/reject pending setlist submissions
    - Status: Admin workflow tool

16. **review_setlist_results.py**
    - Purpose: Review results of setlist fetching - show what was found and what wasn't
    - Status: Quality assurance tool

17. **inspect_submission.py**
    - Purpose: Inspect a submission in detail
    - Status: Diagnostic tool

#### Admin/Permission Tools

18. **get_user_uid.py**
    - Purpose: Get the UID of a user by email
    - Status: Utility script

---

## CATEGORY 5: DEPRECATED/OBSOLETE SCRIPTS
### One-time use, experimental, or superseded by newer scripts

1. **fetch_setlists.py**
   - Purpose: Fetch setlist data from setlist.fm for all concerts in the database
   - Status: DEPRECATED - Replaced by fetch_setlists_enhanced.py
   - Reason: Enhanced version has better co-headliner handling

2. **fetch_missing_setlists.py**
   - Purpose: Fetch missing setlists from setlist.fm for concerts with empty setlist documents
   - Status: DEPRECATED - Replaced by fetch_missing_setlists_with_rotation.py

3. **fetch_missing_setlists_with_rotation.py** (Executable)
   - Purpose: Fetch missing setlists from setlist.fm with automatic API key rotation
   - Status: ACTIVE but specialized (uses API key rotation for higher limits)
   - Features: Automatic retry with rotated API keys

4. **wipe_all_setlist_data.py**
   - Purpose: Complete wipe of all setlist data from Firestore database
   - Status: DANGEROUS - Destructive operation (use with caution)
   - Requires: Confirmation before executing

5. **wipe_all_setlists.py**
   - Purpose: Complete Setlist Database Wipe Script
   - Status: DANGEROUS - Duplicate/deprecated version of wipe_all_setlist_data.py

6. **delete_all_setlists.py**
   - Purpose: Delete all setlist documents from Firestore
   - Status: ACTIVE but specialized (used for complete resets)
   - Features: Dry-run mode, detailed output, --dry-run flag

7. **process_approved_setlists.py**
   - Purpose: Manually process approved setlist submissions that haven't been processed yet
   - Status: MAINTENANCE - Used to handle edge cases

8. **reset_has_setlist_flags.py**
   - Purpose: Reset has_setlist flags to false for all concerts
   - Status: MAINTENANCE - Administrative tool

9. **revert_has_setlist_flags.py**
   - Purpose: Revert has_setlist flags back to True for concerts that have concert_details JSON files
   - Status: MAINTENANCE - Cleanup/recovery script

10. **restore_setlist_flags_from_backup.py**
    - Purpose: Restore has_setlist flags in Firestore from the backup concerts.json file
    - Status: MAINTENANCE - Recovery script

11. **restore_from_oct20_backup.py**
    - Purpose: Restore data from October 20th backup database to fix data corruption
    - Status: ONE-TIME (completed) - Emergency recovery

12. **copy_setlists_from_backup.py**
    - Purpose: Copy setlists from the restored-oct20 database to the default database
    - Status: ONE-TIME (completed) - Data recovery operation

13. **remove_opening_closing_fields.py**
    - Purpose: Remove opening_song and closing_song fields from concert documents
    - Status: ONE-TIME (completed) - Data cleanup

14. **force_reprocess.py**
    - Purpose: Force reprocessing by toggling status
    - Status: UTILITY - Debugging/testing tool

15. **trigger_processing.py**
    - Purpose: Trigger processing of an approved but unprocessed submission
    - Status: UTILITY - Workflow tool

16. **check_firestore.py**
    - Purpose: Quick script to check Firestore for pending submissions
    - Status: DIAGNOSTIC - Info gathering tool

17. **process_concert_updates.py**
    - Purpose: Process concert updates from reviewed CSV file
    - Usage: `python3 scripts/process_concert_updates.py concerts_for_review.csv`
    - Status: UTILITY - Batch update workflow

18. **export_concerts_for_review.py**
    - Purpose: Export all concerts to CSV for manual review and classification
    - Status: UTILITY - Data export for human review

19. **export_to_csv.py**
    - Purpose: Export cleaned data to CSV for easy review in Excel
    - Status: UTILITY - Data export format

20. **example_queries.py**
    - Purpose: Example queries to demonstrate the database capabilities
    - Status: DOCUMENTATION - Example/reference code

---

## USAGE PATTERNS & WORKFLOWS

### Initial Setup (One-time)
1. Run: `python3 scripts/run_all.py` (steps 1-5)
2. Add setlist schema: `python3 scripts/add_setlists_schema.py`
3. Migrate to Firestore: `python3 scripts/migrate_to_firestore.py`

### Regular Operations (Recurring)
1. Add new concert: `python3 scripts/add_concert.py`
2. Fetch setlists: `python3 scripts/fetch_setlists_enhanced.py`
3. Export to web: `python3 scripts/export_to_web.py`
4. Deploy: `firebase deploy --only hosting`

### Data Maintenance (As Needed)
1. Export for review: `python3 scripts/export_concerts_for_review.py`
2. Apply corrections: `python3 scripts/apply_artist_corrections.py <csv_file>`
3. Fix specific issues: Various `fix_*.py` scripts
4. Sync flags: `python3 scripts/sync_has_setlist_with_actual_data.py`

### Troubleshooting
1. Debug setlist search: `python3 scripts/debug_missing_setlists.py [show_number]`
2. Detect missing openers: `python3 scripts/detect_missing_openers.py`
3. Inspect submission: `python3 scripts/inspect_submission.py`
4. Check Firestore: `python3 scripts/check_firestore.py`

---

## KEY DEPENDENCIES

### External APIs
- **setlist.fm API**: Rate limited to 2 req/sec (0.25 req/sec used for safety)
  - Used by: fetch_setlists_enhanced.py, detect_missing_openers.py, etc.

### Firebase Services
- **Firestore**: NoSQL database for all concert/setlist data
- **Firebase Admin SDK**: Used by migration and data manipulation scripts

### Local Data Files
- `data/Original_List.xlsx`: Source Excel file (step 1)
- `mappings/artist_mapping.csv`: Artist name normalization reference
- `mappings/venue_mapping.csv`: Venue name normalization reference
- `database/concerts.db`: SQLite database (generated)

### Environment Variables
- `GOOGLE_CLOUD_PROJECT`: GCP project ID (default: 'earplugs-and-memories')
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Firebase service account key
- `SETLISTFM_API_KEY`: Setlist.fm API key

---

## SUMMARY BY FREQUENCY

### Daily/Regular Use
- export_to_web.py
- fetch_setlists_enhanced.py
- add_concert.py

### Weekly/Monthly Use
- apply_artist_corrections.py
- analyze_setlists.py
- review_setlist_submissions.py
- export_concerts_for_review.py

### As-Needed/Maintenance
- All fix_*.py scripts
- All sync_*.py scripts
- Various diagnostic scripts

### One-Time/Setup Only
- run_all.py (steps 1-5)
- migrate_to_firestore.py
- add_setlists_schema.py
- consolidate_duplicates.py
- restore_from_oct20_backup.py

