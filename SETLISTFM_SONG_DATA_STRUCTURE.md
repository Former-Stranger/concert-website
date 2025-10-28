# Setlist.fm Song Data Structure

## Complete Song Data from API

Based on Cyndi Lauper's setlist at Madison Square Garden (August 7, 2018).

---

## Available Song Fields

### 1. Basic Song Information

```json
{
  "name": "I Drove All Night"
}
```

**Always present.** The song title.

---

### 2. Cover Information

When a song is a cover, the API provides:

```json
{
  "name": "All Through the Night",
  "cover": {
    "mbid": "3b88a652-36b2-4158-bec5-9d6fee5ef655",
    "name": "Jules Shear",
    "sortName": "Shear, Jules",
    "disambiguation": "",
    "url": "https://www.setlist.fm/setlists/jules-shear-3bd6a450.html"
  }
}
```

**Cover Object Fields:**
- `name` - Original artist name
- `mbid` - MusicBrainz ID for the original artist
- `sortName` - Sortable name format (Last, First)
- `disambiguation` - Additional info to distinguish artists with same name
- `url` - Link to original artist's setlist.fm page

**Example from Cyndi Lauper setlist:**

**Song: "All Through the Night"**
- Original Artist: Jules Shear
- MusicBrainz ID: 3b88a652-36b2-4158-bec5-9d6fee5ef655
- Setlist.fm URL: https://www.setlist.fm/setlists/jules-shear-3bd6a450.html

**Song: "Money Changes Everything"**
- Original Artist: The Brains
- MusicBrainz ID: 2f179135-b60c-4f8c-bfaf-8cf170bede4b
- Disambiguation: "American New Wave Band, 1980's"
- Setlist.fm URL: https://www.setlist.fm/setlists/the-brains-7bd46ed8.html

---

### 3. Song Info/Notes

Additional context or notes about the performance:

```json
{
  "name": "Alone in the Harbor",
  "info": "piece of new song from Upcoming Working Girl The Musicl"
}
```

**Use cases:**
- Premiere performances
- Special arrangements
- Dedications
- Partial performances
- Acoustic versions
- Medleys

---

### 4. Tape/Recording

Indicates the song was played from a tape or recording (not live):

```json
{
  "name": "Song Name",
  "tape": true
}
```

**Note:** This was not present in Cyndi Lauper's setlist but is available in the API.

---

### 5. Guest Artist (With)

When a song features a guest artist:

```json
{
  "name": "Song Name",
  "with": {
    "mbid": "artist-mbid-here",
    "name": "Guest Artist Name",
    "sortName": "Artist, Guest",
    "disambiguation": "",
    "url": "https://www.setlist.fm/setlists/guest-artist.html"
  }
}
```

**Note:** This was not present in Cyndi Lauper's setlist but is available in the API.

---

## Complete Song Object Structure

```javascript
{
  "name": string,           // Song title (REQUIRED)
  "cover": {                // Present if this is a cover song
    "mbid": string,         // MusicBrainz ID of original artist
    "name": string,         // Original artist name
    "sortName": string,     // Sortable name (Last, First)
    "disambiguation": string, // Additional context
    "url": string           // Setlist.fm page for original artist
  },
  "info": string,           // Additional notes about performance
  "tape": boolean,          // True if played from tape/recording
  "with": {                 // Guest artist information
    "mbid": string,
    "name": string,
    "sortName": string,
    "disambiguation": string,
    "url": string
  }
}
```

---

## What We're Currently Storing

### Current Format (from our database):

```json
{
  "position": 1,
  "name": "I Drove All Night",
  "set_name": "Set 1",
  "encore": 0,
  "is_cover": false,
  "cover_artist": null
}
```

### What We're Missing:

1. **MusicBrainz IDs** for original artists
2. **Sortable names** for original artists
3. **Disambiguation info** for original artists
4. **Setlist.fm URLs** for original artists
5. **Song info/notes** (performance context)
6. **Tape indicator** (if song was from recording)
7. **Guest artist information** (with field)

---

## Recommendations for Data Enhancement

### Priority 1: Add Cover Artist Details

**Current:**
```json
{
  "is_cover": true,
  "cover_artist": null
}
```

**Enhanced:**
```json
{
  "is_cover": true,
  "cover_artist": "Jules Shear",
  "cover_artist_mbid": "3b88a652-36b2-4158-bec5-9d6fee5ef655",
  "cover_artist_url": "https://www.setlist.fm/setlists/jules-shear-3bd6a450.html"
}
```

**Benefits:**
- Users can click to learn about original artist
- Proper attribution
- Rich data for music discovery

---

### Priority 2: Add Song Notes

**Current:**
```json
{
  "name": "Alone in the Harbor"
}
```

**Enhanced:**
```json
{
  "name": "Alone in the Harbor",
  "notes": "piece of new song from Upcoming Working Girl The Musical"
}
```

**Benefits:**
- Context about special performances
- Historical significance
- User interest

