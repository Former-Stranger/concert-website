import { db, auth, onAuthStateChanged } from './firebase-config.js';
import { collection, addDoc, query, where, getDocs, doc, getDoc } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js';
import { isOwner } from './auth.js';

// Helper function to check if current user is admin (async version)
async function checkIsAdmin() {
    // Wait for auth to initialize if needed
    return new Promise((resolve) => {
        const checkUser = async () => {
            const user = auth.currentUser;
            if (!user) {
                resolve(false);
                return;
            }

            try {
                const adminDoc = await getDoc(doc(db, 'admins', user.uid));
                resolve(adminDoc.exists());
            } catch (error) {
                console.error('Error checking admin status:', error);
                resolve(false);
            }
        };

        // If auth is ready, check immediately
        if (auth.currentUser !== undefined) {
            checkUser();
        } else {
            // Wait for auth state to initialize
            const unsubscribe = onAuthStateChanged(auth, () => {
                unsubscribe();
                checkUser();
            });
        }
    });
}

export async function initSetlistSubmission() {
    const submitBtn = document.getElementById('submit-setlist-btn');
    const urlInput = document.getElementById('setlistfm-url');
    const messageDiv = document.getElementById('submit-setlist-message');

    if (!submitBtn || !urlInput) return;

    submitBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();

        if (!url) {
            showMessage(messageDiv, 'Please enter a setlist.fm URL', 'error');
            return;
        }

        // Extract setlist ID from URL
        const setlistId = extractSetlistId(url);
        if (!setlistId) {
            showMessage(messageDiv, 'Invalid setlist.fm URL format', 'error');
            return;
        }

        // Get current concert ID
        const urlParams = new URLSearchParams(window.location.search);
        const concertId = urlParams.get('id');

        if (!concertId) {
            showMessage(messageDiv, 'Concert ID not found', 'error');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Submitting...';

        try {
            console.log('[Setlist Submission] Concert ID:', concertId);
            console.log('[Setlist Submission] URL:', url);
            console.log('[Setlist Submission] Setlist ID:', setlistId);

            // Check if already submitted
            const existingSubmission = await checkExistingSubmission(concertId);
            if (existingSubmission) {
                showMessage(messageDiv, 'A setlist has already been submitted for this concert and is pending review', 'info');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i>Submit';
                return;
            }

            // Fetch setlist data to validate the URL (includes multi-artist detection)
            console.log('[Setlist Submission] Fetching setlist data from Cloud Function...');
            const setlistResponse = await fetchSetlistData(setlistId);
            console.log('[Setlist Submission] Setlist data received:', setlistResponse);

            if (!setlistResponse || !setlistResponse.setlists || setlistResponse.setlists.length === 0) {
                showMessage(messageDiv, 'Could not find setlist on setlist.fm. Please check the URL', 'error');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i>Submit';
                return;
            }

            // If multiple artists detected, show selection UI
            if (setlistResponse.totalArtists > 1) {
                // Don't use showMessage here because it has a 5-second timeout
                // Instead, the multi-artist selection UI will handle its own messages
                showMultiArtistSelection(setlistResponse, concertId);
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i>Submit';
                return;
            }

            // Single artist - proceed with submission
            const setlistData = setlistResponse.setlists[0];

            // Get user info
            const user = auth.currentUser;
            const submitterEmail = user ? user.email : 'anonymous';
            const submitterName = user ? user.displayName || 'Anonymous' : 'Anonymous';

            // Check if user is owner (auto-approve owner submissions)
            console.log('[Setlist Submission] Current user:', user ? user.uid : 'NOT AUTHENTICATED');

            const userIsOwner = await checkIsAdmin();
            const status = userIsOwner ? 'approved' : 'pending';

            console.log('[Setlist Submission] User is owner:', userIsOwner);
            console.log('[Setlist Submission] Status:', status);

            // Store in Firestore with the fetched setlist data
            const submissionData = {
                concertId: parseInt(concertId),
                setlistfmUrl: url,
                setlistfmId: setlistId,
                submittedBy: user ? user.uid : null,  // Add user UID
                submittedByEmail: submitterEmail,
                submittedByName: submitterName,
                submittedAt: new Date(),
                status: status,
                setlistData: setlistData
            };

            console.log('[Setlist Submission] Saving to Firestore:', submissionData);
            await addDoc(collection(db, 'pending_setlist_submissions'), submissionData);

            const message = userIsOwner
                ? 'Setlist submitted and automatically approved! The website will update in a few minutes.'
                : 'Thank you! Your submission has been received and will be reviewed by an admin';
            showMessage(messageDiv, message, 'success');
            urlInput.value = '';

            // Hide the submission form after successful submission
            setTimeout(() => {
                document.getElementById('submit-setlist-section').classList.add('hidden');
            }, 3000);

        } catch (error) {
            console.error('Error submitting setlist:', error);
            showMessage(messageDiv, 'Error submitting setlist. Please try again', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i>Submit';
        }
    });
}

