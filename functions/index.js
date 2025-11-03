const functions = require('firebase-functions');
const fetch = require('node-fetch');
const admin = require('firebase-admin');
const {CloudBuildClient} = require('@google-cloud/cloudbuild');

// Initialize Firebase Admin SDK
admin.initializeApp();

const SETLISTFM_API_KEY = "DrR0j3jlKSLRrXSTsd_r71QUIA24ZQydjpsE";

// CORS-enabled function to fetch setlist data from setlist.fm
exports.fetchSetlist = functions.https.onRequest(async (req, res) => {
  // Enable CORS
  res.set('Access-Control-Allow-Origin', '*');
  res.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.set('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight request
  if (req.method === 'OPTIONS') {
    res.status(204).send('');
    return;
  }

  // Only allow GET requests
  if (req.method !== 'GET') {
    res.status(405).send('Method Not Allowed');
    return;
  }

  const setlistId = req.query.id;

  if (!setlistId) {
    res.status(400).json({ error: 'Missing setlist ID' });
    return;
  }

  try {
    const apiUrl = `https://api.setlist.fm/rest/1.0/setlist/${setlistId}`;

    const response = await fetch(apiUrl, {
      headers: {
        'x-api-key': SETLISTFM_API_KEY,
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      if (response.status === 404) {
        res.status(404).json({ error: 'Setlist not found' });
        return;
      }
      res.status(response.status).json({ error: `Setlist.fm API error: ${response.status}` });
      return;
    }

    const data = await response.json();
    res.status(200).json(data);

  } catch (error) {
    console.error('Error fetching setlist:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Fetch setlist with multi-artist detection
// Given one setlist URL, find all other artists performing at the same venue/date
exports.fetchSetlistWithMultiArtist = functions.https.onRequest(async (req, res) => {
  // Enable CORS
  res.set('Access-Control-Allow-Origin', '*');
  res.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.set('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight request
  if (req.method === 'OPTIONS') {
    res.status(204).send('');
    return;
  }

  // Only allow GET requests
  if (req.method !== 'GET') {
    res.status(405).send('Method Not Allowed');
    return;
  }

  const setlistId = req.query.id;

  if (!setlistId) {
    res.status(400).json({ error: 'Missing setlist ID' });
    return;
  }

  try {
    // STEP 1: Fetch the provided setlist
    const setlistUrl = `https://api.setlist.fm/rest/1.0/setlist/${setlistId}`;
    const setlistResponse = await fetch(setlistUrl, {
      headers: {
        'x-api-key': SETLISTFM_API_KEY,
        'Accept': 'application/json'
      }
    });

    if (!setlistResponse.ok) {
      if (setlistResponse.status === 404) {
        res.status(404).json({ error: 'Setlist not found' });
        return;
      }
      res.status(setlistResponse.status).json({ error: `Setlist.fm API error: ${setlistResponse.status}` });
      return;
    }

    const setlistData = await setlistResponse.json();

    // Extract venue and date
    const venue = setlistData.venue || {};
    const venueName = venue.name;
    const venueId = venue.id;
    const eventDate = setlistData.eventDate; // Format: DD-MM-YYYY

    if (!venueName || !eventDate) {
      // If we can't detect other artists, just return the single setlist
      res.status(200).json({
        setlists: [setlistData],
        multiArtistDetectionFailed: true
      });
      return;
    }

    // STEP 2: Search for all setlists at this venue on this date
    const searchUrl = `https://api.setlist.fm/rest/1.0/search/setlists?venueId=${venueId}&date=${eventDate}`;
    const searchResponse = await fetch(searchUrl, {
      headers: {
        'x-api-key': SETLISTFM_API_KEY,
        'Accept': 'application/json'
      }
    });

    if (!searchResponse.ok) {
      // If search fails, just return the single setlist
      res.status(200).json({
        setlists: [setlistData],
        multiArtistDetectionFailed: true
      });
      return;
    }

    const searchData = await searchResponse.json();
    const allSetlists = searchData.setlist || [];

    if (allSetlists.length === 0) {
      // No results from search, return the original setlist
      res.status(200).json({
        setlists: [setlistData],
        multiArtistDetectionFailed: true
      });
      return;
    }

    // STEP 3: Return all setlists found, sorted by song count (headliners first)
    const setlistsWithCounts = allSetlists.map(s => {
      const songCount = (s.sets?.set || []).reduce((total, set) => {
        return total + (set.song || []).length;
      }, 0);
      return { ...s, _songCount: songCount };
    });

    // Sort by song count descending (headliners typically have more songs)
    setlistsWithCounts.sort((a, b) => b._songCount - a._songCount);

    res.status(200).json({
      setlists: setlistsWithCounts,
      venue: venueName,
      date: eventDate,
      totalArtists: setlistsWithCounts.length
    });

  } catch (error) {
    console.error('Error fetching setlist with multi-artist detection:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Firestore trigger to automatically import approved setlist submissions (uses onWrite to handle both creates and updates)
exports.processApprovedSetlist = functions.firestore
  .document('pending_setlist_submissions/{submissionId}')
  .onWrite(async (change, context) => {
    const newData = change.after.exists ? change.after.data() : null;
    const oldData = change.before.exists ? change.before.data() : null;

    // Skip if document was deleted
    if (!newData) {
      return null;
    }

    // Only process if:
    // 1. Status is 'approved' AND
    // 2. Either this is a new document OR status just changed to 'approved' AND
    // 3. Not already processed
    const isNewAndApproved = !oldData && newData.status === 'approved';
    const justApproved = oldData && newData.status === 'approved' && oldData.status !== 'approved';
    const alreadyProcessed = newData.processed === true;

    if ((!isNewAndApproved && !justApproved) || alreadyProcessed) {
      return null;
    }

    const submissionId = context.params.submissionId;
    const concertId = String(newData.concertId);  // Ensure it's a string
    const setlistData = newData.setlistData;

    console.log(`Processing approved submission ${submissionId} for concert ${concertId}`);

    try {
      const db = admin.firestore();

      // Parse setlist data and format for Firestore
      const songs = [];
      let position = 1;
      let hasEncore = false;

      if (setlistData.sets && setlistData.sets.set) {
        for (const set of setlistData.sets.set) {
          const setName = set.name || 'Main Set';
          const encore = set.encore || 0;

          if (encore > 0) {
            hasEncore = true;
          }

          if (set.song) {
            for (const song of set.song) {
              songs.push({
                position: position++,
                name: song.name,
                set_name: setName,
                encore: encore,
                is_cover: !!song.cover,
                cover_artist: song.cover ? song.cover.name : null,
                is_tape: !!song.tape,
                info: song.info || null
              });
            }
          }
        }
      }

      const songCount = songs.length;

      // Extract artist info from setlist data
      const artist = setlistData.artist || {};
      const artistName = artist.name || 'Unknown Artist';
      const artistMbid = artist.mbid || null;

      // Extract tour info (optional field)
      const tour = setlistData.tour || {};
      const tourName = tour.name || null;

      // Create slug from artist name for document ID
      const artistSlug = artistName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

      // Get all existing setlists for this concert
      const existingSetlists = await db.collection('setlists')
        .where('concert_id', '==', concertId)
        .get();

      // FIRST: Check if this specific artist already has a setlist (in any format)
      let existingArtistSetlist = null;
      for (const doc of existingSetlists.docs) {
        const data = doc.data();
        if (data.artist_name === artistName) {
          existingArtistSetlist = doc.id;
          console.log(`Found existing setlist for ${artistName} with ID: ${existingArtistSetlist}`);
          break;
        }
      }

      // Determine document ID:
      // - If this artist already has a setlist, use that ID (prevents duplicates)
      // - Otherwise, ALWAYS use artist-specific format for setlist.fm imports
      //   This prevents race conditions where concurrent submissions overwrite each other
      let docId;
      if (existingArtistSetlist) {
        docId = existingArtistSetlist;
      } else {
        // ALWAYS use artist-specific format: {concertId}-{artistSlug}
        // This prevents race conditions when multiple artists are imported concurrently
        // (Concert's artists array gets populated AS setlists are imported, so we can't
        // reliably check it to determine if more artists are coming)
        docId = `${concertId}-${artistSlug}`;

        console.log(`Using artist-specific docId for ${artistName}: ${docId}`);
      }

      // Check if this specific artist's setlist already exists
      const setlistRef = db.collection('setlists').doc(docId);
      const existingSetlist = await setlistRef.get();

      if (existingSetlist.exists) {
        console.log(`Updating existing setlist for ${artistName} at concert ${concertId}`);
      } else {
        console.log(`Creating new setlist for ${artistName} at concert ${concertId}`);
      }

      // Write setlist data with artist info
      await setlistRef.set({
        concert_id: concertId,
        artist_name: artistName,
        artist_id: artistMbid,
        tour_name: tourName,
        setlistfm_id: newData.setlistfmId || null,
        setlistfm_url: newData.setlistfmUrl || null,
        song_count: songCount,
        has_encore: hasEncore,
        songs: songs,
        created_at: admin.firestore.FieldValue.serverTimestamp(),
        fetched_at: admin.firestore.FieldValue.serverTimestamp()
      });

      // Update concert's artists array if this artist isn't already there
      const concertRef = db.collection('concerts').doc(concertId);
      const concertDoc = await concertRef.get();

      if (concertDoc.exists) {
        const concertData = concertDoc.data();
        const existingArtists = concertData.artists || [];

        // Helper function to parse combined artist names like "Artist A and Artist B"
        const parseArtistName = (name) => {
          // Split on common separators (order matters - try most specific first)
          const separators = [' and ', ' & ', ' with ', '/', ', ', ': '];
          for (const sep of separators) {
            if (name.includes(sep)) {
              return name.split(sep).map(n => n.trim()).filter(n => n.length > 0);
            }
          }
          return [name];
        };

        // Helper function to normalize artist names for fuzzy matching
        const normalizeArtistName = (name) => {
          return name
            .toLowerCase()
            .replace(/[^a-z0-9\s]/g, '') // Remove special chars
            .replace(/\s+/g, ' ')         // Normalize whitespace
            .trim()
            .replace(/^(the|a|an)\s+/i, ''); // Remove leading articles (The, A, An)
        };

        // Helper function: Calculate Levenshtein distance between two strings
        const levenshteinDistance = (str1, str2) => {
          const m = str1.length;
          const n = str2.length;
          const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

          for (let i = 0; i <= m; i++) dp[i][0] = i;
          for (let j = 0; j <= n; j++) dp[0][j] = j;

          for (let i = 1; i <= m; i++) {
            for (let j = 1; j <= n; j++) {
              if (str1[i - 1] === str2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1];
              } else {
                dp[i][j] = Math.min(
                  dp[i - 1][j] + 1,    // deletion
                  dp[i][j - 1] + 1,    // insertion
                  dp[i - 1][j - 1] + 1 // substitution
                );
              }
            }
          }

          return dp[m][n];
        };

        // Helper function to check if two artist names are similar/variants
        const areArtistNamesSimilar = (name1, name2) => {
          const norm1 = normalizeArtistName(name1);
          const norm2 = normalizeArtistName(name2);

          // Exact match after normalization
          if (norm1 === norm2) return true;

          // Check Levenshtein distance for close typos (like "Osbourne" vs "Osborne")
          // Allow up to 2 character differences for names longer than 8 characters
          // Allow 1 character difference for shorter names
          const maxDistance = norm1.length > 8 || norm2.length > 8 ? 2 : 1;
          const distance = levenshteinDistance(norm1, norm2);
          if (distance <= maxDistance) {
            console.log(`Fuzzy match: "${name1}" and "${name2}" (distance: ${distance})`);
            return true;
          }

          // One name contains the other (handles cases like "GLAF - Grahame Lesh & Friends" vs "Grahame Lesh & Friends")
          if (norm1.includes(norm2) || norm2.includes(norm1)) {
            // Make sure it's substantial (not just "the" or "and")
            const shorterLength = Math.min(norm1.length, norm2.length);
            if (shorterLength > 5) return true;
          }

          // Check if the words substantially overlap (for abbreviations/variations)
          const words1 = norm1.split(' ').filter(w => w.length > 2);
          const words2 = norm2.split(' ').filter(w => w.length > 2);

          // Count how many significant words match
          const matchingWords = words1.filter(w1 =>
            words2.some(w2 => w1.includes(w2) || w2.includes(w1))
          ).length;

          // If 75% or more of the shorter list's words match, consider them similar
          const minWords = Math.min(words1.length, words2.length);
          if (minWords > 0 && matchingWords / minWords >= 0.75) return true;

          return false;
        };

        // Strategy: setlist.fm is the source of truth for artist names
        // We need to handle three scenarios:
        // 1. Artist already exists with exact/similar name (keep it)
        // 2. Artist is part of a combined name that should be split (replace the combined entry)
        // 3. Artist doesn't exist at all (add it)

        // Check for exact match or MBID match
        const exactMatch = existingArtists.find(a =>
          a.artist_name === artistName ||
          (artistMbid && a.artist_id === artistMbid)
        );

        // Check if this artist name is a VARIANT of an existing single artist
        // (e.g., "GLAF - Grahame Lesh & Friends" is variant of "Grahame Lesh & Friends")
        // BUT we should NOT match if the existing artist is a COMBINED name that should be split
        const variantMatch = !exactMatch && existingArtists.find(a => {
          // Don't match if existing artist is a combined name (contains separators)
          const existingIsCombined = parseArtistName(a.artist_name).length > 1;
          if (existingIsCombined) return false;

          // Check if it's a variant using fuzzy matching
          return areArtistNamesSimilar(a.artist_name, artistName);
        });

        // Check if existing concert has a COMBINED artist name that contains this artist
        // (e.g., "Steve Miller Band with Dave Mason" contains "Steve Miller Band")
        // In this case, we should REPLACE the combined entry with separate artists
        const combinedArtistToReplace = existingArtists.find(a => {
          const parsedExisting = parseArtistName(a.artist_name);
          // Only consider if existing name is combined (has multiple parts)
          if (parsedExisting.length <= 1) return false;

          // Check if any of the parsed parts match our artist
          return parsedExisting.some(part =>
            normalizeArtistName(part) === normalizeArtistName(artistName)
          );
        });

        const artistExists = exactMatch || variantMatch;

        if (!artistExists) {
          console.log(`Adding ${artistName} to concert ${concertId}'s artists array`);

          // Determine role based on song count compared to other setlists for this concert
          // Get all setlists for this concert to compare song counts
          const allConcertSetlists = await db.collection('setlists')
            .where('concert_id', '==', concertId)
            .get();

          let role = 'headliner';  // Default to headliner

          // If there are other setlists with more songs, this is probably an opener
          for (const otherSetlist of allConcertSetlists.docs) {
            const otherData = otherSetlist.data();
            // Skip if this is the setlist we just created
            if (otherData.artist_name === artistName) continue;

            if (otherData.song_count && otherData.song_count > songCount) {
              role = 'opener';
              break;
            }
          }

          // Find or create artist in artists collection
          const artistsQuery = await db.collection('artists')
            .where('canonical_name', '==', artistName)
            .limit(1)
            .get();

          let artistId;
          if (!artistsQuery.empty) {
            artistId = artistsQuery.docs[0].id;
          } else {
            // Create new artist
            const newArtistRef = await db.collection('artists').add({
              canonical_name: artistName,
              created_at: admin.firestore.FieldValue.serverTimestamp()
            });
            artistId = newArtistRef.id;
            console.log(`Created new artist: ${artistName} with ID ${artistId}`);
          }

          // Add artist to concert's artists array
          const newArtist = {
            artist_id: artistId,
            artist_name: artistName,
            role: role,
            position: existingArtists.length + 1
          };

          // Determine setlist status based on whether setlist has songs
          const currentStatus = concertData.setlist_status || 'not_researched';
          let updateData = {
            artists: admin.firestore.FieldValue.arrayUnion(newArtist),
            updated_at: admin.firestore.FieldValue.serverTimestamp()
          };

          if (songCount > 0) {
            // Has actual setlist with songs
            updateData.has_setlist = true;
            updateData.setlist_status = 'has_setlist';
          } else if (currentStatus === 'not_researched') {
            // Found on setlist.fm but no setlist available
            updateData.setlist_status = 'verified_none_on_setlistfm';
            console.log(`Auto-updated status to 'verified_none_on_setlistfm' for concert ${concertId} (found on setlist.fm, no songs)`);
          }

          // Update tour name if available
          if (tourName) {
            updateData.tour_name = tourName;
            console.log(`Setting tour name: ${tourName}`);
          }

          await concertRef.update(updateData);

          console.log(`Added ${artistName} as ${role} to concert ${concertId}`);

          // Re-evaluate ALL artist roles based on final setlist song counts
          // This ensures roles are correct after multiple setlists are added
          const updatedConcert = await concertRef.get();
          let allArtists = updatedConcert.data().artists || [];

          // Get all setlists for this concert
          const allSetlistsForRoleUpdate = await db.collection('setlists')
            .where('concert_id', '==', concertId)
            .get();

          // Create a map of artist_name -> song_count
          const songCounts = {};
          allSetlistsForRoleUpdate.docs.forEach(doc => {
            const data = doc.data();
            songCounts[data.artist_name] = data.song_count || 0;
          });

          // Find the max song count
          const maxSongCount = Math.max(...Object.values(songCounts), 0);

          // Update roles: artist(s) with max song count = headliner, others = opener
          let rolesUpdated = false;
          allArtists = allArtists.map(artist => {
            const artistSongCount = songCounts[artist.artist_name] || 0;
            let correctRole;

            // If all setlists are empty (maxSongCount = 0), use position-based logic
            // First artist (position 1) = headliner, subsequent artists = opener
            if (maxSongCount === 0) {
              correctRole = artist.position === 1 ? 'headliner' : 'opener';
            } else {
              correctRole = artistSongCount === maxSongCount ? 'headliner' : 'opener';
            }

            if (artist.role !== correctRole) {
              console.log(`Updating ${artist.artist_name} role: ${artist.role} -> ${correctRole} (${artistSongCount} songs, position ${artist.position})`);
              rolesUpdated = true;
              return { ...artist, role: correctRole };
            }
            return artist;
          });

          // If roles were updated, save the changes
          if (rolesUpdated) {
            await concertRef.update({
              artists: allArtists,
              updated_at: admin.firestore.FieldValue.serverTimestamp()
            });
            console.log(`Updated artist roles for concert ${concertId}`);
          }

          // Detect malformed entries that look like "Artist A with Artist B and Artist C"
          const malformedArtists = allArtists.filter(a => {
            const name = a.artist_name || '';

            // Check if name contains multiple artist indicators
            const hasMultipleIndicators = (name.match(/ with | and | \+ | \/ /gi) || []).length >= 2;

            // Check if name can be parsed and all parsed names exist as separate artists
            const parsedNames = parseArtistName(name);
            const canBeSplit = parsedNames.length > 1 &&
              parsedNames.every(parsedName =>
                allArtists.some(otherArtist =>
                  otherArtist.artist_name === parsedName && otherArtist.artist_name !== name
                )
              );

            // Check if it contains separator and also contains one of the other artists
            const containsOtherArtist = allArtists.some(otherArtist =>
              otherArtist.artist_name !== name &&
              name.toLowerCase().includes(otherArtist.artist_name.toLowerCase())
            );
            const hasCombinedPattern = (name.includes(' with ') || name.includes(' and ') || name.includes('/') || name.includes(', ')) && containsOtherArtist;

            return hasMultipleIndicators || canBeSplit || hasCombinedPattern;
          });

          if (malformedArtists.length > 0) {
            console.log(`Cleaning up ${malformedArtists.length} malformed artist entries from concert ${concertId}`);
            malformedArtists.forEach(a => {
              console.log(`  Removing: "${a.artist_name}"`);
            });

            // Remove malformed entries
            const cleanedArtists = allArtists.filter(a => !malformedArtists.includes(a));

            // Fix positions to be sequential
            cleanedArtists.forEach((artist, index) => {
              artist.position = index + 1;
            });

            await concertRef.update({
              artists: cleanedArtists,
              updated_at: admin.firestore.FieldValue.serverTimestamp()
            });

            console.log(`Cleaned artists array for concert ${concertId}`);
          }
        } else {
          // Artist already exists (exact match or variant match)
          console.log(`Skipped adding "${artistName}" - already exists in concert (possibly as a variant)`);

          // Check if this is a variant match (not exact match) - if so, fix the artist name
          let updatedArtists = null;
          if (variantMatch && variantMatch.artist_name !== artistName) {
            console.log(`Updating artist name from "${variantMatch.artist_name}" to "${artistName}" (setlist.fm is source of truth)`);

            // Update the artist name in the artists array
            updatedArtists = existingArtists.map(artist => {
              if (artist.artist_name === variantMatch.artist_name) {
                return { ...artist, artist_name: artistName };
              }
              return artist;
            });
          }

          // Determine setlist status based on whether setlist has songs
          const currentStatus = concertData.setlist_status || 'not_researched';
          let updateData = {
            updated_at: admin.firestore.FieldValue.serverTimestamp()
          };

          // Update artists array if name was corrected
          if (updatedArtists) {
            updateData.artists = updatedArtists;
          }

          if (songCount > 0) {
            // Has actual setlist with songs
            updateData.has_setlist = true;
            updateData.setlist_status = 'has_setlist';
          } else if (currentStatus === 'not_researched') {
            // Found on setlist.fm but no setlist available
            updateData.setlist_status = 'verified_none_on_setlistfm';
            console.log(`Auto-updated status to 'verified_none_on_setlistfm' for concert ${concertId} (found on setlist.fm, no songs)`);
          }

          // Update tour name if available
          if (tourName) {
            updateData.tour_name = tourName;
            console.log(`Setting tour name: ${tourName}`);
          }

          await concertRef.update(updateData);
        }
      }

      // Mark submission as processed
      await change.after.ref.update({
        processed: true,
        processed_at: admin.firestore.FieldValue.serverTimestamp()
      });

      console.log(`Successfully imported setlist for concert ${concertId}`);
      return null;

    } catch (error) {
      console.error(`Error processing submission ${submissionId}:`, error);

      // Mark submission with error
      await change.after.ref.update({
        import_error: error.message,
        import_error_at: admin.firestore.FieldValue.serverTimestamp()
      });

      // Re-throw to trigger Cloud Functions retry
      throw error;
    }
  });

// Trigger GitHub Actions to export and deploy when a setlist is processed
exports.triggerDeploy = functions.firestore
  .document('pending_setlist_submissions/{submissionId}')
  .onUpdate(async (change, context) => {
    const newData = change.after.data();
    const oldData = change.before.data();

    // Only trigger if submission was just marked as processed
    if (!newData.processed || oldData.processed) {
      return null;
    }

    const submissionId = context.params.submissionId;
    console.log(`Triggering automatic deployment for submission ${submissionId}`);

    try {
      const githubOwner = 'Former-Stranger';
      const githubRepo = 'concert-website';

      // Get GitHub token from Firebase Functions config
      const githubToken = functions.config().github.token;

      if (!githubToken) {
        throw new Error('GitHub token not configured. Run: firebase functions:config:set github.token="YOUR_TOKEN"');
      }

      // Trigger GitHub Actions workflow via repository dispatch
      const response = await fetch(`https://api.github.com/repos/${githubOwner}/${githubRepo}/dispatches`, {
        method: 'POST',
        headers: {
          'Accept': 'application/vnd.github.v3+json',
          'Authorization': `token ${githubToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          event_type: 'deploy-setlist',
          client_payload: {
            submission_id: submissionId
          }
        })
      });

      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
      }

      console.log(`GitHub Actions workflow triggered for submission ${submissionId}`);
      console.log('Website will be automatically updated in a few minutes.');
      console.log(`View workflow runs: https://github.com/${githubOwner}/${githubRepo}/actions`);

      return null;

    } catch (error) {
      console.error(`Error triggering GitHub Actions: ${error.message}`);
      console.error('Full error:', error);

      // Fallback: Just log instructions
      console.log('AUTOMATIC DEPLOYMENT FAILED. Manual deployment required:');
      console.log('  ./deploy.sh');

      return null;
    }
  });

// Process new concert additions from the web form
exports.processNewConcert = functions.firestore
  .document('concerts/{concertId}')
  .onCreate(async (snap, context) => {
    const concertData = snap.data();
    const concertId = context.params.concertId;

    // Check if this is a form submission (has 'status' field)
    if (!concertData.status || concertData.status !== 'pending') {
      return null;
    }

    console.log(`Processing new concert from web form: ${concertId}`);

    try {
      const db = admin.firestore();

      // Helper function to find or create artist
      async function getOrCreateArtist(artistName) {
        // Search for existing artist (case-insensitive)
        const artistsQuery = await db.collection('artists')
          .where('canonical_name', '==', artistName)
          .limit(1)
          .get();

        if (!artistsQuery.empty) {
          const doc = artistsQuery.docs[0];
          return { id: doc.id, name: doc.data().canonical_name };
        }

        // Create new artist
        const newArtistRef = db.collection('artists').doc();
        await newArtistRef.set({
          canonical_name: artistName,
          created_at: admin.firestore.FieldValue.serverTimestamp()
        });

        console.log(`Created new artist: ${artistName} (${newArtistRef.id})`);
        return { id: newArtistRef.id, name: artistName };
      }

      // Helper function to find or create venue
      async function getOrCreateVenue(venueName, city, state) {
        // Search for existing venue
        const venuesQuery = await db.collection('venues')
          .where('canonical_name', '==', venueName)
          .where('city', '==', city)
          .where('state', '==', state)
          .limit(1)
          .get();

        if (!venuesQuery.empty) {
          const doc = venuesQuery.docs[0];
          return { id: doc.id, name: doc.data().canonical_name };
        }

        // Create new venue
        const newVenueRef = db.collection('venues').doc();
        await newVenueRef.set({
          canonical_name: venueName,
          city: city,
          state: state,
          created_at: admin.firestore.FieldValue.serverTimestamp()
        });

        console.log(`Created new venue: ${venueName} in ${city}, ${state} (${newVenueRef.id})`);
        return { id: newVenueRef.id, name: venueName };
      }

      // Get or create artist
      const headlinerArtist = await getOrCreateArtist(concertData.artist);
      const artists = [{
        artist_id: headlinerArtist.id,
        artist_name: headlinerArtist.name,
        role: 'headliner',
        position: 1
      }];

      // Add support act if provided
      if (concertData.support_act) {
        const supportArtist = await getOrCreateArtist(concertData.support_act);
        artists.push({
          artist_id: supportArtist.id,
          artist_name: supportArtist.name,
          role: 'opener',
          position: 2
        });
      }

      // Get or create venue
      const venue = await getOrCreateVenue(
        concertData.venue,
        concertData.city,
        concertData.state
      );

      // Get next concert ID (numeric) - find the highest numeric document ID
      const allConcerts = await db.collection('concerts').get();

      let maxId = 0;
      let maxShowNumber = 0;

      for (const doc of allConcerts.docs) {
        // Try to parse document ID as number
        const docIdNum = parseInt(doc.id);
        if (!isNaN(docIdNum) && docIdNum > maxId) {
          maxId = docIdNum;
        }

        // Also track max show number
        const showNum = doc.data().show_number || 0;
        if (showNum > maxShowNumber) {
          maxShowNumber = showNum;
        }
      }

      const nextConcertId = maxId + 1;
      const showNumber = maxShowNumber + 1;

      // Delete the auto-generated document
      await snap.ref.delete();

      // Create new document with numeric ID
      const newConcertRef = db.collection('concerts').doc(String(nextConcertId));
      await newConcertRef.set({
        show_number: showNumber,
        date: concertData.date,
        date_unknown: false,
        venue_id: venue.id,
        venue_name: venue.name,
        city: concertData.city,
        state: concertData.state,
        festival_name: concertData.festival_name || null,
        artists: artists,
        has_setlist: false,
        attended: true,
        created_at: admin.firestore.FieldValue.serverTimestamp(),
        updated_at: admin.firestore.FieldValue.serverTimestamp()
      });

      console.log(`Successfully processed concert ${nextConcertId} (Show #${showNumber})`);

      // Trigger deployment
      await triggerGitHubDeployment(nextConcertId, 'new-concert');

      return null;

    } catch (error) {
      console.error(`Error processing new concert ${concertId}:`, error);
      throw error;
    }
  });

// HTTP endpoint to manually trigger deployment (for delete operations, etc.)
exports.triggerManualDeploy = functions.https.onRequest(async (req, res) => {
  // Enable CORS
  res.set('Access-Control-Allow-Origin', '*');
  res.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.set('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight request
  if (req.method === 'OPTIONS') {
    res.status(204).send('');
    return;
  }

  console.log('Manual deployment triggered');

  try {
    await triggerGitHubDeployment('manual', 'manual-deploy');
    res.status(200).json({ success: true, message: 'Deployment triggered successfully' });
  } catch (error) {
    console.error('Error triggering deployment:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// Trigger deployment when a photo is uploaded
exports.onPhotoUpload = functions.firestore
  .document('concert_photos/{photoId}')
  .onCreate(async (snap, context) => {
    const photoData = snap.data();
    const photoId = context.params.photoId;
    const concertId = photoData.concert_id;

    console.log(`New photo uploaded: ${photoId} for concert ${concertId}`);
    console.log(`Triggering automatic deployment to update static site...`);

    try {
      await triggerGitHubDeployment(concertId, 'photo-upload');
      console.log('Deployment triggered successfully. Site will update in 2-3 minutes.');
      return null;
    } catch (error) {
      console.error(`Error triggering deployment for photo ${photoId}:`, error);
      console.log('AUTOMATIC DEPLOYMENT FAILED. Manual deployment required: ./deploy.sh');
      // Don't throw - we don't want photo upload to fail if deployment fails
      return null;
    }
  });

// Trigger deployment when a photo is deleted
exports.onPhotoDelete = functions.firestore
  .document('concert_photos/{photoId}')
  .onDelete(async (snap, context) => {
    const photoData = snap.data();
    const photoId = context.params.photoId;
    const concertId = photoData.concert_id;

    console.log(`Photo deleted: ${photoId} for concert ${concertId}`);
    console.log(`Triggering automatic deployment to update static site...`);

    try {
      await triggerGitHubDeployment(concertId, 'photo-delete');
      console.log('Deployment triggered successfully. Site will update in 2-3 minutes.');
      return null;
    } catch (error) {
      console.error(`Error triggering deployment for photo deletion ${photoId}:`, error);
      console.log('AUTOMATIC DEPLOYMENT FAILED. Manual deployment required: ./deploy.sh');
      // Don't throw - photo is already deleted
      return null;
    }
  });

// Send welcome email when a new user signs up
exports.sendWelcomeEmail = functions.auth.user().onCreate(async (user) => {
  const email = user.email;
  const displayName = user.displayName || 'Music Fan';

  console.log(`New user created: ${email} (${user.uid})`);

  if (!email) {
    console.log('User has no email address, skipping welcome email');
    return null;
  }

  try {
    const resendKey = functions.config().resend?.key;
    if (!resendKey) {
      console.error('Resend not configured');
      return null;
    }

    const { Resend } = require('resend');
    const resend = new Resend(resendKey);

    await resend.emails.send({
      from: 'Earplugs & Memories <noreply@earplugsandmemories.com>',
      to: email,
      subject: 'Welcome to Earplugs & Memories! 🎵',
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
          <h1 style="color: #d4773e; border-bottom: 3px solid #d4773e; padding-bottom: 10px;">
            Welcome to Earplugs & Memories!
          </h1>
          <p>Hi ${displayName},</p>
          <p>Thanks for joining our concert archive community! We're excited to have you here.</p>
          <h2 style="color: #2d1b1b; margin-top: 30px;">What You Can Do:</h2>
          <ul style="line-height: 1.8;">
            <li>📸 <strong>Upload Photos</strong> - Share your concert photos with the community</li>
            <li>🎼 <strong>Submit Setlists</strong> - Help complete the archive by submitting setlist.fm links</li>
            <li>💬 <strong>Add Comments</strong> - Share your memories and experiences</li>
            <li>📊 <strong>Explore Stats</strong> - Browse 35+ years of concert history</li>
          </ul>
          <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #d4773e; margin: 30px 0;">
            <p style="margin: 0;"><strong>Ready to explore?</strong></p>
            <p style="margin: 10px 0 0 0;">
              <a href="https://earplugsandmemories.com"
                 style="display: inline-block; background-color: #d4773e; color: white;
                        padding: 12px 25px; text-decoration: none; border-radius: 5px;
                        font-weight: bold; margin-top: 10px;">
                Visit Earplugs & Memories
              </a>
            </p>
          </div>
          <p style="color: #666; font-size: 14px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;">
            Questions or feedback? Feel free to reach out anytime.<br>
            <em>- The Earplugs & Memories Team</em>
          </p>
        </div>
      `,
      text: `Welcome to Earplugs & Memories!\n\nHi ${displayName},\n\nThanks for joining our concert archive community!\n\nWhat You Can Do:\n- Upload Photos\n- Submit Setlists\n- Add Comments\n- Explore Stats\n\nVisit us at: https://earplugsandmemories.com`
    });

    console.log(`Welcome email sent to ${email}`);
    return null;
  } catch (error) {
    console.error(`Error sending welcome email:`, error);
    return null;
  }
});

// Automatically promote pending admins when they sign up
exports.promotePendingAdmin = functions.auth.user().onCreate(async (user) => {
  const email = user.email;
  const uid = user.uid;

  if (!email) {
    console.log('User has no email address, skipping admin check');
    return null;
  }

  console.log(`Checking if new user is a pending admin: ${email} (${uid})`);

  try {
    const db = admin.firestore();

    // Check if this email is in the pending_admins collection
    const emailDocId = email.replace('@', '_at_').replace(/\./g, '_dot_');
    const pendingAdminRef = db.collection('pending_admins').doc(emailDocId);
    const pendingAdminDoc = await pendingAdminRef.get();

    if (!pendingAdminDoc.exists) {
      console.log('User is not a pending admin');
      return null;
    }

    // User is a pending admin! Promote them to active admin
    const pendingData = pendingAdminDoc.data();
    console.log(`Promoting pending admin: ${email}`);

    const adminData = {
      email: email,
      uid: uid,
      role: pendingData.role || 'owner',
      notes: pendingData.notes || '',
      added_at: pendingData.added_at,
      promoted_at: admin.firestore.FieldValue.serverTimestamp()
    };

    // Create admin document with UID as the document ID (required for security rules)
    await db.collection('admins').doc(uid).set(adminData);

    // Delete the pending admin document
    await pendingAdminRef.delete();

    console.log(`✅ Successfully promoted ${email} to admin with UID ${uid}`);
    return null;
  } catch (error) {
    console.error(`Error promoting pending admin:`, error);
    return null;
  }
});

// Notify when someone uploads a photo
exports.notifyPhotoUpload = functions.firestore
  .document('concert_photos/{photoId}')
  .onCreate(async (snap, context) => {
    const photoData = snap.data();
    const photoId = context.params.photoId;

    console.log(`New photo uploaded: ${photoId} by ${photoData.user_name}`);

    try {
      const resendKey = functions.config().resend?.key;
      const notifyEmail = functions.config().notify?.email;

      if (!resendKey || !notifyEmail) {
        console.error('Resend or notification email not configured');
        return null;
      }

      const { Resend } = require('resend');
      const resend = new Resend(resendKey);

      // Get concert details
      const db = admin.firestore();
      const concertRef = db.collection('concerts').doc(photoData.concert_id);
      const concertSnap = await concertRef.get();
      const concertData = concertSnap.data();

      const concertTitle = concertData
        ? `${concertData.artists?.[0]?.artist_name || 'Concert'} - ${concertData.date}`
        : `Concert #${photoData.concert_id}`;

      await resend.emails.send({
        from: 'Earplugs & Memories <noreply@earplugsandmemories.com>',
        to: notifyEmail,
        subject: `📸 New Photo: ${concertTitle}`,
        html: `
          <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #d4773e;">📸 New Photo Uploaded!</h2>
            <p><strong>${photoData.user_name}</strong> just uploaded a photo.</p>
            <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-left: 4px solid #d4773e;">
              <p style="margin: 0;"><strong>Concert:</strong> ${concertTitle}</p>
              ${photoData.caption ? `<p style="margin: 10px 0 0 0;"><strong>Caption:</strong> ${photoData.caption}</p>` : ''}
            </div>
            <p>
              <a href="https://earplugsandmemories.com/concert.html?id=${photoData.concert_id}"
                 style="display: inline-block; background-color: #d4773e; color: white;
                        padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                View Photo
              </a>
            </p>
          </div>
        `,
        text: `New Photo Uploaded!\n\n${photoData.user_name} uploaded a photo to ${concertTitle}.\n${photoData.caption ? `\nCaption: ${photoData.caption}` : ''}\n\nView at: https://earplugsandmemories.com/concert.html?id=${photoData.concert_id}`
      });

      console.log(`Photo notification sent to ${notifyEmail}`);
      return null;
    } catch (error) {
      console.error(`Error sending photo notification:`, error);
      return null;
    }
  });

// Notify when someone adds a comment
exports.notifyComment = functions.firestore
  .document('concert_comments/{commentId}')
  .onCreate(async (snap, context) => {
    const commentData = snap.data();
    const commentId = context.params.commentId;

    console.log(`New comment by ${commentData.user_name}`);

    try {
      const resendKey = functions.config().resend?.key;
      const notifyEmail = functions.config().notify?.email;

      if (!resendKey || !notifyEmail) {
        console.error('Resend or notification email not configured');
        return null;
      }

      const { Resend } = require('resend');
      const resend = new Resend(resendKey);

      // Get concert details
      const db = admin.firestore();
      const concertRef = db.collection('concerts').doc(commentData.concert_id);
      const concertSnap = await concertRef.get();
      const concertData = concertSnap.data();

      const concertTitle = concertData
        ? `${concertData.artists?.[0]?.artist_name || 'Concert'} - ${concertData.date}`
        : `Concert #${commentData.concert_id}`;

      await resend.emails.send({
        from: 'Earplugs & Memories <noreply@earplugsandmemories.com>',
        to: notifyEmail,
        subject: `💬 New Comment: ${concertTitle}`,
        html: `
          <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #d4773e;">💬 New Comment Posted!</h2>
            <p><strong>${commentData.user_name}</strong> commented on ${concertTitle}.</p>
            <div style="background-color: #f5f5f5; padding: 15px; margin: 20px 0; border-left: 4px solid #d4773e;">
              <p style="margin: 0; font-style: italic;">"${commentData.comment}"</p>
            </div>
            <p>
              <a href="https://earplugsandmemories.com/concert.html?id=${commentData.concert_id}"
                 style="display: inline-block; background-color: #d4773e; color: white;
                        padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                View Comment
              </a>
            </p>
          </div>
        `,
        text: `New Comment Posted!\n\n${commentData.user_name} commented on ${concertTitle}:\n\n"${commentData.comment}"\n\nView at: https://earplugsandmemories.com/concert.html?id=${commentData.concert_id}`
      });

      console.log(`Comment notification sent to ${notifyEmail}`);
      return null;
    } catch (error) {
      console.error(`Error sending comment notification:`, error);
      return null;
    }
  });

// Helper function to trigger GitHub Actions deployment
async function triggerGitHubDeployment(entityId, eventType) {
  try {
    const githubOwner = 'Former-Stranger';
    const githubRepo = 'concert-website';

    // Get GitHub token from Firebase Functions config
    const githubToken = functions.config().github?.token;

    if (!githubToken) {
      console.error('GitHub token not configured. Run: firebase functions:config:set github.token="YOUR_TOKEN"');
      return;
    }

    // Trigger GitHub Actions workflow via repository dispatch
    const response = await fetch(`https://api.github.com/repos/${githubOwner}/${githubRepo}/dispatches`, {
      method: 'POST',
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': `token ${githubToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        event_type: eventType,
        client_payload: {
          entity_id: entityId
        }
      })
    });

    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
    }

    console.log(`GitHub Actions workflow triggered for ${eventType}: ${entityId}`);
    console.log('Website will be automatically updated in a few minutes.');
    console.log(`View workflow runs: https://github.com/${githubOwner}/${githubRepo}/actions`);

  } catch (error) {
    console.error(`Error triggering GitHub Actions: ${error.message}`);
    console.log('AUTOMATIC DEPLOYMENT FAILED. Manual deployment required: ./deploy.sh');
    throw error;
  }
}
