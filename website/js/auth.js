// Authentication module
import { auth, googleProvider, facebookProvider, signInWithPopup, signOut, onAuthStateChanged } from './firebase-config.js';
import { db } from './firebase-config.js';
import { collection, query, where, onSnapshot } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js';

// Current user state
let currentUser = null;
let pendingSetlistsCount = 0;
let unsubscribePendingCount = null;

// Owner UID - set to the owner's Firebase Auth UID
const OWNER_UID = 'jBa71VgYp0Qz782bawa4SgjHu1l1';

// Initialize auth state listener
function initAuth() {
    onAuthStateChanged(auth, (user) => {
        currentUser = user;
        updateAuthUI();

        // Subscribe to pending setlists count if user is owner
        if (user && isOwner()) {
            subscribeToPendingCount();
        } else {
            // Unsubscribe if not owner
            if (unsubscribePendingCount) {
                unsubscribePendingCount();
                unsubscribePendingCount = null;
            }
            pendingSetlistsCount = 0;
        }
    });
}

// Subscribe to pending setlists count
function subscribeToPendingCount() {
    // Unsubscribe from previous listener if any
    if (unsubscribePendingCount) {
        unsubscribePendingCount();
    }

    const q = query(
        collection(db, 'pending_setlist_submissions'),
        where('status', '==', 'pending')
    );

    unsubscribePendingCount = onSnapshot(q, (snapshot) => {
        pendingSetlistsCount = snapshot.size;
        updateAuthUI();
    }, (error) => {
        console.error('Error listening to pending setlists:', error);
    });
}

// Sign in with Google
async function signInWithGoogle() {
    try {
        const result = await signInWithPopup(auth, googleProvider);
        console.log('Signed in with Google:', result.user.displayName);
        return result.user;
    } catch (error) {
        console.error('Error signing in with Google:', error);
        alert('Failed to sign in with Google. Please try again.');
        return null;
    }
}

// Sign in with Facebook
async function signInWithFacebook() {
    try {
        const result = await signInWithPopup(auth, facebookProvider);
        console.log('Signed in with Facebook:', result.user.displayName);
        return result.user;
    } catch (error) {
        console.error('Error signing in with Facebook:', error);
        alert('Failed to sign in with Facebook. Please try again.');
        return null;
    }
}


// Sign out
async function signOutUser() {
    try {
        await signOut(auth);
        console.log('Signed out');
    } catch (error) {
        console.error('Error signing out:', error);
    }
}

// Update UI based on auth state
function updateAuthUI() {
    const authButton = document.getElementById('auth-button');
    const userInfo = document.getElementById('user-info');
    const addConcertNav = document.getElementById('add-concert-nav');
    const adminSetlistsNav = document.getElementById('admin-setlists-nav');

    if (!authButton) return;  // Not on a page with auth UI

    if (currentUser) {
        // User is signed in
        authButton.innerHTML = `
            <i class="fas fa-sign-out-alt mr-2"></i>Sign Out
        `;
        authButton.onclick = signOutUser;

        if (userInfo) {
            userInfo.innerHTML = `
                <div class="flex items-center space-x-3">
                    <img src="${currentUser.photoURL}" alt="${currentUser.displayName}" class="w-8 h-8 rounded-full">
                    <span>${currentUser.displayName}</span>
                </div>
            `;
            userInfo.classList.remove('hidden');
        }

        // Show "Add Concert" and "Pending Setlists" links only for owner
        if (addConcertNav && isOwner()) {
            addConcertNav.classList.remove('hidden');
        }
        if (adminSetlistsNav && isOwner()) {
            adminSetlistsNav.classList.remove('hidden');

            // Update the text with pending count
            if (pendingSetlistsCount > 0) {
                adminSetlistsNav.innerHTML = `Pending Setlists <span style="background: #f87171; color: white; padding: 0.25rem 0.5rem; border-radius: 9999px; font-size: 0.75rem; font-weight: bold; margin-left: 0.5rem;">${pendingSetlistsCount}</span>`;
            } else {
                adminSetlistsNav.textContent = 'Pending Setlists';
            }
        }
    } else {
        // User is signed out
        authButton.innerHTML = `
            <i class="fas fa-sign-in-alt mr-2"></i>Sign In
        `;
        authButton.onclick = showSignInModal;

        if (userInfo) {
            userInfo.classList.add('hidden');
        }

        if (addConcertNav) {
            addConcertNav.classList.add('hidden');
        }
        if (adminSetlistsNav) {
            adminSetlistsNav.classList.add('hidden');
        }
    }
}

