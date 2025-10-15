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

      // Check if setlist already exists for this concert
      const existingSetlistsQuery = await db.collection('setlists')
        .where('concert_id', '==', concertId)
        .limit(1)
        .get();

      let setlistRef;
      if (!existingSetlistsQuery.empty) {
        // Update existing setlist
        setlistRef = existingSetlistsQuery.docs[0].ref;
        console.log(`Updating existing setlist for concert ${concertId}`);
      } else {
        // Create new setlist
        setlistRef = db.collection('setlists').doc();
        console.log(`Creating new setlist for concert ${concertId}`);
      }

      // Write setlist data
      await setlistRef.set({
        concert_id: concertId,
        setlistfm_id: newData.setlistfmId || null,
        setlistfm_url: newData.setlistfmUrl || null,
        song_count: songCount,
        has_encore: hasEncore,
        songs: songs,
        created_at: admin.firestore.FieldValue.serverTimestamp(),
        fetched_at: admin.firestore.FieldValue.serverTimestamp()
      });

      // Update concert to mark that it has a setlist
      const concertRef = db.collection('concerts').doc(concertId);
      await concertRef.update({
        has_setlist: true,
        updated_at: admin.firestore.FieldValue.serverTimestamp()
      });

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
