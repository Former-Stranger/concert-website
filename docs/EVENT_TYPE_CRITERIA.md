# Event Type Classification Criteria

## Overview

Concerts are classified into one of five event types based on specific criteria. This classification helps distinguish between regular concerts, tours, festivals, and special events.

## Event Types

### 1. **solo**
A regular concert with a single headliner, possibly with opening acts.

**Criteria:**
- ✅ One headliner
- ✅ May have one or more opening acts (`role: "opener"`)
- ✅ Single stage/venue performance
- ❌ Not part of a named tour
- ❌ No other headliners
- ❌ Not a benefit or special event

**Examples:**
- Billy Joel at Madison Square Garden
- Bruce Springsteen at Capitol Theatre
- John Hiatt at City Winery

**Database Fields:**
```javascript
{
  event_type: "solo",
  festival_name: null,
  tour_name: null,
  artists: [
    {artist_name: "Billy Joel", role: "headliner"},
    {artist_name: "Opening Act", role: "opener"}
  ]
}
```

---

### 2. **tour**
A concert that is part of a named tour series, featuring one or more headliners traveling together.

**Criteria:**
- ✅ Part of a named tour (tour name provided)
- ✅ One or more headliners
- ✅ Tour is advertised/promoted with a specific name
- ✅ Multiple dates across different venues (same lineup)
- ❌ Not a festival (no multiple stages, not a festival venue)

**Examples:**
- "2018 North American Summer Tour" - Rod Stewart & Cyndi Lauper
- "Outlaw Festival 2025" - Bob Dylan & Willie Nelson touring together
- "Stadium Tour 2024" - Band on multi-city tour

**Database Fields:**
```javascript
{
  event_type: "tour",
  festival_name: null,
  tour_name: "2018 North American Summer Tour",
  artists: [
    {artist_name: "Rod Stewart", role: "headliner"},
    {artist_name: "Cyndi Lauper", role: "headliner"}
  ]
}
```

**Notes:**
- Co-headliner tours are still "tour" type
- Tour name should match official tour name
- setlist.fm often provides tour names in API response

---

### 3. **festival**
A large-scale event with many artists performing, typically across multiple stages, at a specific festival venue or event.

**Criteria:**
- ✅ Named festival event (e.g., "Bonnaroo", "Newport Folk Festival", "Great South Bay Music Festival")
- ✅ Multiple artists performing (typically 10+ artists across all stages)
- ✅ Often multiple stages or venues
- ✅ Ticketed as a festival (not individual artist tickets)
- ✅ Usually held at known festival venues or outdoor spaces
- ✅ May span multiple days

**Examples:**
- Bonnaroo Music Festival (Great Stage Park, Manchester, TN)
- Newport Folk Festival
- Great South Bay Music Festival (Oakdale, NY)
- Lollapalooza
- Outside Lands

**Database Fields:**
```javascript
{
  event_type: "festival",
  festival_name: "Bonnaroo 2024",
  tour_name: null,
  artists: [
    {artist_name: "Foo Fighters", role: "festival_performer"},
    {artist_name: "Tyler, the Creator", role: "festival_performer"},
    // ... many more artists
  ]
}
```

**Special Cases:**
- If you attended a festival but only saw 1-2 artists, it's still a "festival"
- The `artists` array contains only the artists YOU saw
- The venue name is often the festival venue (e.g., "Great Stage Park")
- Use `role: "festival_performer"` for all artists at festivals

---

### 4. **multi_artist_show**
A special event with 2+ headliners performing together, but NOT a tour or festival. Typically a one-off show or benefit concert.

**Criteria:**
- ✅ Multiple headliners (2+) performing together
- ✅ NOT part of a touring series
- ✅ NOT a festival (single venue, single stage, limited artists)
- ✅ Often a benefit, tribute, or special event
- ✅ One-off or limited run show
- ✅ All artists are equally billed (no clear opener/headliner hierarchy)

**Examples:**
- Benefit concerts (Sandy Relief, Newtown Benefit)
- Tribute shows (Tribute to Phil Lesh with multiple artists)
- One-off co-bills at theaters/clubs (2-3 artists sharing a bill)
- Special events ("Light of Day" celebration)
- Holiday shows with multiple artists

**Database Fields:**
```javascript
{
  event_type: "multi_artist_show",
  festival_name: "12-12-12 Concert For Sandy Relief",  // Event name
  tour_name: null,
  artists: [
    {artist_name: "Bruce Springsteen", role: "headliner"},
    {artist_name: "Paul McCartney", role: "headliner"},
    {artist_name: "The Who", role: "headliner"}
  ]
}
```

