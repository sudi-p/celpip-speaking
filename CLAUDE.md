# CLAUDE.md — CELPIP Speaking Practice App

> Feed this file to Claude Code in VS Code and ask: **"Build the entire project as specified in CLAUDE.md."**

---

## Project Overview

Build a **minimal MVP web app** that lets a user practice CELPIP-style speaking tasks. The user picks 1 of 8 tasks, gets a preparation timer, records their spoken response in the browser, and receives an AI-generated transcript + evaluation scored on the CELPIP 12-point scale. **All attempts are persisted to SQLite** so the user can review past sessions.

**Stack:** Vanilla HTML/CSS/JS frontend + minimal Django backend (proxy + SQLite persistence).

**Why a backend?** OpenAI and Deepgram API keys cannot be safely exposed in frontend JavaScript. The Django backend exists to (1) hide API keys behind thin proxy endpoints and (2) persist attempts to SQLite. **No auth, kept as small as possible.**

---

## Architecture

```
Browser (HTML/CSS/JS)
   │
   │  1. MediaRecorder captures audio (webm)
   │  2. POST audio blob → /api/transcribe
   │  3. POST transcript → /api/evaluate    (saves Attempt to SQLite)
   │  4. GET /api/attempts                  (history page)
   │  5. GET /api/attempts/<id>             (detail view)
   ▼
Django Backend
   │
   ├─→ Deepgram API (speech-to-text)
   ├─→ OpenAI API   (CELPIP evaluation, JSON mode)
   └─→ SQLite       (Attempt model)
```

**Decisions:**

- Audio recording: ✅ Browser-native `MediaRecorder` + `getUserMedia`
- Deepgram/OpenAI from browser: ❌ would leak API keys → backend proxy
- DB: ✅ SQLite (zero-config, file-based, perfect for MVP) via Django ORM
- No auth: single-user local app for now; trivially addable later

---

## Project Structure (generate exactly this)

```
celpip-app/
├── README.md
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   ├── db.sqlite3                  # auto-created by migrate
│   └── celpip/
│       ├── __init__.py
│       ├── settings.py
│       ├── urls.py
│       ├── wsgi.py
│       ├── asgi.py
│       └── attempts/               # single Django app
│           ├── __init__.py
│           ├── apps.py
│           ├── models.py
│           ├── views.py
│           ├── urls.py
│           ├── admin.py
│           └── migrations/
│               └── __init__.py
└── frontend/
    ├── index.html                  # task picker
    ├── record.html                 # prep + record + result
    ├── history.html                # list of past attempts
    ├── detail.html                 # single attempt detail
    ├── styles.css
    └── app.js                      # shared module: timing, fetch helpers, render
```

---

## CELPIP Task Specification

Exact timings — **do not change these**:

| Task | Name                   | Prep (s) | Speak (s) |
| ---- | ---------------------- | -------- | --------- |
| 1    | Giving Advice          | 30       | 90        |
| 2    | Personal Experience    | 30       | 60        |
| 3    | Describing a Scene     | 30       | 60        |
| 4    | Making Predictions     | 30       | 60        |
| 5    | Comparing & Persuading | 60       | 60        |
| 6    | Difficult Situation    | 60       | 60        |
| 7    | Expressing Opinions    | 30       | 60        |
| 8    | Unusual Situation      | 30       | 60        |

Define a `TASKS` constant on both frontend (`app.js`) and backend (`attempts/views.py`) — keep them in sync.

---

## Data Model (SQLite via Django ORM)

Single model in `backend/celpip/attempts/models.py`:

```python
class Attempt(models.Model):
    created_at      = models.DateTimeField(auto_now_add=True, db_index=True)
    task_id         = models.IntegerField()                # 1–8
    task_name       = models.CharField(max_length=100)
    transcript      = models.TextField(blank=True)
    score           = models.IntegerField(null=True, blank=True)   # 1–12
    evaluation_json = models.JSONField(null=True, blank=True)      # full OpenAI response
    duration_sec    = models.IntegerField(null=True, blank=True)   # actual recording length

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Task {self.task_id} — {self.score or '?'}/12 — {self.created_at:%Y-%m-%d %H:%M}"
```

**Why JSONField for evaluation?** SQLite 3.9+ supports JSON natively, Django serializes/deserializes for free, and we avoid creating 8 columns for a structure we mainly read whole.

**No audio storage.** Keeping audio blobs in SQLite (or even on disk) bloats the MVP. Add later if needed.

---

## Backend Endpoints

All under `/api/`. CSRF exempt (no auth, local MVP). All return JSON.

