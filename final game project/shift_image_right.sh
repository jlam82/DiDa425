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

# Loop over PNG files in the directory
for filepath in "$DIR"/*.{png,PNG}; do
  [ -e "$filepath" ] || continue

  filename=$(basename "$filepath")
  name="${filename%.*}"

  # Check if the filename is an even number
  if [[ "$name" =~ ^[0-9]+$ ]]; then
    if (( name % 2 == 0 )); then
      width=$(identify -format "%w" "$filepath")
      height=$(identify -format "%h" "$filepath")

      tmpfile=$(mktemp --suffix=".png")

convert \
  \( -size ${width}x${height} canvas:black \) \
  "$filepath" \
  -geometry +8+0 -compose Over -composite \
  -crop ${width}x${height}+0+0 +repage \
  "$tmpfile"

      mv "$tmpfile" "$filepath"
      echo "Shifted right: $filename"
    else
      echo "Skipped (odd-numbered): $filename"
    fi
  else
    echo "Skipped (non-numeric filename): $filename"
  fi
done
