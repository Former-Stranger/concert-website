# Setlist.fm Venue API Research

## Summary of Findings

### How Venue Name Changes Are Handled

**Setlist.fm creates SEPARATE venue IDs for each name change.** They do NOT update the venue name in place.

### Example: Connecticut Amphitheater (Hartford, CT)

This venue has changed names multiple times over the years, and setlist.fm tracks each as a separate venue:

| Venue ID | Name | Active Period | Total Setlists |
|----------|------|---------------|----------------|
| `6bd63ed2` | Meadows Music Theater | 1995-2002 | 467 |
| `13d2f57d` | ctnow.com Meadows Music Theatre | 2000-2005 | 378 |
| `4bd6cb7a` | Comcast Theatre | 2009-2013 | 496 |
| `13d2f571` | XFINITY Theatre | 2013-present | 799 |

**Timeline:**
- **1995-2002**: Meadows Music Theater
- **2000-2005**: ctnow.com Meadows Music Theatre (overlapping with above)
- **2009-2013**: Comcast Theatre
- **2013-present**: XFINITY Theatre

**Note:** There appears to be some overlap in the data, likely due to:
1. Retroactive corrections by users
2. Different stages/venues at the same location
3. Gradual transitions between names

### Additional Variant Found
- `23d704cb`: Scion Festival Stage at Comcast Theatre (specific stage)

---

## Venue API Capabilities

### Available Endpoints

#### 1. Search Venues
**Endpoint:** `GET /search/venues`

**Parameters:**
- `name` - Venue name (partial match)
- `cityName` - City name
- `stateCode` - State code (e.g., CT, NY)
- `country` - Country code (e.g., US, CA, MX)
- `p` - Page number

**Response:**
```json
{
  "type": "venues",
  "itemsPerPage": 30,
  "page": 1,
  "total": 10000,
  "venue": [...]
}
```

**Limitations:**
- Returns max 10,000 results (even if more exist)
- 30 items per page = 333 pages maximum
- Some venues have blank names (data quality issues)
- No way to get ALL venues in a single query

#### 2. Get Venue Details
**Endpoint:** `GET /venue/{venueId}`

**Returns:**
```json
{
  "id": "13d2f571",
  "name": "XFINITY Theatre",
  "city": {
    "id": "4835797",
    "name": "Hartford",
    "state": "Connecticut",
    "stateCode": "CT",
    "coords": {
      "lat": 41.7637111,
      "long": -72.6850932
    },
    "country": {
      "code": "US",
      "name": "United States"
    }
  },
  "url": "https://www.setlist.fm/venue/xfinity-theatre-hartford-ct-usa-13d2f571.html"
}
```

**Note:** Does NOT include historical names or aliases.

#### 3. Get Venue Setlists
**Endpoint:** `GET /venue/{venueId}/setlists`

**Parameters:**
- `p` - Page number

**Returns:** Standard setlist search results for that venue

---

## Getting All North American Venues

### The Challenge

There is **NO direct API endpoint** to get all venues in North America. However, you can:

### Option 1: Search by Country (Limited)
```python
# Get US venues (max 10,000 results)
GET /search/venues?country=US

# Get Canadian venues
GET /search/venues?country=CA

# Get Mexican venues
GET /search/venues?country=MX
```

**Pros:**
- Simple query
- Gets most major venues

**Cons:**
- Limited to 10,000 results per country
- Many results have blank names
- No guarantee of completeness

### Option 2: Search by State/Province
```python
# Iterate through all US states
states = ['AL', 'AK', 'AZ', ... 'WY']
for state in states:
    venues = search_venues(stateCode=state)
```

**Pros:**
- More comprehensive
- Likely stays under 10,000 per state

**Cons:**
- Requires ~50 queries for US states
- Still subject to data quality issues
- Need to handle pagination

### Option 3: Extract from Your Concert Data
The most reliable approach for your use case:

```python
# For each concert in your database:
# 1. Get the venue_id from the concert
# 2. Fetch venue details from API
# 3. Cache venue info locally
```

**Pros:**
- Only gets venues you care about
- Builds up over time
- No pagination issues

**Cons:**
- Not a complete North American list
- Requires processing your entire concert database

---

## Venue Data Structure

### What's Available in API

```python
{
  "id": str,              # Unique venue ID
  "name": str,            # Current venue name
  "city": {
    "id": str,            # City ID
    "name": str,          # City name
    "state": str,         # State/Province full name
    "stateCode": str,     # 2-letter code
    "coords": {
      "lat": float,       # Latitude
      "long": float       # Longitude
    },
    "country": {
      "code": str,        # Country code (US, CA, MX)
      "name": str         # Country name
    }
  },
  "url": str              # Setlist.fm venue page URL
}
```