| Method | Path                     | Purpose                                                                                                      |
| ------ | ------------------------ | ------------------------------------------------------------------------------------------------------------ |
| POST   | `/api/transcribe`        | Body = raw audio bytes; returns `{transcript}`                                                               |
| POST   | `/api/evaluate`          | Body = `{task_id, transcript, duration_sec}`; calls OpenAI, **saves Attempt**, returns `{id, ...evaluation}` |
| GET    | `/api/attempts`          | Returns `[{id, created_at, task_id, task_name, score}, ...]` (list view)                                     |
| GET    | `/api/attempts/<int:id>` | Returns full attempt incl. transcript + evaluation_json                                                      |
| DELETE | `/api/attempts/<int:id>` | Deletes one attempt                                                                                          |

**Transcription is NOT persisted** until `/api/evaluate` is called — keeps DB clean of failed/abandoned attempts.

---

## Frontend Pages

### `index.html` — Task Picker

- Grid of 8 buttons (Task 1 → Task 8) with name underneath
- Header link: **"View History →"** to `history.html`
- Click → `record.html?task=<id>`

### `record.html` — Recording Flow

- Reads `?task=` from URL
- Shows task name + phase ("Preparation" → "Recording" → "Processing")
- Big timer (mm:ss), tabular-nums
- Single button morphs: **"Start Preparation"** → (auto) → **"Stop Early"** → disabled
- After audio is processed:
  - Shows transcript in a panel
  - Shows evaluation: score badge + sections (fluency, grammar, vocabulary, coherence, strengths, weaknesses, improvements, example better response)
  - Shows two buttons: **"Try Again"** (reload) and **"View in History"** (link to `detail.html?id=<new_id>`)

### `history.html` — Past Attempts

- Fetches `/api/attempts`
- Renders a table/list: date, task, score badge, "View" link, "Delete" button
- Empty state: "No attempts yet — go practice!"

### `detail.html` — Single Attempt

- Reads `?id=` from URL
- Fetches `/api/attempts/<id>`
- Renders same layout as record.html result section, plus metadata (date, duration)
- Back link to `history.html`

---

## File Specifications

### `backend/requirements.txt`

```
django>=5.0
django-cors-headers>=4.3
requests>=2.31
python-dotenv>=1.0
openai>=1.50
```

### `backend/.env.example`

```
DEEPGRAM_API_KEY=your_deepgram_key_here
OPENAI_API_KEY=your_openai_key_here
```

### `backend/.gitignore`

```
venv/
__pycache__/
*.pyc
.env
db.sqlite3
```

### `backend/celpip/settings.py`

- `DEBUG = True`, `ALLOWED_HOSTS = ["*"]`
- `INSTALLED_APPS`: `django.contrib.contenttypes`, `django.contrib.auth`, `django.contrib.admin`, `django.contrib.sessions`, `django.contrib.messages`, `django.contrib.staticfiles`, `corsheaders`, `celpip.attempts`
- Middleware: include `corsheaders.middleware.CorsMiddleware` first, then standard Django middleware needed for admin
- `CORS_ALLOW_ALL_ORIGINS = True` (dev only)
- `DATABASES`: default SQLite at `BASE_DIR / "db.sqlite3"`
- Load `.env` via `python-dotenv` and expose `DEEPGRAM_API_KEY`, `OPENAI_API_KEY` as module attrs
- `ROOT_URLCONF = "celpip.urls"`

### `backend/celpip/urls.py`

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("celpip.attempts.urls")),
]
```

### `backend/celpip/attempts/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path("transcribe", views.transcribe),
    path("evaluate", views.evaluate),
    path("attempts", views.list_attempts),
    path("attempts/<int:pk>", views.attempt_detail),
]
```

### `backend/celpip/attempts/views.py`

Implement these functions, all `@csrf_exempt`:

- **`transcribe(request)`** — POST only. Reads `request.body`, sends to Deepgram `https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&punctuate=true` with `Authorization: Token <key>` and `Content-Type` from `X-Audio-Type` header (default `audio/webm`). Returns `{"transcript": "..."}`. On Deepgram failure return 502 with detail.

- **`evaluate(request)`** — POST only. Parses JSON `{task_id, transcript, duration_sec}`. Validates transcript non-empty. Calls OpenAI `gpt-4o-mini` with `response_format={"type": "json_object"}`, temperature 0.4. System prompt: "You are a certified CELPIP speaking examiner..." User prompt asks for JSON with keys: `score` (int 1-12), `fluency`, `grammar`, `vocabulary`, `coherence`, `strengths` (list), `weaknesses` (list), `improvements` (list), `example_better_response`. Parses response, **creates `Attempt` row**, returns `{"id": attempt.id, **evaluation}`.

- **`list_attempts(request)`** — GET only. Returns list of `{id, created_at (ISO), task_id, task_name, score, duration_sec}` ordered newest first. Limit 100.

- **`attempt_detail(request, pk)`** — GET returns full attempt including `transcript` and `evaluation_json`. DELETE removes it. 404 if not found.

Keep `TASK_NAMES` dict at top of file for `task_name` lookup.

### `backend/celpip/attempts/admin.py`

Register `Attempt` with `list_display = ("id", "created_at", "task_id", "score")` for free admin UI at `/admin/`.

### `backend/celpip/attempts/apps.py`

Standard `AppConfig` with `name = "celpip.attempts"`.

### `backend/manage.py` and `backend/celpip/wsgi.py`

Standard Django boilerplate pointing to `celpip.settings`.

---

### `frontend/app.js`

Shared module with:

```js
const API = "http://localhost:8000/api";

