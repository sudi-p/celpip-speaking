# CELPIP Speaking Practice App

A minimal MVP web app for practicing CELPIP-style speaking tasks. Pick a task, prepare, record your response, and get an AI-generated transcript and evaluation scored on the CELPIP 12-point scale.

## Stack

- **Frontend:** Vanilla HTML/CSS/JS (no framework, no build step)
- **Backend:** Django 5 + SQLite (proxy for Deepgram + OpenAI, persistence)

## Setup & Run

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate              # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                  # then edit with real keys
python manage.py migrate              # creates db.sqlite3 + Attempt table
python manage.py createsuperuser      # optional, for /admin/
python manage.py runserver 8000
```

### Frontend (new terminal)

```bash
cd frontend
python -m http.server 5500
# Open http://localhost:5500
```

`getUserMedia` works on `localhost` without HTTPS. Chrome recommended.

## Known Limitations

- Safari records in `audio/mp4` which Deepgram may reject. Use Chrome for v1.
- No auth — single-user local app. Trivially addable later.
- Audio blobs are not stored; only transcript + evaluation are persisted.

## API Keys Required

- **Deepgram** — speech-to-text: https://console.deepgram.com
- **OpenAI** — evaluation: https://platform.openai.com

Add both to `backend/.env` after copying from `.env.example`.
