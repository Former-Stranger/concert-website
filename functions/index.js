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