---

### Priority 3: Add Guest Artist Info

**Current:**
```json
{
  "name": "Thunder Road"
}
```

**Enhanced:**
```json
{
  "name": "Thunder Road",
  "guest_artist": "Jon Bon Jovi",
  "guest_artist_mbid": "...",
  "guest_artist_url": "..."
}
```

**Benefits:**
- Highlights special collaborations
- More accurate concert representation
- Search/filter by guest appearances

---

### Priority 4: Add Tape Indicator

**Current:**
```json
{
  "name": "Abbey Road Medley"
}
```

**Enhanced:**
```json
{
  "name": "Abbey Road Medley",
  "is_tape": true,
  "notes": "Played as intro music"
}
```

**Benefits:**
- Clarifies what was actually performed live
- Transparency about the show

---

## Updated Parsing Code

### Current Code (in create_coheadliner_setlists_847_auto.py):

```python
song_entry = {
    'position': position,
    'name': song_name,
    'set_name': set_display_name
}

# Add cover info if present
cover = song.get('cover')
if cover:
    song_entry['is_cover'] = True
    song_entry['original_artist'] = cover.get('name', '')
```

### Enhanced Version:

```python
song_entry = {
    'position': position,
    'name': song_name,
    'set_name': set_display_name
}

# Add cover info if present
cover = song.get('cover')
if cover:
    song_entry['is_cover'] = True
    song_entry['cover_artist'] = cover.get('name', '')
    song_entry['cover_artist_mbid'] = cover.get('mbid')
    song_entry['cover_artist_url'] = cover.get('url')
    song_entry['cover_artist_disambiguation'] = cover.get('disambiguation')
else:
    song_entry['is_cover'] = False
    song_entry['cover_artist'] = None

# Add song info/notes if present
info = song.get('info')
if info:
    song_entry['notes'] = info

# Add tape indicator if present
tape = song.get('tape')
if tape:
    song_entry['is_tape'] = True

# Add guest artist if present
with_artist = song.get('with')
if with_artist:
    song_entry['guest_artist'] = with_artist.get('name', '')
    song_entry['guest_artist_mbid'] = with_artist.get('mbid')
    song_entry['guest_artist_url'] = with_artist.get('url')
```

---

## Display Updates Needed

### concert.js Enhancement:

**Current:**
```javascript
${song.is_cover ? `
    <div class="text-sm mt-1 font-semibold" style="color: #c1502e;">
        <i class="fas fa-record-vinyl mr-1"></i>Cover of ${song.cover_artist}
    </div>
` : ''}
```

**Enhanced:**
```javascript
${song.is_cover ? `
    <div class="text-sm mt-1 font-semibold" style="color: #c1502e;">
        <i class="fas fa-record-vinyl mr-1"></i>
        Cover of
        ${song.cover_artist_url ?
            `<a href="${song.cover_artist_url}" target="_blank" class="hover:underline">${song.cover_artist}</a>` :
            song.cover_artist
        }
    </div>
` : ''}
${song.notes ? `
    <div class="text-sm mt-1 italic opacity-80">
        <i class="fas fa-info-circle mr-1"></i>${song.notes}
    </div>
` : ''}
${song.guest_artist ? `
    <div class="text-sm mt-1 font-semibold" style="color: #4ade80;">
        <i class="fas fa-user-plus mr-1"></i>
        with
        ${song.guest_artist_url ?
            `<a href="${song.guest_artist_url}" target="_blank" class="hover:underline">${song.guest_artist}</a>` :
            song.guest_artist
        }
    </div>
` : ''}
${song.is_tape ? `
    <div class="text-sm mt-1 opacity-70">
        <i class="fas fa-tape mr-1"></i>Recording
    </div>
` : ''}
```

---

## Migration Strategy

### Phase 1: Update Parsing (Low Risk)
1. Update `create_coheadliner_setlists_847_auto.py` to capture all fields
2. Update `parse_setlist_data()` function
3. Test with concert 847

### Phase 2: Update Display (Low Risk)
1. Update `concert.js` to show new fields
2. Handle missing data gracefully (backward compatible)
3. Test locally

### Phase 3: Backfill Data (Optional)
1. Re-fetch all existing setlists from setlist.fm
2. Update Firestore with enhanced data
3. Re-export to JSON

---

## Summary of Available Data

From the Cyndi Lauper example:

| Field | Count | Example |
|-------|-------|---------|
| Songs | 11 | "I Drove All Night" |
| Covers | 2 | "All Through the Night" (Jules Shear) |
| Cover Details | 2 | MusicBrainz ID, URL, disambiguation |
| Song Notes | 1 | "piece of new song from Upcoming Working Girl The Musical" |
| Tape | 0 | (not present in this setlist) |
| Guest Artists | 0 | (not present in this setlist) |

**Data Richness:** The API provides significantly more data than we're currently storing, particularly around:
- Cover song attribution with links
- Performance notes and context
- Guest collaborations