**Notes:**
- Use `festival_name` field to store the event name (even though it's not a festival)
- This is a legacy field name - it stores "special event name"
- Could be renamed to `event_name` in future schema update

---

### 5. **other**
Catch-all category for events that don't fit the above types.

**Criteria:**
- ✅ Doesn't match criteria for solo, tour, festival, or multi_artist_show
- ✅ Unusual performance format
- ✅ Residency shows (same artist, same venue, multiple consecutive dates)
- ✅ Acoustic/intimate shows that are neither tour nor regular concert
- ✅ Virtual concerts
- ✅ Special formats (seated shows, orchestral performances, etc.)

**Examples:**
- Residency shows (Billy Joel's monthly MSG shows)
- Movie theater screenings with live performance
- Orchestral performances (artist with symphony)
- Drive-in concerts
- Virtual/streaming concerts

**Database Fields:**
```javascript
{
  event_type: "other",
  festival_name: null,
  tour_name: null,
  event_notes: "Monthly residency show",  // Optional explanation
  artists: [
    {artist_name: "Billy Joel", role: "headliner"}
  ]
}
```

---

## Decision Tree

Use this flowchart to classify concerts:

```
START
  │
  ├─ Is this at a known festival venue OR named festival event?
  │   └─ YES → festival
  │
  ├─ Does it have a tour name AND is part of multi-date tour?
  │   └─ YES → tour
  │
  ├─ Are there 2+ headliners performing together?
  │   └─ YES
  │       ├─ Is it part of a touring series?
  │       │   └─ YES → tour
  │       │
  │       └─ Is it a one-off or benefit show?
  │           └─ YES → multi_artist_show
  │
  ├─ Is it a single headliner, regular concert?
  │   └─ YES → solo
  │
  └─ Doesn't fit any category?
      └─ other
```

## Edge Cases & Guidelines

### Co-Headliner Tours vs Multi-Artist Shows

**Co-Headliner Tour:**
- Same two artists perform multiple dates together
- Has an official tour name
- Promoted as a tour
- **Classification:** `tour`
- **Example:** Rod Stewart & Cyndi Lauper "2018 Summer Tour"

**Multi-Artist One-Off:**
- Artists come together for single show or limited run
- No tour name
- Often a benefit or special event
- **Classification:** `multi_artist_show`
- **Example:** Sandy Relief concert with multiple stars

### Festival Attendance

**You attended a festival:**
- Even if you only saw 1 artist
- Even if you only went one day
- **Still classify as:** `festival`
- **Store in artists array:** Only the artists YOU personally saw
- **Note:** This represents YOUR concert history, not the full festival lineup

### Openers vs Co-Headliners

**Clear opener/headliner:**
- Opening act performs shorter set first
- Headliner performs longer set last
- **Classification:** `solo` (if not on tour)
- **Roles:** opener + headliner

**Co-headliners:**
- Both artists have equal billing
- Similar set lengths
- Order may rotate
- **Classification:** Depends on context (tour vs one-off)

### Residency Shows

**Monthly/weekly recurring shows:**
- Same artist, same venue, over extended period
- Not a tour (doesn't move venues)
- **Classification:** `other`
- **Example:** Billy Joel's monthly MSG shows

---

## Database Schema Changes Needed

### Current Schema
```javascript
{
  festival_name: string | null  // Currently used for multiple purposes
}
```

### Proposed New Schema
```javascript
{
  event_type: "solo" | "tour" | "festival" | "multi_artist_show" | "other",
  event_name: string | null,     // Name of festival/benefit/special event
  tour_name: string | null,      // Name of tour (if event_type = "tour")
  event_notes: string | null     // Optional notes about event format
}
```

### Migration Strategy

**Option 1: Add new fields, keep old**
```javascript
{
  // OLD (keep for compatibility)
  festival_name: "Multi-Artist Show",

  // NEW
  event_type: "multi_artist_show",
  event_name: "12-12-12 Concert For Sandy Relief",
  tour_name: null
}
```

**Option 2: Rename and replace**
- Rename `festival_name` → `event_name`
- Add `event_type` as required field
- Add `tour_name` as optional field
- Run migration script to classify all existing concerts

---

## Classification Examples

### Example 1: Regular Concert
```javascript
{
  event_type: "solo",
  event_name: null,
  tour_name: null,
  artists: [
    {artist_name: "John Hiatt", role: "headliner"},
    {artist_name: "Opening Act", role: "opener"}
  ]
}
```

### Example 2: Tour Show
```javascript
{
  event_type: "tour",
  event_name: null,
  tour_name: "Outlaw Festival 2025",
  artists: [
    {artist_name: "Bob Dylan", role: "headliner"},
    {artist_name: "Willie Nelson", role: "headliner"}
  ]
}
```

### Example 3: Festival
```javascript
{
  event_type: "festival",
  event_name: "Bonnaroo 2024",
  tour_name: null,
  venue_name: "Great Stage Park",
  artists: [
    {artist_name: "Foo Fighters", role: "festival_performer"},
    {artist_name: "Tyler, the Creator", role: "festival_performer"}
  ]
}
```

### Example 4: Benefit Concert
```javascript
{
  event_type: "multi_artist_show",
  event_name: "12-12-12 Concert For Sandy Relief",
  tour_name: null,
  artists: [
    {artist_name: "Bruce Springsteen", role: "headliner"},
    {artist_name: "Paul McCartney", role: "headliner"},
    {artist_name: "The Who", role: "headliner"}
  ]
}
```

### Example 5: Residency
```javascript
{
  event_type: "other",
  event_name: "Billy Joel Monthly Residency",
  tour_name: null,
  event_notes: "Monthly residency show at MSG",
  artists: [
    {artist_name: "Billy Joel", role: "headliner"}
  ]
}
```

---

## Implementation Checklist

- [ ] Add `event_type` field to Firestore schema
- [ ] Add `event_name` field (or rename `festival_name`)
- [ ] Add `tour_name` field
- [ ] Add `event_notes` field (optional)
- [ ] Update export script to include new fields
- [ ] Create classification script for existing data
- [ ] Update web forms to include event type selection
- [ ] Update display logic to show event type
- [ ] Document API changes

---

## Questions for Review

1. **Should residency shows be "other" or separate "residency" type?**
2. **Should `event_name` replace `festival_name` or be separate?**
3. **How to handle historical data - automated classification or manual review?**
4. **Should setlist.fm tour names auto-populate `tour_name` field?**
5. **Display event type on concert pages? Badge/icon?**
