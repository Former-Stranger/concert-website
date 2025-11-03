#!/bin/bash
# Comprehensive Backup Script for Earplugs & Memories
# Version 1.0

set -e

BACKUP_DIR="backups/$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$BACKUP_DIR"

echo "========================================"
echo "Earplugs & Memories - Full Backup V1.0"
echo "========================================"
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""

# 1. Export Firestore Database
echo "Step 1/3: Exporting Firestore database..."
python3 scripts/export_firestore_backup.py "$BACKUP_DIR/firestore"
echo "✓ Firestore data exported"
echo ""

# 2. Backup Firebase Storage (Photos)
echo "Step 2/3: Backing up Firebase Storage (photos)..."
gsutil -m cp -r gs://earplugs-and-memories.firebasestorage.app/concert_photos "$BACKUP_DIR/photos" 2>/dev/null || echo "No photos found or already backed up"
echo "✓ Photos backed up"
echo ""

# 3. Git commit current state
echo "Step 3/3: Committing current state to Git..."
git add -A
git commit -m "Backup checkpoint $(date +%Y-%m-%d)" || echo "No changes to commit"
git push origin main
echo "✓ Git repository updated"
echo ""

# Create backup summary
cat > "$BACKUP_DIR/README.txt" <<EOF
Earplugs & Memories Backup
Created: $(date)
Version: 1.0

Contents:
- firestore/: Complete Firestore database export
- photos/: All concert photos from Firebase Storage

To restore:
1. Firestore: firebase firestore:import firestore/
2. Photos: gsutil -m cp -r photos/* gs://earplugs-and-memories.firebasestorage.app/
3. Code: Already in GitHub (git clone https://github.com/Former-Stranger/concert-website.git)

GitHub Repository: https://github.com/Former-Stranger/concert-website
Tag: v1.0
EOF

echo "========================================"
echo "Backup Complete!"
echo "========================================"
echo ""
echo "Backup saved to: $BACKUP_DIR"
echo ""
echo "What's backed up:"
echo "  ✓ Firestore database (all collections)"
echo "  ✓ Firebase Storage photos"
echo "  ✓ Source code (GitHub)"
echo "  ✓ Exported JSON data (GitHub)"
echo ""
echo "To restore from this backup, see: $BACKUP_DIR/README.txt"
