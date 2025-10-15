# Setlist.fm Integration Guide

This guide explains how to fetch and analyze setlist data from setlist.fm for your concert database.

## Overview

The setlist.fm integration allows you to:
- ✅ Fetch detailed setlists for concerts in your database
- ✅ Store songs played with position and metadata
- ✅ Analyze patterns like most common opening/closing songs
- ✅ Answer questions like "What song did [Artist] play most at the end of concerts?"
- ✅ Track cover songs and encore statistics

## Prerequisites

### 1. Get a setlist.fm API Key

1. Visit https://www.setlist.fm/
2. Create an account (if you don't have one)
3. Go to https://www.setlist.fm/settings/api
4. Request an API key
5. Copy your API key

**Important Notes:**
- API is free for non-commercial use
- Rate limit: 2 requests/second, 1,440 requests/day (standard API key)
- Be respectful of the rate limits

### 2. Add Setlist Schema to Database

```bash
python3 scripts/add_setlists_schema.py
```

This creates two new tables:
- `setlists` - Metadata for each concert's setlist
- `setlist_songs` - Individual songs with position and details

## Usage

### Step 1: Test the API Client

Test that your API key works:

```bash
python3 scripts/setlistfm_client.py YOUR_API_KEY
```

This will test fetching Kip Moore's setlist from Ridgefield Playhouse (May 9, 2019).

### Step 2: Fetch Setlists

#### Fetch all setlists (skip existing):
```bash
python3 scripts/fetch_setlists.py YOUR_API_KEY
```

#### Test with just 10 concerts:
```bash
python3 scripts/fetch_setlists.py YOUR_API_KEY --limit 10
```

#### Re-fetch all (including existing):
```bash
python3 scripts/fetch_setlists.py YOUR_API_KEY --all
```

#### Show statistics only:
```bash
python3 scripts/fetch_setlists.py YOUR_API_KEY --stats-only
```

**Expected Time:**
- With ~1,200 past concerts at ~1.67 requests/second: ~12 hours
- Limited by daily quota of 1,440 requests: can process ~1,440 concerts per day
- The script includes automatic rate limiting
- Expected match rate: 40-60% depending on artist popularity
- Note: Each concert may require 1-3 API calls (tries different search strategies)

**What happens:**
1. Queries your database for concerts with dates
2. For each concert, searches setlist.fm by artist, venue, city, state, and date
3. If found, stores the setlist and all songs in order
4. Shows progress every 10 concerts
5. Displays final statistics

### Step 3: Analyze Setlists

#### Overall analysis (all artists):
```bash
python3 scripts/analyze_setlists.py
```

Shows:
- Most common closing songs (all artists)
- Most common opening songs (all artists)
- Most common encore songs (all artists)
- Most covered artists

#### Artist-specific analysis:
```bash
python3 scripts/analyze_setlists.py "Kip Moore"
```

Shows:
- Number of setlists available
- Average songs per show
- Encore percentage
- Most played songs overall
- Most common opening songs
- Most common closing songs
- Most common encore songs
- Opening vs closing comparison

#### Examples:
```bash
# Analyze Bruce Springsteen setlists
python3 scripts/analyze_setlists.py "Bruce Springsteen"

# Analyze Billy Joel setlists
python3 scripts/analyze_setlists.py "Billy Joel"

# Analyze Kip Moore setlists
python3 scripts/analyze_setlists.py "Kip Moore"
```

## Example Queries

Once you have setlist data, you can run custom SQL queries:

### Find Kip Moore's most common closing song:
```sql
SELECT
    ss.song_name,
    COUNT(*) as times
FROM setlist_songs ss
JOIN setlists sl ON ss.setlist_id = sl.id
JOIN concerts c ON sl.concert_id = c.id
JOIN concert_artists ca ON c.id = ca.concert_id
JOIN artists a ON ca.artist_id = a.id
WHERE LOWER(a.canonical_name) LIKE '%kip moore%'
  AND ss.position = (
      SELECT MAX(position)
      FROM setlist_songs ss2
      WHERE ss2.setlist_id = ss.setlist_id
  )
GROUP BY ss.song_name
ORDER BY times DESC;
```

### Find all covers played at your concerts:
```sql
SELECT
    a.canonical_name as artist,
    ss.song_name,
    ss.cover_artist,
    c.date,
    v.canonical_name as venue
FROM setlist_songs ss
JOIN setlists sl ON ss.setlist_id = sl.id
JOIN concerts c ON sl.concert_id = c.id
JOIN concert_artists ca ON c.id = ca.concert_id
JOIN artists a ON ca.artist_id = a.id
JOIN venues v ON c.venue_id = v.id
WHERE ss.is_cover = 1
ORDER BY c.date DESC;
```

### Find longest setlists:
```sql
SELECT
    a.canonical_name as artist,
    v.canonical_name as venue,
    c.date,
    sl.song_count
FROM setlists sl
JOIN concerts c ON sl.concert_id = c.id
JOIN concert_artists ca ON c.id = ca.concert_id
JOIN artists a ON ca.artist_id = a.id
JOIN venues v ON c.venue_id = v.id
ORDER BY sl.song_count DESC
LIMIT 20;
```

### Find shows with the most encores:
```sql
SELECT
    a.canonical_name as artist,
    v.canonical_name as venue,
    c.date,
    COUNT(*) as encore_song_count
FROM setlist_songs ss
JOIN setlists sl ON ss.setlist_id = sl.id
JOIN concerts c ON sl.concert_id = c.id
JOIN concert_artists ca ON c.id = ca.concert_id
JOIN artists a ON ca.artist_id = a.id
JOIN venues v ON c.venue_id = v.id
WHERE ss.encore > 0
GROUP BY sl.id
ORDER BY encore_song_count DESC
LIMIT 20;
```

## Database Schema

### `setlists` table:
- `id` - Primary key
- `concert_id` - Foreign key to concerts table
- `setlistfm_id` - ID from setlist.fm
- `setlistfm_url` - Direct link to setlist on setlist.fm
- `fetched_at` - Timestamp of when data was fetched
- `song_count` - Total number of songs
- `has_encore` - Boolean indicating if show had encore
- `notes` - Optional notes

### `setlist_songs` table:
- `id` - Primary key
- `setlist_id` - Foreign key to setlists table
- `position` - Song position in show (1 = opener, MAX = closer)
- `song_name` - Name of the song
- `set_name` - Name of the set (e.g., "Main Set", "Encore")
- `encore` - Encore number (0 = not encore, 1+ = encore number)
- `is_cover` - Boolean indicating if song is a cover
- `cover_artist` - Original artist if cover
- `is_tape` - Boolean indicating if played from tape/recording
- `info` - Additional info about the song

## Limitations

### Coverage:
- Not all concerts will have setlists on setlist.fm
- Smaller artists and older shows may have less coverage
- User-submitted data quality varies

### Matching:
- Script attempts to match by artist, venue, city, state, and exact date
- If exact match fails, tries broader search (without venue)
- Multi-artist shows may require manual review

### Rate Limits:
- 2 requests/second (enforced by the client at ~1.67 req/sec)
- 1,440 requests/day (standard API key)
- Script automatically respects these limits
- May need to run across multiple days for large databases

## Tips

1. **Start with a test run**: Use `--limit 10` first
2. **Run overnight**: Full fetch may take 1-2 hours
3. **Re-run periodically**: New setlists get added to setlist.fm regularly
4. **Check coverage**: Run with `--stats-only` to see what you have
5. **Artist name variations**: If an artist isn't matching, check how they're listed on setlist.fm

## Troubleshooting

### No matches found:
- Artist name might be different on setlist.fm
- Concert might not be in setlist.fm database
- Try searching setlist.fm manually to verify

### Rate limit errors:
- Script automatically waits and retries
- If persistent, your API key may have different limits

### Missing data:
- Some setlists on setlist.fm are incomplete
- Users may not have submitted full data

## Future Enhancements

Potential additions:
- Manual setlist entry for concerts not on setlist.fm
- Setlist comparison (how similar are two shows?)
- Song frequency heatmaps over time
- Venue-specific setlist patterns
- Integration with Spotify for playlist generation

## Credits

Data provided by [setlist.fm](https://www.setlist.fm/) API.
Please respect their [terms of service](https://www.setlist.fm/help/terms).
