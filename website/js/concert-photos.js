// Concert photos upload and display functionality

import {
  auth,
  db,
  storage,
  collection,
  addDoc,
  getDocs,
  query,
  where,
  orderBy,
  serverTimestamp,
  doc,
  deleteDoc,
  ref,
  uploadBytesResumable,
  getDownloadURL,
  deleteObject
} from './firebase-config.js';
import { getCurrentUser, isOwner } from './auth.js';

let currentConcertId = null;

/**
 * Initialize photo upload functionality
 */
export function initPhotoUpload(concertId) {
  currentConcertId = concertId;

  // Load photos for this concert
  loadPhotos(concertId);

  // Set up upload button
  const uploadBtn = document.getElementById('upload-photo-btn');
  const uploadForm = document.getElementById('photo-upload-form');
  const cancelBtn = document.getElementById('cancel-photo-btn');
  const submitBtn = document.getElementById('submit-photo-btn');
  const fileInput = document.getElementById('photo-file-input');

  if (!uploadBtn || !uploadForm || !cancelBtn || !submitBtn || !fileInput) {
    console.error('Photo upload elements not found in DOM');
    return;
  }

  // Show upload button for authenticated users
  // Use a timeout to check auth state after auth.js initializes
  const checkAuthState = () => {
    const user = getCurrentUser();
    if (user) {
      uploadBtn.classList.remove('hidden');
    } else {
      uploadBtn.classList.add('hidden');
    }
  };

  // Check immediately
  checkAuthState();

  // Also listen for auth state changes
  auth.onAuthStateChanged(user => {
    checkAuthState();
  });

  // Toggle upload form
  uploadBtn.addEventListener('click', () => {
    uploadForm.classList.toggle('hidden');
    fileInput.value = '';
    document.getElementById('photo-caption-input').value = '';
  });

  // Cancel upload
  cancelBtn.addEventListener('click', () => {
    uploadForm.classList.add('hidden');
    fileInput.value = '';
    document.getElementById('photo-caption-input').value = '';
  });

  // Submit photo
  submitBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) {
      alert('Please select a photo to upload');
      return;
    }

    const caption = document.getElementById('photo-caption-input').value;
    await uploadPhoto(file, concertId, caption);
  });
}

/**
 * Upload a photo to Firebase Storage and save metadata to Firestore
 */
async function uploadPhoto(file, concertId, caption = '') {
  const user = getCurrentUser();
  if (!user) {
    alert('You must be signed in to upload photos');
    return;
  }

  // Validate file type
  if (!file.type.startsWith('image/')) {
    alert('Please select an image file (JPG, PNG, WEBP, or GIF)');
    return;
  }

  // Validate file size (5MB max)
  const maxSize = 5 * 1024 * 1024; // 5MB
  if (file.size > maxSize) {
    alert('Photo size must be under 5MB. Please resize your image.');
    return;
  }

  try {
    // Show progress
    const progressContainer = document.getElementById('upload-progress');
    const progressBar = document.getElementById('upload-progress-bar');
    const submitBtn = document.getElementById('submit-photo-btn');

    progressContainer.classList.remove('hidden');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Uploading...';

    // Resize image before upload
    const resizedFile = await resizeImage(file, 1920);

    // Generate unique photo ID
    const photoId = generatePhotoId();
    const fileExtension = file.name.split('.').pop();
    const storagePath = `concert_photos/${concertId}/${photoId}.${fileExtension}`;

    // Upload to Firebase Storage
    const storageRef = ref(storage, storagePath);
    const uploadTask = uploadBytesResumable(storageRef, resizedFile);

    // Monitor upload progress
    uploadTask.on('state_changed',
      (snapshot) => {
        const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
        progressBar.style.width = progress + '%';
      },
      (error) => {
        console.error('Upload error:', error);
        alert('Error uploading photo: ' + error.message);
        progressContainer.classList.add('hidden');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Upload';
      },
      async () => {
        // Upload complete - get download URL
        const downloadURL = await getDownloadURL(uploadTask.snapshot.ref);

        // Save metadata to Firestore
        console.log('Saving photo with concert_id:', concertId, 'Type:', typeof concertId);
        await addDoc(collection(db, 'concert_photos'), {
          concert_id: concertId,
          user_id: user.uid,
          user_name: user.displayName || 'Anonymous',
          user_photo: user.photoURL || '',
          storage_path: storagePath,
          download_url: downloadURL,
          uploaded_at: serverTimestamp(),
          file_size: resizedFile.size,
          file_type: resizedFile.type,
          caption: caption
        });

        // Reset form
        document.getElementById('photo-file-input').value = '';
        document.getElementById('photo-caption-input').value = '';
        document.getElementById('photo-upload-form').classList.add('hidden');
        progressContainer.classList.add('hidden');
        progressBar.style.width = '0%';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Upload';

        // Reload photos
        await loadPhotos(concertId);

        alert('Photo uploaded successfully!');
      }
    );

  } catch (error) {
    console.error('Error uploading photo:', error);
    alert('Error uploading photo: ' + error.message);
  }
}

