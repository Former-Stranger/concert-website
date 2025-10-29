# Festival Tracking System

## Overview

The concert website tracks festivals using **internal database fields**, not from setlist.fm API data. This is because **setlist.fm API does not provide any festival-specific fields or indicators**.

## Database Schema

### Firestore `concerts` Collection

```javascript
{
  id: "334",
  date: "2008-04-06",
  venue_name: "Great South Bay Music Festival",
  city: "Oakdale",
  state: "NY",
  festival_name: "Multi-Artist Show",  // <-- FESTIVAL TRACKING FIELD
  artists: [
    {
      artist_id: "123",
      artist_name: "Jackson Browne",
      role: "headliner",           // or "festival_performer"
      position: 1
    }
  ],
  // ... other fields
}
```

### Key Fields for Festival Tracking

1. **`festival_name`** (string, optional)
   - Primary field for marking concerts as festivals
   - Common values:
     - `"Multi-Artist Show"` (245 concerts) - Generic multi-artist events
     - `"Outlaw Festival"` (2 concerts) - Named festival series
     - `"Newport Folk Festival"` (1 concert)
     - `null` - Regular concerts (1,019 concerts)

2. **`role`** in artists array
   - `"headliner"` - Main artist at regular concerts
   - `"festival_performer"` - Artist performing at festivals
   - `"opener"` - Opening act

3. **`venue_name`**
   - Sometimes the venue name IS the festival name
   - Example: "Great South Bay Music Festival"

## Current State Analysis

### Statistics (as of dataset)
- **Total concerts:** 1,275
- **Concerts with festival_name:** 256 (20%)
- **Concerts without festival_name:** 1,019 (80%)
- **Unique festival names:** 11

### Distribution by Festival Name
```
Multi-Artist Show           245 concerts (95.7% of festivals)
Outlaw Festival              2 concerts
Newport Folk Festival        1 concert
SOULSHINE                    1 concert
Candlelight Concerts         1 concert
Light of Day 22              1 concert
John Henry's Friends         1 concert
BB King                      1 concert
Pearl Jam                    1 concert
Newtown Benefit              1 concert
12-12-12 Concert For Sandy   1 concert
```

## Tracking Patterns

### Pattern 1: festival_name Set, Regular Venue
**Most common pattern** - Multi-artist shows at regular venues

```javascript
{
  id: "1275",
  date: "2025-08-10",
  venue_name: "Jones Beach Theater",      // Regular venue
  festival_name: "Multi-Artist Show",     // Festival indicator
  artists: [
    {artist_name: "The Doobie Brothers", role: "headliner"},
    {artist_name: "Coral Reefer Band", role: "headliner"}
  ]
}
```

### Pattern 2: "Festival" in Venue Name, No festival_name
**Inconsistent** - Some festivals tracked only in venue name

```javascript
{
  id: "334",
  date: "2008-04-06",
  venue_name: "Great South Bay Music Festival",  // Festival is venue
  festival_name: null,                           // Not set!
  artists: [
    {artist_name: "Jackson Browne", role: "headliner"}
  ]
}
```

### Pattern 3: Both festival_name AND "Festival" in Venue
**Rare but correct** - Proper dual tracking

```javascript
{
  id: "443",
  date: "2010-09-05",
  venue_name: "Great South Bay Music Festival",
  festival_name: "Multi-Artist Show",
  artists: [
    {artist_name: "Keith Urban", role: "headliner"},
    {artist_name: "Kris Allen", role: "headliner"}
  ]
}
```

## Data Issues & Inconsistencies

### Issue 1: Inconsistent "Great South Bay Music Festival" Tracking
- 10 concerts have venue_name = "Great South Bay Music Festival"
- Only 2 of these have festival_name set
- **8 concerts are not marked as festivals despite being at a festival venue**

Examples:
- Concert 334 (2008-04-06): Jackson Browne - `festival_name: null` ❌
- Concert 443 (2010-09-05): Keith Urban - `festival_name: "Multi-Artist Show"` ✅

### Issue 2: "Multi-Artist Show" Overuse
- 245 out of 256 festival concerts (95.7%) use this generic label
- Loses information about actual festival names
- Makes it hard to distinguish:
  - Actual festivals (Bonnaroo, Newport, etc.)
  - Co-headliner tours
  - One-off multi-artist shows

### Issue 3: Missing Role Distinction
- `role: "festival_performer"` exists in schema but **rarely used**
- Most festival artists still marked as `role: "headliner"`
- Can't distinguish festival performers from tour co-headliners