function extractSetlistId(url) {
    // URL format: https://www.setlist.fm/setlist/artist/year/venue-city-state-ID.html
    const match = url.match(/-([a-zA-Z0-9]+)\.html$/);
    return match ? match[1] : null;
}

async function fetchSetlistData(setlistId) {
    try {
        // Use Cloud Function with multi-artist detection
        const response = await fetch(`https://us-central1-earplugs-and-memories.cloudfunctions.net/fetchSetlistWithMultiArtist?id=${setlistId}`);

        if (response.ok) {
            const data = await response.json();
            // If multi-artist detection worked, return all setlists
            // Otherwise, return single setlist in same format
            if (data.setlists && Array.isArray(data.setlists)) {
                return {
                    setlists: data.setlists,
                    venue: data.venue,
                    date: data.date,
                    totalArtists: data.totalArtists || data.setlists.length
                };
            }
            // Fallback for single setlist
            return { setlists: [data], totalArtists: 1 };
        }
        return null;
    } catch (error) {
        console.error('Error fetching setlist:', error);
        return null;
    }
}

async function checkExistingSubmission(concertId) {
    const q = query(
        collection(db, 'pending_setlist_submissions'),
        where('concertId', '==', concertId),
        where('status', '==', 'pending')
    );

    const querySnapshot = await getDocs(q);
    return !querySnapshot.empty;
}

function showMessage(element, message, type) {
    const colors = {
        success: 'text-green-700 bg-green-100 border-green-300',
        error: 'text-red-700 bg-red-100 border-red-300',
        info: 'text-blue-700 bg-blue-100 border-blue-300'
    };

    element.className = `mt-3 text-center p-3 rounded border-2 ${colors[type] || colors.info}`;
    element.textContent = message;

    // Clear message after 5 seconds
    setTimeout(() => {
        element.className = 'mt-3 text-center';
        element.textContent = '';
    }, 5000);
}

export function showSubmitSetlistSection() {
    const section = document.getElementById('submit-setlist-section');
    if (section) {
        section.classList.remove('hidden');
    }
}