/**
 * Resize image to max width/height while maintaining aspect ratio
 */
function resizeImage(file, maxSize) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        // Calculate new dimensions
        let width = img.width;
        let height = img.height;

        if (width > maxSize || height > maxSize) {
          if (width > height) {
            height = (height / width) * maxSize;
            width = maxSize;
          } else {
            width = (width / height) * maxSize;
            height = maxSize;
          }
        }

        // Create canvas and resize
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);

        // Convert to blob
        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(new File([blob], file.name, {
                type: file.type,
                lastModified: Date.now()
              }));
            } else {
              reject(new Error('Failed to resize image'));
            }
          },
          file.type,
          0.9 // Quality (90%)
        );
      };
      img.onerror = () => reject(new Error('Failed to load image'));
      img.src = e.target.result;
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsDataURL(file);
  });
}

/**
 * Load photos for a concert
 */
async function loadPhotos(concertId) {
  try {
    // First try to load from Firestore (real-time)
    console.log('Loading photos for concert_id:', concertId, 'Type:', typeof concertId);
    const photosQuery = query(
      collection(db, 'concert_photos'),
      where('concert_id', '==', concertId),
      orderBy('uploaded_at', 'desc')
    );

    const snapshot = await getDocs(photosQuery);
    console.log('Firestore query returned', snapshot.size, 'documents');
    const photos = [];

    snapshot.forEach(doc => {
      const data = doc.data();
      photos.push({
        id: doc.id,
        user_name: data.user_name,
        user_photo: data.user_photo,
        download_url: data.download_url,
        uploaded_at: data.uploaded_at,
        caption: data.caption,
        file_type: data.file_type,
        user_id: data.user_id,
        storage_path: data.storage_path
      });
    });

    console.log(`Loaded ${photos.length} photos from Firestore for concert ${concertId}`);
    renderPhotoGallery(photos);

  } catch (error) {
    console.error('Error loading photos from Firestore:', error);

    // Fallback: Try loading from static JSON if concert has setlist
    try {
      console.log('Attempting to load photos from static JSON...');
      const response = await fetch(`data/concert_details/${concertId}.json?v=${Date.now()}`);
      if (response.ok) {
        const concertData = await response.json();
        if (concertData.photos && concertData.photos.length > 0) {
          console.log(`Loaded ${concertData.photos.length} photos from JSON for concert ${concertId}`);
          // Convert JSON photos to expected format
          const jsonPhotos = concertData.photos.map(photo => ({
            id: photo.id,
            user_name: photo.user_name,
            user_photo: photo.user_photo,
            download_url: photo.download_url,
            uploaded_at: photo.uploaded_at ? { toDate: () => new Date(photo.uploaded_at) } : null,
            caption: photo.caption,
            file_type: photo.file_type
          }));
          renderPhotoGallery(jsonPhotos);
          return;
        }
      }
    } catch (jsonError) {
      console.error('Error loading photos from JSON:', jsonError);
    }

    // If all else fails, show no photos message
    document.getElementById('photos-grid').innerHTML = '';
    const noPhotosMsg = document.getElementById('no-photos-message');
    if (noPhotosMsg) {
      noPhotosMsg.classList.remove('hidden');
    }
  }
}

