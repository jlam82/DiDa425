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

# Counter for new filenames
count=1

# Loop over files in directory
for filepath in "$DIR"/*; do
  if [ -f "$filepath" ]; then
    extension="${filepath##*.}"
    filename=$(basename "$filepath")

    # If no extension, skip the dot
    if [[ "$filename" == *.* && "$extension" != "$filename" ]]; then
      newname="${count}.${extension}"
    else
      newname="${count}"
    fi

    mv "$filepath" "$DIR/$newname"
    ((count++))
  fi
done
