# Concert Photo Upload Feature

## Overview

This feature allows authenticated users to upload photos to concerts. Photos are stored in Firebase Storage and metadata is stored in Firestore. Photos are displayed in a gallery on each concert's detail page.

## Architecture

### Data Storage

**Firebase Storage**: Stores actual photo files
- Path structure: `/concert_photos/{concert_id}/{photo_id}.{extension}`
- Files are resized client-side before upload (max 1920px width/height)
- Supported formats: JPG, PNG, WEBP, GIF
- Max file size: 5MB (enforced client-side and in storage rules)

**Firestore Collection**: `concert_photos`
- Stores photo metadata and references
- Links photos to concerts and users
- Exported to JSON for static site display

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    USER UPLOADS PHOTO                        │
│                                                              │
│  1. User clicks "Upload Photo" on concert page             │
│  2. Selects image file (JPG, PNG, WEBP, GIF)              │
│  3. Client-side: Image resized to max 1920px              │
│  4. Client-side: File uploaded to Firebase Storage         │
│  5. Client-side: Metadata saved to Firestore              │
│  6. UI updates immediately to show new photo               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 FIREBASE STORAGE                             │
│                                                              │
│  /concert_photos/                                           │
│    ├── {concert_id}/                                        │
│    │   ├── {photo_id_1}.jpg                                │
│    │   ├── {photo_id_2}.png                                │
│    │   └── {photo_id_3}.jpg                                │
│    └── {another_concert_id}/                               │
│        └── {photo_id_4}.jpg                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  FIRESTORE COLLECTION                        │
│                  concert_photos                              │
│                                                              │
│  {photo_id_1}:                                              │
│    concert_id: "123"                                        │
│    user_id: "abc123"                                        │
│    user_name: "John Doe"                                    │
│    storage_path: "concert_photos/123/photo_id_1.jpg"       │
│    download_url: "https://..."                             │
│    uploaded_at: timestamp                                   │
│    file_size: 245678                                        │
│    file_type: "image/jpeg"                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           DEPLOYMENT (Triggered manually or via deploy)     │
│                                                              │
│  1. export_to_web.py reads concert_photos collection       │
│  2. Generates JSON files with photo metadata               │
│  3. concert_details/{id}.json includes photos array        │
│  4. Static site displays photos from Firebase Storage URLs │
└─────────────────────────────────────────────────────────────┘
```

## Firestore Schema

### Collection: `concert_photos`

```javascript
{
  id: auto-generated          // Unique photo ID
  concert_id: string          // Reference to concert
  user_id: string             // Firebase Auth UID of uploader
  user_name: string           // Display name of uploader
  user_photo: string          // Profile photo URL of uploader (optional)
  storage_path: string        // Path in Firebase Storage
  download_url: string        // Public download URL
  uploaded_at: timestamp      // When photo was uploaded
  file_size: number           // File size in bytes
  file_type: string           // MIME type (image/jpeg, image/png, etc.)
  caption: string             // Optional caption (optional)
}
```

### Example Document

```json
{
  "id": "abc123xyz",
  "concert_id": "1274",
  "user_id": "jBa71VgYp0Qz782bawa4SgjHu1l1",
  "user_name": "Jason",
  "user_photo": "https://...",
  "storage_path": "concert_photos/1274/abc123xyz.jpg",
  "download_url": "https://firebasestorage.googleapis.com/...",
  "uploaded_at": "2024-01-15T10:30:00Z",
  "file_size": 245678,
  "file_type": "image/jpeg",
  "caption": "Great view from the front row!"
}
```

## Security Rules

### Firestore Rules (`firestore.rules`)

```javascript
// Concert photos - authenticated users can create, everyone can read, uploader can delete
match /concert_photos/{photoId} {
  // Everyone can read photos
  allow read: if true;

  // Authenticated users can upload photos
  allow create: if isAuthenticated()
                && request.resource.data.user_id == request.auth.uid
                && request.resource.data.user_name == request.auth.token.name
                && request.resource.data.concert_id is string
                && request.resource.data.storage_path is string
                && request.resource.data.download_url is string;

  // Users can delete their own photos, or owner can delete any photo
  allow delete: if isAuthenticated()
                && (resource.data.user_id == request.auth.uid || isOwner());

  // Photos cannot be updated (must delete and re-upload)
  allow update: if false;
}
```

### Storage Rules (`storage.rules`)

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Concert photos
    match /concert_photos/{concertId}/{photoId} {
      // Anyone can read photos
      allow read: if true;

      // Authenticated users can upload photos
      allow create: if request.auth != null
                    && request.resource.size < 5 * 1024 * 1024  // Max 5MB
                    && request.resource.contentType.matches('image/.*');

      // Users can delete their own photos (we verify ownership via Firestore)
      allow delete: if request.auth != null;
    }
  }
}
```

## Client-Side Implementation

### File Structure

```
website/js/
├── firebase-config.js      (Updated: Add Storage imports)
├── concert-photos.js       (New: Photo upload module)
└── concert.js              (Updated: Display photos)

website/
└── concert.html            (Updated: Add photo gallery UI)
```

