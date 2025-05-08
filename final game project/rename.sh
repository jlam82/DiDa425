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

# Loop over files in directory
for filepath in "$DIR"/*; do
  filename=$(basename "$filepath")
  extension="${filename##*.}"

  # Extract number from filename
  number=$(echo "$filename" | grep -oE '[0-9]+')

  if [[ -n "$number" ]]; then
    # Preserve extension if one exists and not same as filename (e.g., no .txt)
    if [[ "$filename" == *.* && "$extension" != "$filename" ]]; then
      newname="${number}.${extension}"
    else
      newname="${number}"
    fi

    mv "$filepath" "$DIR/$newname"
  fi
done
