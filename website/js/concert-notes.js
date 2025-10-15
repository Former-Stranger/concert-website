// Concert notes and comments functionality
import { isAuthenticated, isOwner, getCurrentUser } from './auth.js';
import { db, collection, addDoc, getDocs, query, where, orderBy, serverTimestamp, doc, setDoc, getDoc } from './firebase-config.js';

// Get concert ID from URL
const urlParams = new URLSearchParams(window.location.search);
const concertId = urlParams.get('id');

// Initialize notes and comments
export async function initNotesAndComments() {
    if (!concertId) return;

    // Wait for auth to initialize
    setTimeout(async () => {
        await loadNotes();
        await loadComments();
        setupEventListeners();
        updateUIBasedOnAuth();
    }, 500);
}

// Update UI based on authentication state
function updateUIBasedOnAuth() {
    const isAuth = isAuthenticated();
    const isOwn = isOwner();

    // Notes section - only show to owner
    const notesSection = document.getElementById('notes-section');
    const editNotesBtn = document.getElementById('edit-notes-btn');

    if (notesSection) {
        if (isOwn) {
            notesSection.classList.remove('hidden');
            if (editNotesBtn) {
                editNotesBtn.classList.remove('hidden');
            }
        } else {
            notesSection.classList.add('hidden');
        }
    }

    // Comments section - any authenticated user can comment
    const commentForm = document.getElementById('comment-form');
    const commentSigninPrompt = document.getElementById('comment-signin-prompt');

    if (isAuth && commentForm && commentSigninPrompt) {
        commentForm.classList.remove('hidden');
        commentSigninPrompt.classList.add('hidden');
    } else if (commentSigninPrompt) {
        commentSigninPrompt.classList.remove('hidden');
    }
}