### Key Functions

**concert-photos.js**
- `initPhotoUpload()` - Initialize photo upload UI
- `uploadPhoto(file, concertId)` - Handle file upload
- `resizeImage(file, maxSize)` - Resize image before upload
- `loadPhotos(concertId)` - Load photos for a concert
- `deletePhoto(photoId)` - Delete a photo
- `renderPhotoGallery(photos)` - Render photo gallery

**concert.js (updates)**
- Load and display photos in gallery section
- Show upload button for authenticated users
- Handle photo deletion for authorized users

### User Interface

#### Photo Gallery Section (concert.html)
```html
<!-- Photos Section -->
<div id="photos-section" class="mt-8">
    <div class="marquee-header text-center text-2xl rounded flex justify-between items-center">
        <span><i class="fas fa-camera mr-3"></i>Photos</span>
        <button id="upload-photo-btn" class="hidden text-lg">
            <i class="fas fa-plus mr-2"></i>Upload Photo
        </button>
    </div>

    <!-- Photo Upload Form (Hidden by default) -->
    <div id="photo-upload-form" class="hidden mb-4 p-4 bg-white rounded">
        <input type="file" id="photo-file-input" accept="image/*" class="mb-2">
        <input type="text" id="photo-caption-input" placeholder="Add a caption (optional)"
               class="w-full p-2 border rounded mb-2">
        <div class="flex gap-2">
            <button id="submit-photo-btn" class="bg-[#c1502e] text-white px-4 py-2 rounded">
                Upload
            </button>
            <button id="cancel-photo-btn" class="bg-gray-400 text-white px-4 py-2 rounded">
                Cancel
            </button>
        </div>
        <div id="upload-progress" class="hidden mt-2">
            <div class="w-full bg-gray-200 rounded">
                <div id="upload-progress-bar" class="bg-[#c1502e] h-2 rounded" style="width: 0%"></div>
            </div>
        </div>
    </div>

    <!-- Photo Gallery Grid -->
    <div id="photos-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- Photos will be loaded here -->
    </div>

    <!-- No photos message -->
    <div id="no-photos-message" class="text-center py-8 opacity-70">
        <p>No photos yet. Be the first to share a photo from this concert!</p>
    </div>
</div>
```

#### Photo Card Component
```html
<div class="photo-card border rounded overflow-hidden">
    <img src="{download_url}" alt="Concert photo" class="w-full cursor-pointer">
    <div class="p-3 bg-white">
        <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
                <img src="{user_photo}" class="w-8 h-8 rounded-full">
                <span class="font-bold">{user_name}</span>
            </div>
            <button class="delete-photo-btn hidden text-red-600">
                <i class="fas fa-trash"></i>
            </button>
        </div>
        <p class="text-sm">{caption}</p>
        <p class="text-xs opacity-70">{formatted_date}</p>
    </div>
</div>
```

## Data Export

### Updates to export_to_web.py

The export script is updated to include photo metadata in concert detail JSON files:

```python
# Get photos for this concert
photos_ref = db.collection('concert_photos')
photos_query = photos_ref.where('concert_id', '==', concert_id).order_by('uploaded_at', direction=firestore.Query.DESCENDING)
photos_docs = photos_query.stream()

photos = []
for photo_doc in photos_docs:
    photo_data = photo_doc.to_dict()
    photos.append({
        'id': photo_doc.id,
        'user_name': photo_data.get('user_name', ''),
        'user_photo': photo_data.get('user_photo', ''),
        'download_url': photo_data.get('download_url', ''),
        'uploaded_at': photo_data.get('uploaded_at', ''),
        'caption': photo_data.get('caption', ''),
        'file_type': photo_data.get('file_type', '')
    })

concert_detail['photos'] = photos
concert_detail['photo_count'] = len(photos)
```

### Exported JSON Structure

**concert_details/{id}.json** (updated)
```json
{
  "id": "1274",
  "date": "2024-01-15",
  "venue": "Madison Square Garden",
  "artists": [...],
  "songs": [...],
  "photos": [
    {
      "id": "abc123",
      "user_name": "Jason",
      "user_photo": "https://...",
      "download_url": "https://firebasestorage.googleapis.com/...",
      "uploaded_at": "2024-01-15T22:30:00Z",
      "caption": "Amazing show!",
      "file_type": "image/jpeg"
    }
  ],
  "photo_count": 1
}
```

## Deployment Workflow

### Manual Photo Management Workflow

1. **User uploads photo**:
   - Photo stored in Firebase Storage
   - Metadata saved to Firestore `concert_photos` collection
   - Photo appears immediately on concert page (real-time)

2. **Deployment (to update static site)**:
   ```bash
   ./deploy.sh
   ```
   OR manually trigger deployment:
   - Owner can trigger via Cloud Function
   - GitHub Actions runs export_to_web.py
   - Photos metadata exported to JSON files
   - Static site updated with photo data

3. **Photo deletion**:
   - User/owner deletes photo
   - Firestore document deleted
   - Storage file deleted via Cloud Function (optional trigger)
   - Next deployment updates static site

### Optional: Automatic Deployment on Photo Upload