### What's NOT Available

- ❌ Historical names/aliases
- ❌ Venue type (amphitheater, arena, theater, etc.)
- ❌ Capacity
- ❌ Opening/closing dates
- ❌ Parent company/operator
- ❌ Links to other venue IDs (for name changes)

---

## Implications for Your Database

### Current Approach
Your concert database stores `venue_name` as a string in each concert document. This is actually **better** than using venue IDs because:

1. **Preserves Historical Context**: If you attended "Comcast Theatre" in 2010, your concert shows "Comcast Theatre" not "XFINITY Theatre"

2. **Avoids Confusion**: A concert at "Meadows Music Theater" in 1998 is clearly different from one at "XFINITY Theatre" in 2023, even though it's the same physical location

3. **Flexibility**: You're not locked into setlist.fm's venue ID system

### Potential Enhancements

If you wanted to link venues across name changes, you could:

1. **Add venue_id field** to concerts (optional)
2. **Create a venue_aliases collection** in Firestore:
   ```json
   {
     "canonical_name": "XFINITY Theatre",
     "location": "Hartford, CT",
     "aliases": [
       {
         "name": "Meadows Music Theater",
         "setlistfm_venue_id": "6bd63ed2",
         "active_period": "1995-2002"
       },
       {
         "name": "ctnow.com Meadows Music Theatre",
         "setlistfm_venue_id": "13d2f57d",
         "active_period": "2000-2005"
       },
       {
         "name": "Comcast Theatre",
         "setlistfm_venue_id": "4bd6cb7a",
         "active_period": "2009-2013"
       },
       {
         "name": "XFINITY Theatre",
         "setlistfm_venue_id": "13d2f571",
         "active_period": "2013-present"
       }
     ],
     "coordinates": {
       "lat": 41.7637111,
       "long": -72.6850932
     }
   }
   ```

3. **Add venue merging UI**: Allow user to see all concerts at "the same venue" across name changes

---

## Recommendations

### For Your Current Project

**Don't change anything.** Your current approach is fine:
- Store venue name as it was at the time
- Store venue city and state
- This preserves historical accuracy

### If You Want to Add Venue Linking

1. Create a manual mapping for major venues that have changed names
2. Add a `venue_canonical_id` field to link related venues
3. Add a venue detail page that shows:
   - All names this venue has had
   - All concerts at this location (across all names)
   - Map with coordinates

### For Getting All North American Venues

**Not recommended unless you have a specific use case.** The API limitations and data quality issues make this impractical. Better to:
- Build venue data organically from your concert database
- Fetch venue details on-demand when needed
- Cache venue info locally to reduce API calls

---

## API Rate Limits

- **2 requests per second** (standard API key)
- **1,440 calls per day** (24 hours)

**Implications:**
- Getting all 10,000 US venues = 334 requests = ~3-4 minutes
- Getting all 50 US states = ~50-150 requests (depending on pagination)
- Well within daily limit for reasonable use

---

## Code Examples

### Search for Venue by Name and State
```python
from setlistfm_client import SetlistFMClient

client = SetlistFMClient(api_key)

# Search
response = client._make_request('/search/venues', {
    'name': 'Madison Square Garden',
    'stateCode': 'NY'
})

# Results
for venue in response.get('venue', []):
    print(f"{venue['id']}: {venue['name']}")
```

### Get All Historical Names for a Location
```python
def find_venue_aliases(venue_name, city, state):
    """Find all venue IDs for a location"""

    # Search for main name
    main_results = client._make_request('/search/venues', {
        'name': venue_name,
        'stateCode': state
    })

    # Check if there are venues at same coordinates
    # (setlist.fm doesn't provide this directly)

    return main_results.get('venue', [])
```

### Iterate Through US States
```python
US_STATES = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
             'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
             'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
             'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
             'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

all_venues = []
for state in US_STATES:
    page = 1
    while True:
        response = client._make_request('/search/venues', {
            'stateCode': state,
            'p': page
        })

        venues = response.get('venue', [])
        if not venues:
            break

        all_venues.extend(venues)

        # Check if there are more pages
        total = response.get('total', 0)
        if page * 30 >= total:
            break

        page += 1
        time.sleep(0.6)  # Rate limiting
```

---

## Additional Resources

- **API Documentation**: https://api.setlist.fm/docs/1.0/index.html
- **Venue Search**: https://www.setlist.fm/search/venues
- **Your API Key**: `DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE`
