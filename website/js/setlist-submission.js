import { db, auth } from './firebase-config.js';
import { collection, addDoc, query, where, getDocs } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js';
import { isOwner } from './auth.js';

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

            // Fetch setlist data to validate the URL
            console.log('[Setlist Submission] Fetching setlist data from Cloud Function...');
            const setlistData = await fetchSetlistData(setlistId);
            console.log('[Setlist Submission] Setlist data received:', setlistData);

            if (!setlistData) {
                showMessage(messageDiv, 'Could not find setlist on setlist.fm. Please check the URL', 'error');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i>Submit';
                return;
            }

            // Get user info
            const user = auth.currentUser;
            const submitterEmail = user ? user.email : 'anonymous';
            const submitterName = user ? user.displayName || 'Anonymous' : 'Anonymous';

            // Check if user is owner (auto-approve owner submissions)
            const userIsOwner = isOwner();
            const status = userIsOwner ? 'approved' : 'pending';

            console.log('[Setlist Submission] User is owner:', userIsOwner);
            console.log('[Setlist Submission] Status:', status);

            // Store in Firestore with the fetched setlist data
            const submissionData = {
                concertId: parseInt(concertId),
                setlistfmUrl: url,
                setlistfmId: setlistId,
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
        // Use Cloud Function to avoid CORS issues
        const response = await fetch(`https://us-central1-earplugs-and-memories.cloudfunctions.net/fetchSetlist?id=${setlistId}`);

        if (response.ok) {
            return await response.json();
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

export async function initUpdateSetlist() {
    const updateBtn = document.getElementById('update-setlist-btn');
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
                const userIsOwner = isOwner();
                const status = userIsOwner ? 'approved' : 'pending';

                console.log('[Update Setlist] User is owner:', userIsOwner);
                console.log('[Update Setlist] Status:', status);

                // Store in Firestore with the fetched setlist data
                // This will trigger the Cloud Function to update the existing setlist
                const submissionData = {
                    concertId: parseInt(concertId),
                    setlistfmUrl: url,
                    setlistfmId: setlistId,
                    submittedByEmail: submitterEmail,
                    submittedByName: submitterName,
                    submittedAt: new Date(),
                    status: status,
                    setlistData: setlistData,
                    isUpdate: true // Flag to indicate this is an update
                };

                console.log('[Update Setlist] Saving to Firestore:', submissionData);
                await addDoc(collection(db, 'setlist_submissions'), submissionData);

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