function showMultiArtistSelection(setlistResponse, concertId) {
    const { setlists, venue, date } = setlistResponse;

    // Create selection UI
    const messageDiv = document.getElementById('submit-setlist-message');
    const urlInput = document.getElementById('setlistfm-url');

    // Hide the URL input
    urlInput.parentElement.style.display = 'none';

    // Create artist selection interface
    const selectionHTML = `
        <div id="multi-artist-selection" class="mb-4 p-4 bg-white rounded border-2 border-[#d4773e]">
            <h3 class="text-lg font-bold text-[#2d1b1b] mb-3">
                <i class="fas fa-users mr-2"></i>Select Artists to Submit
            </h3>
            <p class="text-sm text-[#2d1b1b] mb-3">
                ${venue} on ${date} - ${setlists.length} artist${setlists.length > 1 ? 's' : ''} found
            </p>
            <div class="space-y-2">
                ${setlists.map((setlist, idx) => {
                    const artist = setlist.artist || {};
                    const artistName = artist.name || 'Unknown Artist';
                    const songCount = setlist._songCount || 0;
                    return `
                        <label class="flex items-center p-3 border border-[#d4773e] rounded cursor-pointer hover:bg-[#f4e4c1]">
                            <input type="checkbox"
                                   class="artist-checkbox mr-3"
                                   data-index="${idx}"
                                   ${idx === 0 ? 'checked' : ''}>
                            <div class="flex-1">
                                <div class="font-bold text-[#2d1b1b]">${artistName}</div>
                                <div class="text-sm text-gray-600">${songCount} song${songCount !== 1 ? 's' : ''}</div>
                            </div>
                        </label>
                    `;
                }).join('')}
            </div>
            <div class="mt-4 flex gap-2">
                <button id="submit-selected-btn" class="bg-[#c1502e] text-[#f4e4c1] px-6 py-2 rounded font-bold hover:bg-[#d4773e] transition">
                    <i class="fas fa-paper-plane mr-2"></i>Submit Selected
                </button>
                <button id="cancel-selection-btn" class="bg-gray-400 text-white px-6 py-2 rounded font-bold hover:bg-gray-500 transition">
                    <i class="fas fa-times mr-2"></i>Cancel
                </button>
            </div>
        </div>
    `;

    messageDiv.innerHTML = selectionHTML;

    // Handle submit selected
    document.getElementById('submit-selected-btn').addEventListener('click', async () => {
        const checkboxes = document.querySelectorAll('.artist-checkbox:checked');
        const selectedIndices = Array.from(checkboxes).map(cb => parseInt(cb.dataset.index));

        if (selectedIndices.length === 0) {
            showMessage(messageDiv, 'Please select at least one artist', 'error');
            return;
        }

        const submitBtn = document.getElementById('submit-selected-btn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Submitting...';

        try {
            // Get user info
            const user = auth.currentUser;
            const submitterEmail = user ? user.email : 'anonymous';
            const submitterName = user ? user.displayName || 'Anonymous' : 'Anonymous';

            // Check if user is owner (auto-approve owner submissions)
            console.log('[Multi-Artist Submit] Current user:', user ? user.uid : 'NOT AUTHENTICATED');

            const userIsOwner = await checkIsAdmin();
            const status = userIsOwner ? 'approved' : 'pending';

            console.log('[Multi-Artist Submit] User is owner:', userIsOwner);
            console.log('[Multi-Artist Submit] Submission status:', status);

            // Submit each selected artist's setlist
            const submissions = [];
            for (const idx of selectedIndices) {
                const setlistData = setlists[idx];
                const submissionData = {
                    concertId: parseInt(concertId),
                    setlistfmUrl: setlistData.url || '',
                    setlistfmId: setlistData.id || '',
                    submittedBy: user ? user.uid : null,  // Add user UID
                    submittedByEmail: submitterEmail,
                    submittedByName: submitterName,
                    submittedAt: new Date(),
                    status: status,
                    setlistData: setlistData
                };

                submissions.push(addDoc(collection(db, 'pending_setlist_submissions'), submissionData));
            }

            await Promise.all(submissions);

            const message = userIsOwner
                ? `${selectedIndices.length} setlist${selectedIndices.length > 1 ? 's' : ''} submitted and automatically approved! The website will update in a few minutes.`
                : `Thank you! ${selectedIndices.length} setlist${selectedIndices.length > 1 ? 's' : ''} submitted and will be reviewed by an admin`;
            showMessage(messageDiv, message, 'success');

            // Clear the selection UI
            setTimeout(() => {
                document.getElementById('multi-artist-selection').remove();
                urlInput.parentElement.style.display = '';
                urlInput.value = '';

                // Hide the submission form after successful submission
                setTimeout(() => {
                    document.getElementById('submit-setlist-section').classList.add('hidden');
                }, 2000);
            }, 2000);

        } catch (error) {
            console.error('Error submitting setlists:', error);
            showMessage(messageDiv, 'Error submitting setlists. Please try again', 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i>Submit Selected';
        }
    });

    // Handle cancel
    document.getElementById('cancel-selection-btn').addEventListener('click', () => {
        document.getElementById('multi-artist-selection').remove();
        urlInput.parentElement.style.display = '';
        urlInput.value = '';
        messageDiv.innerHTML = '';
    });
}

export async function initUpdateSetlist() {
    // Wait for button to exist (it's created asynchronously by concert.js)
    const waitForButton = () => {
        return new Promise((resolve) => {
            const checkButton = () => {
                const btn = document.getElementById('update-setlist-btn');
                if (btn) {
                    resolve(btn);
                } else {
                    setTimeout(checkButton, 100);
                }
            };
            checkButton();
        });
    };

    const updateBtn = await waitForButton();
    const submitBtn = document.getElementById('update-setlist-submit-btn');
    const cancelBtn = document.getElementById('cancel-update-btn');
    const urlInput = document.getElementById('update-setlistfm-url');
    const messageDiv = document.getElementById('update-setlist-message');
    const updateSection = document.getElementById('update-setlist-section');

    if (!updateBtn) return;

    // Show update form when clicking update button
    updateBtn.addEventListener('click', () => {
        updateSection.classList.remove('hidden');
        updateBtn.classList.add('hidden');
        // Scroll to the update section
        updateSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });

    // Cancel update
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            updateSection.classList.add('hidden');
            updateBtn.classList.remove('hidden');
            urlInput.value = '';
            messageDiv.textContent = '';
            messageDiv.className = 'mt-3 text-center';
        });
    }

    // Handle update submission
    if (submitBtn) {
        submitBtn.addEventListener('click', async () => {
            const url = urlInput.value.trim();

            if (!url) {
                showMessage(messageDiv, 'Please enter a setlist.fm URL', 'error');
                return;
            }

            // Extract setlist ID from URL
            const setlistId = extractSetlistId(url);
            if (!setlistId) {
                showMessage(messageDiv, 'Invalid setlist.fm URL format', 'error');
                return;
            }

            // Get current concert ID
            const urlParams = new URLSearchParams(window.location.search);
            const concertId = urlParams.get('id');

            if (!concertId) {
                showMessage(messageDiv, 'Concert ID not found', 'error');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Updating...';

            try {
                console.log('[Update Setlist] Concert ID:', concertId);
                console.log('[Update Setlist] URL:', url);
                console.log('[Update Setlist] Setlist ID:', setlistId);

                // Fetch setlist data to validate the URL
                console.log('[Update Setlist] Fetching setlist data from Cloud Function...');
                const setlistData = await fetchSetlistData(setlistId);
                console.log('[Update Setlist] Setlist data received:', setlistData);

                if (!setlistData) {
                    showMessage(messageDiv, 'Could not find setlist on setlist.fm. Please check the URL', 'error');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-sync mr-2"></i>Update';
                    return;
                }

                // Get user info
                const user = auth.currentUser;
                const submitterEmail = user ? user.email : 'anonymous';
                const submitterName = user ? user.displayName || 'Anonymous' : 'Anonymous';

                // Check if user is owner (auto-approve owner submissions)
                console.log('[Update Setlist] Current user:', user ? user.uid : 'NOT AUTHENTICATED');

                const userIsOwner = await checkIsAdmin();
                const status = userIsOwner ? 'approved' : 'pending';

                console.log('[Update Setlist] User is owner:', userIsOwner);
                console.log('[Update Setlist] Status:', status);

                // Store in Firestore with the fetched setlist data
                // This will trigger the Cloud Function to update the existing setlist
                const submissionData = {
                    concertId: parseInt(concertId),
                    setlistfmUrl: url,
                    setlistfmId: setlistId,
                    submittedBy: user ? user.uid : null,  // Add user UID
                    submittedByEmail: submitterEmail,
                    submittedByName: submitterName,
                    submittedAt: new Date(),
                    status: status,
                    setlistData: setlistData,
                    isUpdate: true // Flag to indicate this is an update
                };

                console.log('[Update Setlist] Saving to Firestore:', submissionData);
                await addDoc(collection(db, 'pending_setlist_submissions'), submissionData);

                const message = userIsOwner
                    ? 'Setlist updated! The website will refresh with the new data in a few minutes. Please reload the page.'
                    : 'Update submitted and will be reviewed by an admin';
                showMessage(messageDiv, message, 'success');
                urlInput.value = '';

                // Hide the update form after successful submission
                setTimeout(() => {
                    updateSection.classList.add('hidden');
                    if (userIsOwner) {
                        // Reload the page after a short delay for owner submissions
                        setTimeout(() => {
                            window.location.reload();
                        }, 3000);
                    }
                }, 2000);

            } catch (error) {
                console.error('Error updating setlist:', error);
                showMessage(messageDiv, 'Error updating setlist. Please try again', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-sync mr-2"></i>Update';
            }
        });
    }
}
