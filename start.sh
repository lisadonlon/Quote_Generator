#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for the credentials.json file to be available.
while [ ! -f credentials.json ]; do
  echo "Waiting for credentials.json to be mounted..."
  sleep 1
done

echo "credentials.json found. Starting Gunicorn..."
# Start Gunicorn and bind it to the host and port Render provides.
gunicorn --bind 0.0.0.0:$PORT app:app