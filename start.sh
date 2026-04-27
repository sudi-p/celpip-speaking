#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv and start Django (serves both API and frontend)
echo "Starting server on http://localhost:8000 ..."
source venv/bin/activate
python manage.py runserver
