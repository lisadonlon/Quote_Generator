#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Define the source and destination for the credentials file
SECRET_PATH="/etc/secrets/credentials.json"
DEST_PATH="credentials.json"

# Check if the secret file exists at the Render path and copy it
if [ -f "$SECRET_PATH" ]; then
  echo "Secret file found at $SECRET_PATH. Copying to $DEST_PATH..."
  cp "$SECRET_PATH" "$DEST_PATH"
else
  echo "Waiting for secret file to be mounted..."
  # Wait loop as a fallback
  while [ ! -f "$DEST_PATH" ]; do
    sleep 1
  done
fi

echo "credentials.json is available. Starting Gunicorn..."
# Start Gunicorn and bind it to the host and port Render provides.
gunicorn --bind 0.0.0.0:$PORT app:app