// Load personal notes
async function loadNotes() {
    const notesDisplay = document.getElementById('notes-display');
    if (!notesDisplay) return;

    try {
        const noteDoc = await getDoc(doc(db, 'concert_notes', concertId));

        if (noteDoc.exists()) {
            const data = noteDoc.data();
            notesDisplay.innerHTML = `
                <div class="bg-white border-2 border-[#d4773e] rounded p-4">
                    <div class="whitespace-pre-wrap">${escapeHtml(data.notes)}</div>
                    <div class="text-xs opacity-50 mt-2">Last updated: ${formatTimestamp(data.updated_at)}</div>
                </div>
            `;
        } else {
            notesDisplay.innerHTML = `
                <div class="text-center py-6 opacity-70">
                    <i class="fas fa-info-circle mr-2"></i>
                    No notes yet for this concert
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading notes:', error);
        notesDisplay.innerHTML = `
            <div class="text-center py-6 opacity-70 text-red-600">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                Error loading notes
            </div>
        `;
    }
}

// Load comments
async function loadComments() {
    const commentsList = document.getElementById('comments-list');
    if (!commentsList) return;

    try {
        // Query without orderBy to avoid needing a composite index
        const q = query(
            collection(db, 'concert_comments'),
            where('concert_id', '==', concertId)
        );

        const querySnapshot = await getDocs(q);

        if (querySnapshot.empty) {
            commentsList.innerHTML = `
                <div class="text-center py-6 opacity-70">
                    <i class="fas fa-info-circle mr-2"></i>
                    No comments yet. Be the first to share your thoughts!
                </div>
            `;
            return;
        }

        const comments = [];
        querySnapshot.forEach((doc) => {
            comments.push({ id: doc.id, ...doc.data() });
        });

        // Sort comments by created_at in JavaScript (newest first)
        comments.sort((a, b) => {
            if (!a.created_at) return 1;
            if (!b.created_at) return -1;
            const aTime = a.created_at.toMillis ? a.created_at.toMillis() : new Date(a.created_at).getTime();
            const bTime = b.created_at.toMillis ? b.created_at.toMillis() : new Date(b.created_at).getTime();
            return bTime - aTime; // Descending order (newest first)
        });

        commentsList.innerHTML = comments.map(comment => `
            <div class="bg-white border-2 border-[#d4773e] rounded p-4">
                <div class="flex items-center mb-2">
                    <img src="${comment.user_photo || '/default-avatar.png'}"
                         alt="${comment.user_name}"
                         class="w-8 h-8 rounded-full mr-2">
                    <div>
                        <div class="font-bold">${escapeHtml(comment.user_name)}</div>
                        <div class="text-xs opacity-50">${formatTimestamp(comment.created_at)}</div>
                    </div>
                </div>
                <div class="whitespace-pre-wrap">${escapeHtml(comment.comment)}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading comments:', error);
        commentsList.innerHTML = `
            <div class="text-center py-6 opacity-70 text-red-600">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                Error loading comments
            </div>
        `;
    }
}

// Setup event listeners
function setupEventListeners() {
    // Edit notes button
    const editNotesBtn = document.getElementById('edit-notes-btn');
    if (editNotesBtn) {
        editNotesBtn.addEventListener('click', showNotesEditor);
    }

    // Save notes button
    const saveNotesBtn = document.getElementById('save-notes-btn');
    if (saveNotesBtn) {
        saveNotesBtn.addEventListener('click', saveNotes);
    }

    // Cancel notes button
    const cancelNotesBtn = document.getElementById('cancel-notes-btn');
    if (cancelNotesBtn) {
        cancelNotesBtn.addEventListener('click', hideNotesEditor);
    }

    // Post comment button
    const postCommentBtn = document.getElementById('post-comment-btn');
    if (postCommentBtn) {
        postCommentBtn.addEventListener('click', postComment);
    }
}

// Show notes editor
async function showNotesEditor() {
    const notesEditor = document.getElementById('notes-editor');
    const editNotesBtn = document.getElementById('edit-notes-btn');
    const notesTextarea = document.getElementById('notes-textarea');

    if (!notesEditor || !editNotesBtn || !notesTextarea) return;

    // Load current notes into textarea
    try {
        const noteDoc = await getDoc(doc(db, 'concert_notes', concertId));
        if (noteDoc.exists()) {
            notesTextarea.value = noteDoc.data().notes;
        } else {
            notesTextarea.value = '';
        }
    } catch (error) {
        console.error('Error loading notes for editing:', error);
    }

    notesEditor.classList.remove('hidden');
    editNotesBtn.classList.add('hidden');
}

// Hide notes editor
function hideNotesEditor() {
    const notesEditor = document.getElementById('notes-editor');
    const editNotesBtn = document.getElementById('edit-notes-btn');

    if (!notesEditor || !editNotesBtn) return;

    notesEditor.classList.add('hidden');
    editNotesBtn.classList.remove('hidden');
}

// Save notes
async function saveNotes() {
    if (!isOwner()) {
        alert('Only the owner can edit notes');
        return;
    }

    const notesTextarea = document.getElementById('notes-textarea');
    const saveNotesBtn = document.getElementById('save-notes-btn');

    if (!notesTextarea || !saveNotesBtn) return;

    const notes = notesTextarea.value.trim();

    if (!notes) {
        alert('Please enter some notes');
        return;
    }

    saveNotesBtn.disabled = true;
    saveNotesBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';

    try {
        await setDoc(doc(db, 'concert_notes', concertId), {
            concert_id: concertId,
            notes: notes,
            updated_at: serverTimestamp()
        });

        // Reload notes
        await loadNotes();
        hideNotesEditor();
    } catch (error) {
        console.error('Error saving notes:', error);
        alert('Failed to save notes. Please try again.');
    } finally {
        saveNotesBtn.disabled = false;
        saveNotesBtn.innerHTML = '<i class="fas fa-save mr-2"></i>Save Notes';
    }
}

// Post comment
async function postComment() {
    if (!isAuthenticated()) {
        alert('Please sign in to comment');
        return;
    }

    const commentTextarea = document.getElementById('comment-textarea');
    const postCommentBtn = document.getElementById('post-comment-btn');

    if (!commentTextarea || !postCommentBtn) return;

    const comment = commentTextarea.value.trim();

    if (!comment) {
        alert('Please enter a comment');
        return;
    }

    postCommentBtn.disabled = true;
    postCommentBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Posting...';

    try {
        const user = getCurrentUser();

        await addDoc(collection(db, 'concert_comments'), {
            concert_id: concertId,
            comment: comment,
            user_id: user.uid,
            user_name: user.displayName,
            user_photo: user.photoURL,
            created_at: serverTimestamp()
        });

        // Clear textarea
        commentTextarea.value = '';

        // Reload comments
        await loadComments();
    } catch (error) {
        console.error('Error posting comment:', error);
        alert('Failed to post comment. Please try again.');
    } finally {
        postCommentBtn.disabled = false;
        postCommentBtn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i>Post Comment';
    }
}

// Utility: Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility: Format timestamp
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Just now';

    // Handle Firestore timestamp
    const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp);

    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;

    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}
