# Festival & Artist Name Review Guide

## Overview

The `headliners_to_review.csv` file contains 85 artist names that need review because they contain special characters. Many of these are **festivals** where the festival name was embedded in the artist name.

## File Location
`website/data/headliners_to_review.csv`

## Columns Explained

| Column | Purpose | Example |
|--------|---------|---------|
| `artist_name` | Current (incorrect) name in database | `Sea Hear Now (Stevie Nicks)` |
| `artist_name_corrected` | **Fill this in** with clean artist name | `Stevie Nicks` |
| `festival_name` | **Fill this in** if it's a festival | `Sea Hear Now` |
| `current_festival_name` | What's currently in database | (empty) |
| `notes` | Pre-filled guidance | `FESTIVAL` |

## How to Review

### 1. Festivals (Set both artist AND festival)

**Example: Sea Hear Now Festival**
```
Current:  Sea Hear Now (Stevie Nicks)
Correct:  artist_name_corrected = Stevie Nicks
          festival_name = Sea Hear Now
```

**Known Festivals:**
- Sea Hear Now (2 concerts)
- Friends (3 concerts - benefit concerts)
- Stand Up for Heroes (4 concerts)

### 2. Special Events (Artist name only, no festival)

**Example: Billy Joel Milestone Shows**
```
Current:  Billy Joel (100th)
Correct:  artist_name_corrected = Billy Joel
          festival_name = (leave empty)
Notes:    This is his 100th MSG show, not a festival
```

**Example: Steve Earle Play**
```
Current:  Steve Earle (Coal Country Play)
Correct:  artist_name_corrected = Steve Earle
          festival_name = (leave empty)
Notes:    This is a theatrical performance
```

### 3. Guest Artists (Keep main artist, note guest)

**Example: Artist with Guest**
```
Current:  Avett Brothers (w./ Clem Snide)
Correct:  artist_name_corrected = Avett Brothers
          festival_name = (leave empty)
Notes:    Clem Snide was opening act or guest
```

### 4. Band Names with Numbers (Keep as-is)

**Example: U2**
```
Current:  U2
Correct:  artist_name_corrected = U2
          festival_name = (leave empty)
Notes:    Number is part of band name
```

### 5. Multi-Artist Shows (Needs splitting)

**Example: Multiple Headliners**
```
Current:  Kenny Chesney / Dan + Shay / Old Dominion
Options:
  A) Main headliner: Kenny Chesney, add others as separate artists
  B) Festival show: Set festival_name and split artists
Decision: Depends on billing - if co-headliners, might be a festival
```

## Decision Tree

```
Does the name have parentheses?
├─ Yes: Is the text in parentheses an artist name?
│   ├─ Yes → It's a FESTIVAL
│   │   Example: Sea Hear Now (Stevie Nicks)
│   │   Action: Extract artist, set festival_name
│   │
│   └─ No → It's a NOTE or EVENT DETAIL
│       Example: Billy Joel (100th)
│       Action: Remove parentheses, keep artist name
│
└─ No: Does it have + or / separators?
    ├─ Yes → Multiple artists or collaboration
    │   Example: Queen + Adam Lambert
    │   Action: Decide if it's a festival or dual billing
    │
    └─ No → Other special characters
        Example: U2 (number in name)
        Action: Keep as-is if legitimate
```

## Special Cases

### Sea Hear Now Festival
- Concert 1058 (2022-09-17): Stevie Nicks
- Concert 1059 (2022-09-18): Green Day
- **Action**: Set festival_name = "Sea Hear Now", extract artist from parentheses

### Stand Up for Heroes
- Annual charity event at Madison Square Garden
- Features multiple artists
- **Action**: Set festival_name = "Stand Up for Heroes", list primary performer

### Bruce Springsteen Special Events
- "7th Annual J. Henry" - Charity event, likely a festival
- "Light of Day" - Annual benefit concert series, **IS a festival**
- "Stand Up for Heroes" - As above

### U2
- 18 instances
- **Action**: Keep as "U2" - the number is part of the band name

## After Editing

Once you've reviewed and corrected the CSV:

1. Save the file
2. Run: `python3 scripts/apply_artist_corrections.py website/data/headliners_to_review.csv`
3. The script will:
   - Update artist names in Firestore
   - Set festival_name field for festivals
   - Change role to 'festival_performer' where appropriate
4. Re-export: `python3 scripts/export_to_web.py`
5. Deploy: `firebase deploy --only hosting`

## Pre-Filled Suggestions

The CSV has been pre-filled with intelligent suggestions for:
- **FESTIVAL**: Known festivals have artist extracted and festival name set
- **GUEST**: Guest artist info identified
- **NOTE**: Special event notes identified (100th show, etc.)

**Review these suggestions** - they're smart guesses but may need adjustment!

## Questions?

If you're unsure about a particular concert:
1. Check the `current_festival_name` column - does it already have a festival set?
2. Look at the venue and date - is it a known festival location/time?
3. Check if there are multiple concerts on consecutive days with the same pattern
4. Leave a note and we can review it together