## How Export Script Handles Festivals

The export script (`scripts/export_to_web.py`) treats festivals identically to regular concerts:

1. **Exports `festival_name` to JSON** (lines 66, 131, 489, 555)
2. **Filters to primary artists** using `role in ['headliner', 'festival_performer']`
3. **No special processing** for festivals vs regular concerts

### Exported JSON Structure
```json
{
  "id": "334",
  "date": "2008-04-06",
  "venue": "Great South Bay Music Festival",
  "city": "Oakdale",
  "state": "NY",
  "artists": "Jackson Browne",
  "festival_name": null,
  "hasSetlist": false
}
```

## setlist.fm API Reality

### What setlist.fm API DOES NOT Provide
❌ No `festival` field
❌ No `eventType` field
❌ No `isFestival` flag
❌ No festival classification

### What setlist.fm API DOES Provide
✅ `tour` field (sometimes contains festival name like "Bonnaroo 2019")
✅ `info` field (sometimes mentions stage names or set times)
✅ `venue` data (but no venue type indicator)

### Example: Bonnaroo Festival Setlist
```javascript
{
  "id": "7b9daaac",
  "eventDate": "13-10-2019",
  "artist": {"name": "Deftones"},
  "venue": {"name": "Great Stage Park", "city": {"name": "Manchester"}},
  "tour": null,  // No tour field
  "info": "\"Heaven\" stage. Set time: 18:00 - 19:00",  // Only hint
  // NO FESTIVAL FIELD EXISTS
}
```

## Recommendations

### Short-term Fixes

1. **Standardize Great South Bay Tracking**
   - Update all 8 concerts with venue="Great South Bay Music Festival" to have `festival_name` set
   - Decision needed: Use actual festival name or "Multi-Artist Show"?

2. **Use More Specific Festival Names**
   - Replace generic "Multi-Artist Show" with actual festival names when known
   - Examples:
     - "Bonnaroo 2019"
     - "Newport Folk Festival 2024"
     - "Great South Bay Music Festival 2008"

3. **Document Festival Classification Rules**
   - When should `festival_name` be set?
   - Multi-artist show at regular venue: Set `festival_name`?
   - Co-headliner tour: Set `festival_name`?

### Long-term Improvements

1. **Add `event_type` Field**
   ```javascript
   {
     event_type: "festival" | "tour" | "solo" | "residency",
     festival_name: "Bonnaroo 2024",  // If event_type = "festival"
     tour_name: "Summer Tour 2024"    // If event_type = "tour"
   }
   ```

2. **Use `festival_performer` Role Consistently**
   - Mark all festival artists with `role: "festival_performer"`
   - Reserve `role: "headliner"` for regular concerts and tours

3. **Create Festival Venue Registry**
   - Maintain list of known festival venues
   - Auto-suggest festival_name when venue is in registry

4. **Import Festival Data from External Sources**
   - Scrape festival lineups from festival websites
   - Use MusicBrainz or other APIs that track events better

## Current Workflow

### Adding a New Concert

**Manual Process:**
1. User adds concert via web form or script
2. If multiple artists → consider setting `festival_name`
3. If venue name contains "festival" → consider setting `festival_name`
4. **No automated festival detection**

### Fetching Setlists

**setlist.fm Integration:**
1. Script searches setlist.fm by artist/date/venue
2. Returns setlist data (if exists)
3. **No festival information returned**
4. Festival classification remains manual

## Questions to Resolve

1. **What defines a "festival" in your system?**
   - Multiple artists on same bill?
   - Specific venue types?
   - Named event series?
   - All of the above?

2. **Should "Multi-Artist Show" be replaced?**
   - Use actual festival names?
   - Distinguish between festivals and co-headliner tours?
   - Keep generic label for simplicity?

3. **How to handle historical data?**
   - Review and update 8 Great South Bay concerts?
   - Audit all 245 "Multi-Artist Show" entries?
   - Leave as-is and improve going forward?

4. **Role classification rules?**
   - When to use `festival_performer` vs `headliner`?
   - Should co-headliner tours use `festival_performer`?

## Summary

- **Festival tracking is entirely manual** in your system
- **setlist.fm API provides no festival data**
- **Current system has inconsistencies** but is functional
- **Needs clear rules and data cleanup** to improve accuracy
- **Consider adding more structured event_type classification**