/**
 * Render photo gallery
 */
function renderPhotoGallery(photos) {
  const grid = document.getElementById('photos-grid');
  const noPhotosMessage = document.getElementById('no-photos-message');

  if (!grid) {
    console.error('Photos grid element not found');
    return;
  }

  if (photos.length === 0) {
    grid.innerHTML = '';
    if (noPhotosMessage) {
      noPhotosMessage.classList.remove('hidden');
    }
    return;
  }

  if (noPhotosMessage) {
    noPhotosMessage.classList.add('hidden');
  }

  const user = getCurrentUser();
  const userIsOwner = isOwner();

  grid.innerHTML = photos.map(photo => {
    const canDelete = user && (photo.user_id === user.uid || userIsOwner);
    const uploadedDate = photo.uploaded_at ? formatDate(photo.uploaded_at.toDate()) : 'Just now';

    return `
      <div class="photo-card border-2 border-[#d4773e] rounded-lg overflow-hidden bg-white" data-photo-id="${photo.id}">
        <img src="${photo.download_url}"
             alt="Concert photo"
             class="w-full h-64 object-cover cursor-pointer hover:opacity-90 transition"
             onclick="openPhotoModal('${photo.download_url}', '${escapeHtml(photo.caption || '')}', '${escapeHtml(photo.user_name)}')">
        <div class="p-3">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              ${photo.user_photo ? `<img src="${photo.user_photo}" class="w-8 h-8 rounded-full" alt="${escapeHtml(photo.user_name)}">` : `<div class="w-8 h-8 rounded-full bg-[#d4773e] flex items-center justify-center text-white font-bold">${photo.user_name.charAt(0).toUpperCase()}</div>`}
              <span class="font-bold text-[#2d1b1b]">${escapeHtml(photo.user_name)}</span>
            </div>
            ${canDelete ? `
              <button class="delete-photo-btn text-red-600 hover:text-red-800 transition"
                      onclick="deletePhotoConfirm('${photo.id}', '${photo.storage_path}')">
                <i class="fas fa-trash"></i>
              </button>
            ` : ''}
          </div>
          ${photo.caption ? `<p class="text-sm text-[#2d1b1b] mb-2">${escapeHtml(photo.caption)}</p>` : ''}
          <p class="text-xs opacity-70 text-[#2d1b1b]">${uploadedDate}</p>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Delete photo
 */
window.deletePhotoConfirm = async function(photoId, storagePath) {
  if (!confirm('Are you sure you want to delete this photo?')) {
    return;
  }

  try {
    // Delete from Firestore
    await deleteDoc(doc(db, 'concert_photos', photoId));

    // Delete from Storage
    const storageRef = ref(storage, storagePath);
    await deleteObject(storageRef);

    // Reload photos
    await loadPhotos(currentConcertId);

    alert('Photo deleted successfully');

  } catch (error) {
    console.error('Error deleting photo:', error);
    alert('Error deleting photo: ' + error.message);
  }
};

/**
 * Open photo modal (full size view)
 */
window.openPhotoModal = function(url, caption, userName) {
  // Create modal
  const modal = document.createElement('div');
  modal.id = 'photo-modal';
  modal.className = 'fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4';
  modal.onclick = (e) => {
    if (e.target === modal) {
      modal.remove();
    }
  };

  modal.innerHTML = `
    <div class="max-w-6xl w-full">
      <div class="flex justify-end mb-2">
        <button onclick="document.getElementById('photo-modal').remove()"
                class="text-white hover:text-gray-300 text-3xl">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <img src="${url}" alt="Concert photo" class="w-full h-auto max-h-[80vh] object-contain">
      ${caption || userName ? `
        <div class="text-white mt-4 text-center">
          ${userName ? `<p class="font-bold">${escapeHtml(userName)}</p>` : ''}
          ${caption ? `<p class="mt-2">${escapeHtml(caption)}</p>` : ''}
        </div>
      ` : ''}
    </div>
  `;

  document.body.appendChild(modal);
};

/**
 * Generate unique photo ID
 */
function generatePhotoId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * Format date for display
 */
function formatDate(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