const TASKS = {
  1: { name: "Giving Advice", prep: 30, speak: 90 },
  2: { name: "Personal Experience", prep: 30, speak: 60 },
  3: { name: "Describing a Scene", prep: 30, speak: 60 },
  4: { name: "Making Predictions", prep: 30, speak: 60 },
  5: { name: "Comparing & Persuading", prep: 60, speak: 60 },
  6: { name: "Difficult Situation", prep: 60, speak: 60 },
  7: { name: "Expressing Opinions", prep: 30, speak: 60 },
  8: { name: "Unusual Situation", prep: 30, speak: 60 },
};

// Helpers (export via window.* since no bundler):
//   fmtTime(s), escapeHtml(s), countdown(seconds, onTick, onDone)
//   renderEvaluation(containerEl, evalObj)
//   apiGet(path), apiPost(path, body, isBlob), apiDelete(path)
```

Page-specific code is inline in each HTML via `<script>` blocks that use these helpers.

### `frontend/index.html`

- Renders 8 task cards from `TASKS` into `#task-grid`
- Top-right link: `<a href="history.html">View History →</a>`

### `frontend/record.html`

- Reads `?task=` param
- Phase machine: `idle → prep → recording → processing → done`
- On `done`: render transcript + evaluation; show "Try Again" + "View in History" buttons (using returned `id`)

### `frontend/history.html`

- On load, `apiGet("/attempts")`, render rows with View/Delete buttons
- Score badge color-coded (≥10 green, 7–9 amber, ≤6 red — keep it simple)

### `frontend/detail.html`

- On load, read `?id=`, `apiGet("/attempts/" + id)`, render

### `frontend/styles.css`

- Clean light theme: `#f6f7f9` background, `#4f46e5` primary
- `.task-card`, `.timer`, `.panel`, `.score-badge`, `.eval-section h3`
- `.score-badge.good`, `.score-badge.mid`, `.score-badge.low` for history coloring
- Mobile-friendly (single column under 600px)

---

## Setup & Run Instructions (include in `README.md`)

```bash
# --- Backend ---
cd backend
python -m venv venv
source venv/bin/activate              # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                  # then edit with real keys
python manage.py migrate              # creates db.sqlite3 + Attempt table
python manage.py createsuperuser      # optional, for /admin/
python manage.py runserver 8000

# --- Frontend (new terminal) ---
cd frontend
python -m http.server 5500
# Open http://localhost:5500
```

`getUserMedia` works on `localhost` without HTTPS. Chrome recommended.

---

## Implementation Rules for Claude Code

1. **Generate every file listed above.** Don't skip the migration folder's `__init__.py`.
2. **Run `python manage.py makemigrations attempts && python manage.py migrate`** as a final step (or instruct the user to).
3. **Keep it minimal** — no DRF, no serializers library, no class-based views. Plain function views + `JsonResponse`.
4. **No frontend frameworks, no build step.** Plain `<script src="app.js">`.
5. **Error handling:** every API call wrapped in try/except returning `JsonResponse({"error": ...}, status=...)`. Frontend shows errors inline, not `alert()` (except for mic permission).
6. **CSRF exempt all `/api/` views** with `@csrf_exempt` — no auth surface to protect.
7. **Audio MIME:** default to `audio/webm`. Don't try to handle Safari's `audio/mp4` in v1; note it as a known limitation in the README.
8. **Don't persist failed evaluations.** Only create `Attempt` after OpenAI returns valid JSON.
9. **JSON mode for OpenAI** is mandatory (`response_format={"type": "json_object"}`) — parse with `json.loads`, fail loud if invalid.
10. **Comment sparingly.** Only where intent isn't obvious. No tutorial-style narration.

---

## Stretch (do NOT build unless asked)

- Auth (Django sessions + login page)
- Audio file storage (FileField + MEDIA_ROOT)
- Per-task statistics dashboard (avg score, attempts over time)
- Beep sound between prep and recording phases
- Export attempts as CSV/JSON
- Re-evaluate an existing attempt with a different model

---

## Acceptance Checklist

- [ ] `python manage.py runserver` starts without errors
- [ ] `/admin/` loads and shows the Attempts table
- [ ] Task picker renders 8 cards
- [ ] Recording flow: prep timer → auto-start recording → auto-stop → transcript appears → evaluation appears
- [ ] New row appears in `/admin/` after each completed evaluation
- [ ] `history.html` lists all attempts newest-first
- [ ] `detail.html` shows full transcript + evaluation for any attempt
- [ ] Delete button removes attempt and refreshes list
- [ ] App works end-to-end with real Deepgram + OpenAI keys