// Show sign-in modal with multiple provider options
function showSignInModal() {
    // Create modal backdrop
    const modal = document.createElement('div');
    modal.id = 'sign-in-modal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
    modal.onclick = (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    };

    modal.innerHTML = `
        <div class="bg-white rounded-lg p-8 max-w-md w-full shadow-2xl" onclick="event.stopPropagation()">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-2xl font-bold text-[#2d1b1b]">Sign In</h2>
                <button onclick="document.getElementById('sign-in-modal').remove()"
                        class="text-gray-500 hover:text-gray-700 text-2xl">
                    <i class="fas fa-times"></i>
                </button>
            </div>

            <p class="text-gray-600 mb-6">Choose a sign-in method to continue</p>

            <div class="space-y-3">
                <!-- Google Sign In -->
                <button id="google-sign-in-btn"
                        class="w-full flex items-center justify-center gap-3 bg-white border-2 border-gray-300 hover:border-gray-400 text-gray-700 font-semibold py-3 px-4 rounded-lg transition">
                    <svg width="20" height="20" viewBox="0 0 20 20">
                        <path fill="#4285F4" d="M19.6 10.23c0-.82-.1-1.42-.25-2.05H10v3.72h5.5c-.15.96-.74 2.31-2.04 3.22v2.45h3.16c1.89-1.73 2.98-4.3 2.98-7.34z"/>
                        <path fill="#34A853" d="M13.46 15.13c-.83.59-1.96 1-3.46 1-2.64 0-4.88-1.74-5.68-4.15H1.07v2.52C2.72 17.75 6.09 20 10 20c2.7 0 4.96-.89 6.62-2.42l-3.16-2.45z"/>
                        <path fill="#FBBC05" d="M3.99 10c0-.69.12-1.35.32-1.97V5.51H1.07A9.973 9.973 0 000 10c0 1.61.39 3.14 1.07 4.49l3.24-2.52c-.2-.62-.32-1.28-.32-1.97z"/>
                        <path fill="#EA4335" d="M10 3.88c1.88 0 3.13.81 3.85 1.48l2.84-2.76C14.96.99 12.7 0 10 0 6.09 0 2.72 2.25 1.07 5.51l3.24 2.52C5.12 5.62 7.36 3.88 10 3.88z"/>
                    </svg>
                    Continue with Google
                </button>

                <!-- Facebook Sign In -->
                <button id="facebook-sign-in-btn"
                        class="w-full flex items-center justify-center gap-3 bg-[#1877F2] hover:bg-[#166FE5] text-white font-semibold py-3 px-4 rounded-lg transition">
                    <i class="fab fa-facebook text-xl"></i>
                    Continue with Facebook
                </button>
            </div>

            <p class="text-xs text-gray-500 mt-6 text-center">
                By signing in, you agree to our Terms of Service and Privacy Policy
            </p>
        </div>
    `;

    document.body.appendChild(modal);

    // Add event listeners to buttons
    document.getElementById('google-sign-in-btn').addEventListener('click', async () => {
        const user = await signInWithGoogle();
        if (user) {
            modal.remove();
        }
    });

    document.getElementById('facebook-sign-in-btn').addEventListener('click', async () => {
        const user = await signInWithFacebook();
        if (user) {
            modal.remove();
        }
    });
}

// Check if current user is the owner
function isOwner() {
    if (!currentUser) return false;
    // If no owner is set yet, first user is owner
    if (!OWNER_UID || OWNER_UID === '') return true;
    return currentUser.uid === OWNER_UID;
}

// Get current user
function getCurrentUser() {
    return currentUser;
}

// Check if user is authenticated
function isAuthenticated() {
    return currentUser !== null;
}

// Export functions and auth instance
export { initAuth, signInWithGoogle, signInWithFacebook, signOutUser, getCurrentUser, isAuthenticated, isOwner, auth };
