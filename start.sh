#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate venv and start Django (serves both API and frontend)
echo "Starting server on http://localhost:8000 ..."
cd "$SCRIPT_DIR"
venv/bin/python3 manage.py runserver 8000 &
SERVER_PID=$!

echo ""
echo "Server running. Open http://localhost:8000"
echo "Press Ctrl+C to stop."

trap "kill $SERVER_PID 2>/dev/null; echo 'Stopped.'" INT TERM
wait $SERVER_PID
