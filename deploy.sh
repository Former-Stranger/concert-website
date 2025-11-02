#!/bin/bash
# Simple one-click deploy script
# Run this after approving setlists to update the website

echo "🚀 Deploying Concert Archive Updates"
echo "======================================="
echo ""

# Update cache-busting version numbers
echo "🔄 Updating cache version..."
python3 scripts/update_cache_version.py

if [ $? -ne 0 ]; then
    echo "❌ Cache version update failed!"
    exit 1
fi

echo ""
# Export data from Firestore
echo "📊 Exporting data from Firestore..."
export GOOGLE_CLOUD_PROJECT=earplugs-and-memories
python3 scripts/export_to_web.py

if [ $? -ne 0 ]; then
    echo "❌ Export failed!"
    exit 1
fi

echo ""
echo "🧹 Clearing Firebase CLI cache..."
rm -rf .firebase/hosting*.cache
echo "✓ Cache cleared"

echo ""
echo "🌐 Deploying to Firebase Hosting..."
firebase deploy --only hosting --force

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deploy complete! Your website is updated."
    echo "🔗 https://earplugs-and-memories.web.app"
    echo ""
    echo "⏳ Note: Firebase CDN cache may take 10-30 seconds to propagate."
    echo "   Clear your browser cache to see changes immediately."
    echo "   (DevTools → Right-click refresh → Empty Cache and Hard Reload)"
else
    echo "❌ Deploy failed!"
    exit 1
fi
