// Authentication module
import { auth, googleProvider, signInWithPopup, signOut, onAuthStateChanged } from './firebase-config.js';
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
        console.log('Signed in:', result.user.displayName);
        return result.user;
    } catch (error) {
        console.error('Error signing in:', error);
        alert('Failed to sign in. Please try again.');
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
        authButton.onclick = signInWithGoogle;

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
export { initAuth, signInWithGoogle, signOutUser, getCurrentUser, isAuthenticated, isOwner, auth };
