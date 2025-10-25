// Authentication module
import { auth, googleProvider, signInWithPopup, signOut, onAuthStateChanged, createUserWithEmailAndPassword, signInWithEmailAndPassword, updateProfile, sendSignInLinkToEmail, isSignInWithEmailLink, signInWithEmailLink } from './firebase-config.js';
import { db } from './firebase-config.js';
import { collection, query, where, onSnapshot, doc, getDoc } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js';

// Current user state
let currentUser = null;
let pendingSetlistsCount = 0;
let unsubscribePendingCount = null;
let isPromptingForDisplayName = false;

// Admin status cache - checked against Firestore admins collection
let isAdminUser = false;
let adminCheckComplete = false;

// Auth ready callbacks
let authReadyCallbacks = [];

// Check if user is an admin by querying Firestore
async function checkAdminStatus(user) {
    if (!user) {
        isAdminUser = false;
        adminCheckComplete = true;
        return false;
    }

    try {
        const adminDoc = await getDoc(doc(db, 'admins', user.uid));
        isAdminUser = adminDoc.exists();
        adminCheckComplete = true;
        console.log('Admin status checked:', isAdminUser ? 'Is admin' : 'Not admin');
        return isAdminUser;
    } catch (error) {
        console.error('Error checking admin status:', error);
        isAdminUser = false;
        adminCheckComplete = true;
        return false;
    }
}