If you want automatic deployment when photos are uploaded, add a Cloud Function:

```javascript
// functions/index.js (add this function)

exports.onPhotoUploaded = functions.firestore
  .document('concert_photos/{photoId}')
  .onCreate(async (snap, context) => {
    // Trigger deployment
    await triggerGitHubDeployment();
  });
```

## User Experience

### For Authenticated Users
1. Sign in with Google
2. Navigate to any concert page
3. Scroll to "Photos" section
4. Click "Upload Photo" button
5. Select image file (auto-resizes)
6. Optionally add caption
7. Click "Upload"
8. Photo appears in gallery immediately
9. Can delete own photos

### For Owner
- All capabilities of authenticated users
- Can delete any photo (not just own)
- Can bulk manage photos via Firestore console if needed

### For Anonymous Users
- Can view all photos
- Cannot upload photos
- Prompted to sign in if they try to upload

## Image Optimization

### Client-Side Resizing
- Maximum dimension: 1920px (width or height)
- Maintains aspect ratio
- Uses HTML5 Canvas API
- Quality: 0.9 (90%)

### Recommended Best Practices
- Accept only common image formats (JPG, PNG, WEBP, GIF)
- Compress images before upload
- 5MB file size limit enforced
- Progressive JPEG encoding for faster loading

### Future Enhancements (Optional)
- Server-side thumbnail generation using Cloud Functions
- Multiple size variants (thumbnail, medium, full)
- Image compression using Cloud Storage lifecycle
- Lazy loading for better performance
- Lightbox/modal for full-size viewing

## Performance Considerations

### Loading Strategy
- Photos loaded after main concert content
- Use lazy loading for off-screen images
- Limit initial display to 12 photos (load more button)
- Cache photo URLs in browser

### Storage Costs
- Firebase Storage free tier: 5GB storage, 1GB/day transfer
- Typical photo: 200-500KB after resizing
- ~10,000-25,000 photos fit in free tier
- ~2,000-5,000 photo views per day in free tier

## Testing Checklist

- [ ] Upload photo as authenticated user
- [ ] Upload photo without authentication (should prompt to sign in)
- [ ] Upload oversized image (should be resized)
- [ ] Upload unsupported file type (should show error)
- [ ] View photos on concert page
- [ ] Delete own photo
- [ ] Delete others' photos as owner
- [ ] View concert with no photos
- [ ] View concert with many photos
- [ ] Export data and verify photos in JSON
- [ ] Deploy and verify photos on static site
- [ ] Test photo gallery on mobile devices

## Troubleshooting

### Photo upload fails
- **Check**: User is authenticated
- **Check**: File size under 5MB
- **Check**: File type is supported
- **Check**: Storage rules are deployed
- **Check**: Browser console for errors

### Photos don't appear on static site
- **Check**: export_to_web.py includes photo export code
- **Check**: Run deployment after uploading photos
- **Check**: Verify JSON files contain photo data
- **Check**: Storage URLs are publicly accessible

### Storage rules errors
- **Check**: storage.rules file exists
- **Check**: Rules are deployed: `firebase deploy --only storage`
- **Check**: Bucket name matches in rules

### Large storage costs
- **Check**: Number of photos uploaded
- **Check**: Average file sizes
- **Check**: Storage usage in Firebase Console
- **Solution**: Implement photo limits per concert/user

## Cost Estimation

### Free Tier (Firebase Spark Plan)
- Storage: 5GB
- Downloads: 1GB/day
- Operations: 50k/day reads, 20k/day writes

### Typical Usage Scenarios

**Small site (1,200 concerts, 10 photos/concert average)**:
- Total photos: ~12,000
- Storage needed: ~3-6GB (at 250-500KB per photo)
- Downloads: ~10-50GB/month (at 100-500 views per photo per month)
- **Cost**: Within free tier limits

**Growing site (need to monitor)**:
- If exceeding free tier, upgrade to Blaze (pay-as-you-go)
- Storage: $0.026/GB per month
- Downloads: $0.12/GB
- Example: 20GB storage + 100GB downloads = ~$13/month

## Security Best Practices

1. **Authentication required** for uploads
2. **File size limits** enforced (5MB)
3. **File type validation** on client and server
4. **User ownership** verified for deletions
5. **Rate limiting** (consider adding Cloud Functions rate limiter)
6. **Content moderation** (consider manual review for public sites)

## Related Documentation

- [Firestore Schema](FIRESTORE_SCHEMA.md) - Updated with concert_photos collection
- [Deployment Guide](DEPLOYMENT.md) - How to deploy photo updates
- [Project Overview](PROJECT_OVERVIEW.md) - Overall architecture

## Migration Notes

### Enabling This Feature

1. Deploy storage rules: `firebase deploy --only storage`
2. Deploy Firestore rules: `firebase deploy --only firestore:rules`
3. Update firebase-config.js to include Storage
4. Add concert-photos.js module
5. Update concert.html and concert.js
6. Update export_to_web.py
7. Test photo upload functionality
8. Deploy website: `./deploy.sh`

### No Data Migration Needed
This is a new feature with no existing data to migrate.
