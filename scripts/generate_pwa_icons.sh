#!/bin/bash
# Generate PWA icons from SVG favicon
# Requires: ImageMagick (brew install imagemagick)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ICONS_DIR="$PROJECT_ROOT/website/icons"
SVG_FILE="$PROJECT_ROOT/website/favicon.svg"

echo "🎨 Generating PWA Icons from favicon.svg"
echo "=========================================="

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "❌ ImageMagick not found. Install with: brew install imagemagick"
    echo ""
    echo "Alternative: Use an online tool to convert favicon.svg to PNG:"
    echo "  1. Visit https://realfavicongenerator.net/"
    echo "  2. Upload website/favicon.svg"
    echo "  3. Download generated icons"
    echo "  4. Extract to website/icons/"
    exit 1
fi

# Create icons directory
mkdir -p "$ICONS_DIR"

# Generate icons in various sizes
sizes=(72 96 128 144 152 192 384 512)

for size in "${sizes[@]}"; do
    echo "  Generating ${size}x${size}..."
    convert -background none -resize "${size}x${size}" "$SVG_FILE" "$ICONS_DIR/icon-${size}x${size}.png"
done

# Generate Apple Touch Icons
echo "  Generating apple-touch-icon-180x180..."
convert -background none -resize "180x180" "$SVG_FILE" "$ICONS_DIR/apple-touch-icon-180x180.png"

echo "  Generating apple-touch-icon-167x167..."
convert -background none -resize "167x167" "$SVG_FILE" "$ICONS_DIR/apple-touch-icon-167x167.png"

echo "  Generating apple-touch-icon-152x152..."
convert -background none -resize "152x152" "$SVG_FILE" "$ICONS_DIR/apple-touch-icon-152x152.png"

echo ""
echo "✅ Icons generated successfully!"
echo "📁 Location: $ICONS_DIR"
echo ""
echo "Generated icons:"
ls -lh "$ICONS_DIR"
