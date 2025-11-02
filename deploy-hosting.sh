#!/bin/bash
# Quick deploy for hosting-only changes (no data export needed)
# Use this when you've only changed HTML/CSS/JS files

echo "🚀 Quick Hosting Deploy"
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
    echo "⏳ Note: Service worker update will apply on next page load."
else
    echo "❌ Deploy failed!"
    exit 1
fi
