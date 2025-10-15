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

// Firestore trigger to automatically import approved setlist submissions
exports.processApprovedSetlist = functions.firestore
  .document('pending_setlist_submissions/{submissionId}')
  .onUpdate(async (change, context) => {
    const newData = change.after.data();
    const oldData = change.before.data();

    // Only process if status changed to 'approved'
    if (newData.status !== 'approved' || oldData.status === 'approved') {
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

      // Get GitHub token from environment (will be set as a Cloud Function environment variable)
      const githubToken = process.env.GITHUB_TOKEN;

      if (!githubToken) {
        throw new Error('GITHUB_TOKEN environment variable not set');
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
