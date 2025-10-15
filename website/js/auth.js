// Authentication module
import { auth, googleProvider, signInWithPopup, signOut, onAuthStateChanged } from './firebase-config.js';

// Current user state
let currentUser = null;

// Owner UID - we'll set this to your friend's Google ID after he logs in the first time
// For now, leave empty - the first person to log in will be considered the owner
const OWNER_UID = '';  // We'll update this later

// Initialize auth state listener
function initAuth() {
    onAuthStateChanged(auth, (user) => {
        currentUser = user;
        updateAuthUI();
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