// Initialize auth state listener
function initAuth(onAuthReady) {
    // Add callback if provided
    if (onAuthReady && typeof onAuthReady === 'function') {
        authReadyCallbacks.push(onAuthReady);
    }

    // Check for email link sign-in on page load
    completeEmailLinkSignIn();

    onAuthStateChanged(auth, async (user) => {
        currentUser = user;

        // Check admin status from Firestore
        await checkAdminStatus(user);

        updateAuthUI();

        // Check if authenticated user needs to set display name
        if (user && !user.displayName) {
            // Prompt for display name, but don't await here to avoid blocking auth state
            promptForDisplayName(user).catch(error => {
                console.error('Error prompting for display name:', error);
            });
        }

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

        // Call all registered callbacks when auth state is ready
        if (authReadyCallbacks.length > 0) {
            authReadyCallbacks.forEach(callback => callback(user));
            authReadyCallbacks = []; // Clear callbacks after calling
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

// Sign up with email and password
async function signUpWithEmail(email, password, displayName) {
    try {
        const result = await createUserWithEmailAndPassword(auth, email, password);

        // Update the user's profile with display name if provided
        if (displayName && displayName.trim()) {
            await updateProfile(result.user, {
                displayName: displayName.trim()
            });
        }
        // Note: If no display name provided, onAuthStateChanged listener will prompt

        console.log('Signed up with email:', result.user.email);
        return result.user;
    } catch (error) {
        console.error('Error signing up with email:', error);
        let errorMessage = 'Failed to sign up. Please try again.';

        if (error.code === 'auth/email-already-in-use') {
            errorMessage = 'This email is already registered. Please sign in instead.';
        } else if (error.code === 'auth/invalid-email') {
            errorMessage = 'Invalid email address.';
        } else if (error.code === 'auth/weak-password') {
            errorMessage = 'Password should be at least 6 characters.';
        }

        alert(errorMessage);
        return null;
    }
}

// Sign in with email and password
async function signInWithEmail(email, password) {
    try {
        const result = await signInWithEmailAndPassword(auth, email, password);
        console.log('Signed in with email:', result.user.email);
        return result.user;
    } catch (error) {
        console.error('Error signing in with email:', error);
        let errorMessage = 'Failed to sign in. Please try again.';

        if (error.code === 'auth/invalid-credential' || error.code === 'auth/wrong-password' || error.code === 'auth/user-not-found') {
            errorMessage = 'Invalid email or password.';
        } else if (error.code === 'auth/invalid-email') {
            errorMessage = 'Invalid email address.';
        }

        alert(errorMessage);
        return null;
    }
}

// Send email sign-in link (passwordless)
async function sendEmailSignInLink(email) {
    try {
        // Encode email in URL so we can retrieve it even on different devices
        const urlWithEmail = `${window.location.origin}${window.location.pathname}?email=${encodeURIComponent(email)}`;

        const actionCodeSettings = {
            url: urlWithEmail,
            handleCodeInApp: true,
        };

        await sendSignInLinkToEmail(auth, email, actionCodeSettings);

        // Save the email locally as backup
        window.localStorage.setItem('emailForSignIn', email);

        console.log('Sign-in link sent to:', email);
        return true;
    } catch (error) {
        console.error('Error sending sign-in link:', error);
        let errorMessage = 'Failed to send sign-in link. Please try again.';

        if (error.code === 'auth/invalid-email') {
            errorMessage = 'Invalid email address.';
        } else if (error.code === 'auth/quota-exceeded') {
            errorMessage = 'Too many requests. Please try again later.';
        }

        alert(errorMessage);
        return false;
    }
}

// Complete email link sign-in
async function completeEmailLinkSignIn() {
    if (isSignInWithEmailLink(auth, window.location.href)) {
        // Try to get email from multiple sources
        let email = null;

        // 1. Check URL parameters (works across devices)
        const urlParams = new URLSearchParams(window.location.search);
        email = urlParams.get('email');

        // 2. Fallback to localStorage (same device)
        if (!email) {
            email = window.localStorage.getItem('emailForSignIn');
        }

        if (!email) {
            console.error('Could not retrieve email for sign-in');
            alert('Unable to complete sign-in. Please try requesting a new link.');
            return null;
        }

        try {
            const result = await signInWithEmailLink(auth, email, window.location.href);
            window.localStorage.removeItem('emailForSignIn');
            console.log('Successfully signed in with email link:', result.user.email);

            // Clean up the URL (remove email parameter and Firebase auth parameters)
            window.history.replaceState({}, document.title, window.location.pathname);

            // Note: Display name prompt will be handled by onAuthStateChanged listener
            // If user has display name, redirect to home page
            if (result.user.displayName) {
                window.location.href = '/';
            }
            // Otherwise, wait for display name prompt which will redirect after submission

            return result.user;
        } catch (error) {
            console.error('Error signing in with email link:', error);
            alert('Failed to sign in with email link. Please try again.');
            return null;
        }
    }
    return null;
}

// Prompt user to set their display name
async function promptForDisplayName(user) {
    // Prevent duplicate prompts
    if (isPromptingForDisplayName) {
        return null;
    }

    // Check if modal already exists
    if (document.getElementById('display-name-modal')) {
        return null;
    }

    isPromptingForDisplayName = true;

    // Create modal
    const modal = document.createElement('div');
    modal.id = 'display-name-modal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';

    modal.innerHTML = `
        <div class="bg-white rounded-lg p-8 max-w-md w-full shadow-2xl">
            <h2 class="text-2xl font-bold text-[#2d1b1b] mb-4">Welcome!</h2>
            <p class="text-gray-600 mb-6">Please tell us your name so others can identify you when you post photos or comments.</p>

            <form id="display-name-form" class="space-y-4">
                <div>
                    <label for="user-display-name" class="block text-sm font-medium text-gray-700 mb-1">Your Name</label>
                    <input type="text" id="user-display-name" required
                           class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#d4773e] text-gray-900"
                           placeholder="Enter your name">
                </div>

                <button type="submit"
                        class="w-full bg-[#d4773e] hover:bg-[#bf6535] text-white font-semibold py-3 px-4 rounded-lg transition">
                    Continue
                </button>
            </form>
        </div>
    `;

    document.body.appendChild(modal);

    // Handle form submission
    return new Promise((resolve) => {
        const form = document.getElementById('display-name-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const displayName = document.getElementById('user-display-name').value.trim();

            if (displayName) {
                try {
                    await updateProfile(user, { displayName: displayName });
                    console.log('Display name set to:', displayName);
                    modal.remove();
                    isPromptingForDisplayName = false;
                    // Redirect to home page after setting display name
                    window.location.href = '/';
                    resolve(displayName);
                } catch (error) {
                    console.error('Error setting display name:', error);
                    alert('Failed to set display name. Please try again.');
                    isPromptingForDisplayName = false;
                }
            }
        });
    });
}

// Sign out
async function signOutUser() {
    try {
        await signOut(auth);
        console.log('Signed out');
        // Redirect to home page after sign out
        window.location.href = '/';
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
            const displayName = currentUser.displayName || currentUser.email.split('@')[0];
            const userPhoto = currentUser.photoURL
                ? `<img src="${currentUser.photoURL}" alt="${displayName}" class="w-8 h-8 rounded-full">`
                : `<div class="w-8 h-8 rounded-full bg-[#2d1b1b] text-white flex items-center justify-center font-semibold">${displayName.charAt(0).toUpperCase()}</div>`;

            userInfo.innerHTML = `
                <div class="flex items-center space-x-3">
                    ${userPhoto}
                    <span>${displayName}</span>
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
                <h2 id="modal-title" class="text-2xl font-bold text-[#2d1b1b]">Sign In</h2>
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
            </div>

            <!-- Divider -->
            <div class="flex items-center my-6">
                <div class="flex-1 border-t border-gray-300"></div>
                <span class="px-4 text-gray-500 text-sm">OR</span>
                <div class="flex-1 border-t border-gray-300"></div>
            </div>

            <!-- Email/Password Form -->
            <form id="email-auth-form" class="space-y-4">
                <!-- Display Name (only for sign up) -->
                <div id="display-name-field" style="display: none;">
                    <label for="display-name" class="block text-sm font-medium text-gray-700 mb-1">
                        Display Name <span class="text-xs text-gray-500">(shown on photos & comments)</span>
                    </label>
                    <input type="text" id="display-name"
                           class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2d1b1b] text-gray-900"
                           placeholder="Enter your name">
                </div>

                <!-- Email -->
                <div>
                    <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input type="email" id="email" required
                           class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2d1b1b] text-gray-900"
                           placeholder="Enter your email">
                </div>

                <!-- Password -->
                <div>
                    <label for="password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
                    <input type="password" id="password" required
                           class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2d1b1b] text-gray-900"
                           placeholder="Enter your password">
                </div>

                <!-- Submit Button -->
                <button type="submit" id="email-auth-submit"
                        class="w-full bg-[#2d1b1b] hover:bg-[#1a1010] text-white font-semibold py-3 px-4 rounded-lg transition">
                    Sign In with Email
                </button>
            </form>

            <!-- Email Link Alternative -->
            <div class="text-center mt-3">
                <button id="email-link-sign-in-btn" class="text-sm text-[#d4773e] hover:text-[#bf6535] font-semibold">
                    <i class="fas fa-magic mr-1"></i>Or send me a magic link instead
                </button>
            </div>

            <!-- Toggle between Sign In / Sign Up -->
            <p class="text-sm text-center mt-4">
                <span id="toggle-text" class="text-gray-600">Don't have an account?</span>
                <button id="toggle-mode" class="text-[#2d1b1b] font-semibold hover:underline ml-1">
                    Sign Up
                </button>
            </p>

            <p class="text-xs text-gray-500 mt-6 text-center">
                By signing in, you agree to our Terms of Service and Privacy Policy
            </p>
        </div>
    `;

    document.body.appendChild(modal);

    // Track mode (sign-in or sign-up)
    let isSignUpMode = false;

    // Add event listeners to social buttons
    document.getElementById('google-sign-in-btn').addEventListener('click', async () => {
        const user = await signInWithGoogle();
        if (user) {
            modal.remove();
            // Redirect to home page after sign in
            window.location.href = '/';
        }
    });

    // Email link sign-in
    document.getElementById('email-link-sign-in-btn').addEventListener('click', async () => {
        const email = document.getElementById('email').value;

        if (!email) {
            alert('Please enter your email address first');
            document.getElementById('email').focus();
            return;
        }

        const success = await sendEmailSignInLink(email);
        if (success) {
            modal.remove();
            alert('Check your email! We sent you a magic link to sign in. Click the link in the email to complete sign-in.');
        }
    });

    // Toggle between sign-in and sign-up
    const toggleButton = document.getElementById('toggle-mode');
    const toggleText = document.getElementById('toggle-text');
    const modalTitle = document.getElementById('modal-title');
    const submitButton = document.getElementById('email-auth-submit');
    const displayNameField = document.getElementById('display-name-field');

    toggleButton.addEventListener('click', () => {
        isSignUpMode = !isSignUpMode;

        if (isSignUpMode) {
            modalTitle.textContent = 'Sign Up';
            submitButton.textContent = 'Sign Up with Email';
            toggleText.textContent = 'Already have an account?';
            toggleButton.textContent = 'Sign In';
            displayNameField.style.display = 'block';
        } else {
            modalTitle.textContent = 'Sign In';
            submitButton.textContent = 'Sign In with Email';
            toggleText.textContent = "Don't have an account?";
            toggleButton.textContent = 'Sign Up';
            displayNameField.style.display = 'none';
        }
    });

    // Handle email/password form submission
    const emailForm = document.getElementById('email-auth-form');
    emailForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const displayName = document.getElementById('display-name').value;

        let user;
        if (isSignUpMode) {
            user = await signUpWithEmail(email, password, displayName);
        } else {
            user = await signInWithEmail(email, password);
        }

        if (user) {
            modal.remove();
            // Redirect to home page after sign in
            window.location.href = '/';
        }
    });
}

// Check if current user is an admin/owner
function isOwner() {
    if (!currentUser) return false;
    return isAdminUser;
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
export { initAuth, signInWithGoogle, signUpWithEmail, signInWithEmail, sendEmailSignInLink, signOutUser, getCurrentUser, isAuthenticated, isOwner, auth };
