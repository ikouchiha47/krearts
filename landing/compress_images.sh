#!/bin/bash

# Convert PNG images to WebP format for better compression

cd "$(dirname "$0")/assets"

echo "Converting images to WebP format..."
echo "Original PNG sizes:"
ls -lh *.png
echo ""

for img in *.png; do
    if [ -f "$img" ]; then
        base="${img%.png}"
        echo "Converting $img to $base.webp..."
        # Convert to WebP with quality 80, resize to max 1200px width
        magick "$img" -strip -resize '1200x1200>' -quality 80 "$base.webp"
        echo "✓ $base.webp created"
    fi
done

echo ""
echo "Conversion complete!"
echo ""
echo "WebP sizes:"
ls -lh *.webp
echo ""
echo "To use WebP images, update your HTML to use .webp extensions"
