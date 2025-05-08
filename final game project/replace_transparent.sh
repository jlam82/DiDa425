#!/bin/bash

# Check for directory argument
if [ -z "$1" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

DIR="$1"

# Validate directory
if [ ! -d "$DIR" ]; then
  echo "Error: '$DIR' is not a valid directory."
  exit 1
fi

# Loop over PNG image files in directory
for filepath in "$DIR"/*.{png,PNG}; do
  # Skip if no matching files
  [ -e "$filepath" ] || continue

  # Use a temporary file to prevent issues with overwriting
  tmpfile=$(mktemp --suffix=".png")

  # Process image:
  # 1. Remove transparency by flattening onto black background
  # 2. Replace #3d2e33 with black using -fill and -opaque
  convert "$filepath" \
    -background black -alpha remove -alpha off \
    -fill black -opaque "#3d2e33" \
    -fill black -opaque "#483539" \
    -fill black -opaque "#21161a" \
    -fill black -opaque "#574549" \
    -fill black -opaque "#564347" \
    "$tmpfile"

  # Overwrite original file
  mv "$tmpfile" "$filepath"

  echo "Processed and replaced: $(basename "$filepath")"
done