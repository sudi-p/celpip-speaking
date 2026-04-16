import json
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Attempt, Session

TASK_NAMES = {
    1: "Giving Advice",
    2: "Personal Experience",
    3: "Describing a Scene",
    4: "Making Predictions",
    5: "Comparing & Persuading",
    6: "Difficult Situation",
    7: "Expressing Opinions",
    8: "Unusual Situation",
}

# Tasks where a scenario is inferred from the first transcript
SCENARIO_TASKS = {3, 4, 5, 8}

QUESTION_PROMPTS = {
    1: (
        "Write a single CELPIP Speaking Task 1 (Giving Advice) question. "
        "The format is: a friend or family member is in a realistic life situation and has asked the test-taker for advice. "
        "The scenario should involve a concrete everyday dilemma (e.g. job change, moving city, relationship, education). "
        "End with 'What advice would you give?' or similar. "
        "Write only the question text, no labels or explanations."
    ),
    2: (
        "Write a single CELPIP Speaking Task 2 (Describing a Personal Experience) question. "
        "The format is: ask the test-taker to talk about a specific personal memory or experience "
        "(e.g. a challenge they overcame, an important decision, a memorable event). "
        "Use natural prompting language such as 'Describe a time when…' or 'Talk about an experience where…'. "
        "Write only the question text, no labels or explanations."
    ),
    6: (
        "Write a single CELPIP Speaking Task 6 (Dealing with a Difficult Situation) question. "
        "The format is: place the test-taker in an awkward or stressful real-life scenario "
        "(e.g. a misunderstanding with a colleague, an unexpected problem at work or home, a conflict with a neighbour). "
        "Ask how they would handle it. "
        "Write only the question text, no labels or explanations."
    ),
    7: (
        "Write a single CELPIP Speaking Task 7 (Expressing an Opinion) question. "
        "The format is: present a debatable statement about society, technology, education, work, or lifestyle. "
        "Ask whether the test-taker agrees or disagrees, and to support their view with reasons. "
        "Write only the question text, no labels or explanations."
    ),
}

EVAL_SYSTEM_PROMPT = (
    "You are a certified CELPIP speaking examiner with strict but fair grading standards. "
    "Evaluate the candidate's spoken response using the official CELPIP 12-point scale. "

    "Scoring guide:\n"
    "Band 10–12:\n"
    "- Clear, fluent, and natural speech\n"
    "- Very few or no grammar errors\n"
    "- Well-structured, fully developed ideas\n"
    "- Strong vocabulary and smooth transitions\n\n"

    "Band 8–9:\n"
    "- Generally clear and easy to understand\n"
    "- Some grammar errors, but meaning is not affected\n"
    "- Good organization and relevant ideas\n"
    "- Adequate vocabulary and transitions\n\n"

    "Band 6–7:\n"
    "- Understandable but noticeable grammar issues\n"
    "- Some awkward phrasing or repetition\n"
    "- Ideas are somewhat basic or unevenly developed\n"
    "- Occasional clarity issues, but task is completed\n\n"

    "Band 4–5:\n"
    "- Frequent grammar errors\n"
    "- Meaning is sometimes unclear\n"
    "- Weak structure and limited vocabulary\n\n"

    "Band 1–3:\n"
    "- Very difficult to understand\n"
    "- Major grammar breakdowns\n"
    "- Incomplete or irrelevant response\n\n"

   "Evaluation rules:\n"
    "- Prioritize clarity, coherence, and task completion over grammar perfection.\n"
    "- Do NOT over-penalize minor grammar mistakes if the meaning is clear.\n"
    "- Score holistically; do not count errors mechanically.\n"
    "- If the response is clear, logically structured, and fully addresses the task, it should typically fall in Band 8–9.\n"
    "- Only assign Band 6–7 if grammar or phrasing issues noticeably affect fluency or naturalness.\n"
    "- Only assign Band 5 or below if there are real comprehension problems.\n\n"

    "Band decision rule:\n"
    "- When choosing between two bands (e.g., 7 vs 8), decide based on overall clarity and ease of understanding.\n"
    "- If the response is easy to follow despite errors, choose the higher band.\n"
    "- If errors interrupt flow or require effort to understand, choose the lower band.\n\n"

    "Consistency rule:\n"
    "- Responses with clear structure, relevant advice, and minor language issues should NOT be scored below 7.\n"
    "- Responses that are clear and natural with only occasional mistakes should be scored at least 8.\n\n"

    
    "Return ONLY a valid JSON object with these keys:\n"
    "score (integer 1-12),\n"
    "fluency (string),\n"
    "grammar (string),\n"
    "vocabulary (string),\n"
    "coherence (string),\n"
    "strengths (array of strings),\n"
    "weaknesses (array of strings — high-level weakness categories),\n"
    "transcript_issues (array of objects — detailed line-by-line issues found in the transcript; "
    "each object has: quote (the exact problematic phrase or sentence copied verbatim from the transcript), "
    "type (one of: Grammar, Vocabulary, Fluency, Coherence, Pronunciation-note), "
    "problem (concise explanation of what is wrong), "
    "fix (the corrected version of that phrase). "
    "Include ALL notable issues you find — aim for thoroughness, not brevity. "
    "If the transcript is strong, still include at least 2–3 minor issues.),\n"
    "improvements (array of strings),\n"
    "example_better_response (string).\n\n"

    "When a previous attempt transcript is provided, also include:\n"
    "comparison (object with keys: improvements (array of strings describing what the candidate did better "
    "than the previous attempt), regressions (array of strings describing what got worse or hurt the score "
    "compared to the previous attempt)). Reference specific language from both transcripts. "
    "If nothing clearly improved or regressed, use empty arrays.\n\n"

    "Be specific, constructive, and consistent with the rubric."
)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _openai_client():
    from openai import OpenAI
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def _audio_url(request, attempt):
    if attempt.audio_file:
        return request.build_absolute_uri(attempt.audio_file.url)
    return None


def _session_payload(s):
    return {
        "id": s.id,
        "name": s.name,
        "task_id": s.task_id,
        "task_name": s.task_name,
        "created_at": s.created_at.isoformat(),
        "question": s.question,
        "attempt_count": s.attempt_count,
        "avg_score": round(s.avg_score, 1) if s.avg_score is not None else None,
    }


def _deepgram_transcribe(audio_bytes, content_type):
    api_key = settings.DEEPGRAM_API_KEY
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY not configured")
    resp = requests.post(
        "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&punctuate=true",
        headers={"Authorization": f"Token {api_key}", "Content-Type": content_type},
        data=audio_bytes,
        timeout=30,
    )
    if not resp.ok:
        raise ValueError(f"Deepgram error {resp.status_code}: {resp.text[:200]}")
    try:
        return resp.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
    except (KeyError, IndexError):
        raise ValueError("Unexpected Deepgram response format")


def _openai_evaluate(task_id, task_name, transcript, duration_sec, question,
                     prev_transcript=None, session_summary=None):
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    question_line = f"Question given to candidate:\n{question}\n\n" if question else ""
    user_prompt = (
        f"CELPIP Speaking Task {task_id}: {task_name}\n\n"
        f"{question_line}"
        f"Candidate's response (duration: {duration_sec}s):\n{transcript}\n\n"
    )
    if session_summary:
        user_prompt += (
            f"Session history summary (candidate's patterns across all prior attempts in this session):\n"
            f"{session_summary}\n\n"
        )
    if prev_transcript:
        user_prompt += (
            f"Previous attempt transcript:\n{prev_transcript}\n\n"
            "Compare the current response to the previous attempt and include a 'comparison' key in your JSON."
        )
    else:
        user_prompt += "Provide your evaluation as a JSON object."

    completion = _openai_client().chat.completions.create(
        model="gpt-4o",
        temperature=0.4,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EVAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    evaluation = json.loads(completion.choices[0].message.content)
    required = {"score", "fluency", "grammar", "vocabulary", "coherence",
                "strengths", "weaknesses", "improvements", "example_better_response"}
    missing = required - evaluation.keys()
    if missing:
        raise ValueError(f"OpenAI response missing keys: {missing}")
    return evaluation


def _update_session_summary(session, transcript, score, evaluation):
    """Synthesize a rolling plain-text summary of all attempts in the session."""
    existing = session.response_summary.strip()
    attempt_num = session.attempts.count()  # already saved at this point
    strengths = "; ".join(evaluation.get("strengths", [])[:2])
    weaknesses = "; ".join(evaluation.get("weaknesses", [])[:2])
    new_entry = (
        f"Attempt {attempt_num} (score {score}/12): "
        f"Strengths — {strengths or 'none noted'}. "
        f"Weaknesses — {weaknesses or 'none noted'}."
    )
    if existing:
        prompt = (
            "You are summarizing a language learner's speaking practice session. "
            "Below is the running summary so far, followed by a new attempt entry. "
            "Produce a concise updated summary (max 120 words) that captures the candidate's "
            "overall patterns, recurring strengths, persistent weaknesses, and score trajectory.\n\n"
            f"Current summary:\n{existing}\n\n"
            f"New entry:\n{new_entry}\n\n"
            "Write only the updated summary, no labels."
        )
    else:
        prompt = (
            "You are summarizing a language learner's first speaking attempt in a practice session. "
            "Write a concise summary (max 60 words) capturing key strengths, weaknesses, and score. "
            f"\n\n{new_entry}\n\nWrite only the summary, no labels."
        )
    try:
        completion = _openai_client().chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        session.response_summary = completion.choices[0].message.content.strip()
        session.save(update_fields=["response_summary"])
    except Exception:
        pass  # Never fail the request over summary update


def _generate_scenario(task_id, task_name, transcript):
    """Infer a short topic description from the first transcript of tasks 3/4/5/8."""
    prompt = (
        f"A CELPIP test-taker just completed Speaking Task {task_id}: {task_name}. "
        f"Here is their response:\n\n{transcript}\n\n"
        "Based on this response, write a short scenario title (1–2 sentences, max 80 words) "
        "that describes the topic or scenario this person was likely responding to. "
        "Write it as a neutral topic description, not as a question. "
        "Example: 'The speaker described a busy outdoor market with food stalls and crowds on a summer afternoon.' "
        "Write only the scenario description, nothing else."
    )
    completion = _openai_client().chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content.strip()


# ── Session endpoints ─────────────────────────────────────────────────────────

@csrf_exempt
def sessions_list_create(request):
    if request.method == "GET":
        qs = Session.objects.annotate(
            attempt_count=Count("attempts"),
            avg_score=Avg("attempts__score"),
        )
        return JsonResponse([_session_payload(s) for s in qs], safe=False)

    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid JSON body"}, status=400)

        task_id = body.get("task_id")
        question = body.get("question", "").strip()

        if not task_id or task_id not in TASK_NAMES:
            return JsonResponse({"error": "Invalid task_id"}, status=400)

        task_name = TASK_NAMES[task_id]
        n = Session.objects.filter(task_id=task_id).count() + 1
        session = Session.objects.create(
            task_id=task_id,
            task_name=task_name,
            name=f"{task_name} — Session {n}",
            question=question,
        )
        return JsonResponse({
            "id": session.id,
            "name": session.name,
            "task_id": session.task_id,
            "task_name": session.task_name,
            "created_at": session.created_at.isoformat(),
            "question": session.question,
        }, status=201)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@require_http_methods(["GET"])
def latest_session(request):
    task_id = request.GET.get("task_id")
    if not task_id:
        return JsonResponse({"error": "task_id required"}, status=400)
    try:
        task_id = int(task_id)
    except ValueError:
        return JsonResponse({"error": "task_id must be an integer"}, status=400)

    session = (
        Session.objects
        .filter(task_id=task_id)
        .annotate(attempt_count=Count("attempts"), avg_score=Avg("attempts__score"))
        .first()
    )
    if not session:
        return JsonResponse({"error": "No session found"}, status=404)
    return JsonResponse(_session_payload(session))


@csrf_exempt
@require_http_methods(["GET"])
def session_detail(request, pk):
    try:
        session = (
            Session.objects
            .annotate(attempt_count=Count("attempts"), avg_score=Avg("attempts__score"))
            .get(pk=pk)
        )
    except Session.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    attempts = session.attempts.all()
    return JsonResponse({
        **_session_payload(session),
        "attempts": [
            {
                "id": a.id,
                "created_at": a.created_at.isoformat(),
                "score": a.score,
                "duration_sec": a.duration_sec,
                "transcript": a.transcript,
                "question": a.question,
                "user_name": a.user_name,
                "evaluation_json": a.evaluation_json,
                "audio_url": _audio_url(request, a),
            }
            for a in attempts
        ],
    })


# ── Submit (transcribe + evaluate + save audio + link to session) ─────────────

@csrf_exempt
@require_http_methods(["POST"])
def submit(request):
    task_id = request.POST.get("task_id")
    duration_sec = request.POST.get("duration_sec")
    question = request.POST.get("question", "").strip()
    session_id = request.POST.get("session_id", "").strip()
    user_name = request.POST.get("user_name", "").strip()
    audio = request.FILES.get("audio")

    if not task_id:
        return JsonResponse({"error": "task_id is required"}, status=400)
    try:
        task_id = int(task_id)
    except ValueError:
        return JsonResponse({"error": "task_id must be an integer"}, status=400)
    if task_id not in TASK_NAMES:
        return JsonResponse({"error": "Invalid task_id (must be 1-8)"}, status=400)
    if not audio:
        return JsonResponse({"error": "No audio file uploaded"}, status=400)

    # Resolve session
    session = None
    if session_id:
        try:
            session = Session.objects.get(pk=int(session_id))
            # Use session's question if caller didn't supply one
            if not question and session.question:
                question = session.question
        except (Session.DoesNotExist, ValueError):
            pass

    is_first_attempt = session is not None and session.attempts.count() == 0

    # Capture previous attempt for progress tracking and comparison
    prev_score = None
    prev_transcript = None
    session_summary = None
    if session and not is_first_attempt:
        last = session.attempts.order_by("-created_at").first()
        if last:
            prev_score = last.score
            prev_transcript = last.transcript or None
        if session.response_summary:
            session_summary = session.response_summary

    audio_bytes = audio.read()
    content_type = audio.content_type or "audio/webm"
    task_name = TASK_NAMES[task_id]

    try:
        transcript = _deepgram_transcribe(audio_bytes, content_type)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=502)
    except requests.RequestException as e:
        return JsonResponse({"error": f"Deepgram request failed: {e}"}, status=502)

    if not transcript.strip():
        return JsonResponse({"error": "Transcript is empty — please speak clearly and try again"}, status=400)

    try:
        evaluation = _openai_evaluate(
            task_id, task_name, transcript, duration_sec, question,
            prev_transcript=prev_transcript,
            session_summary=session_summary,
        )
    except Exception as e:
        return JsonResponse({"error": f"Evaluation failed: {e}"}, status=502)

    attempt = Attempt.objects.create(
        task_id=task_id,
        task_name=task_name,
        transcript=transcript,
        score=evaluation.get("score"),
        evaluation_json=evaluation,
        duration_sec=int(duration_sec) if duration_sec else None,
        question=question,
        user_name=user_name,
        session=session,
    )

    ext = "webm" if "webm" in content_type else "mp4"
    attempt.audio_file.save(f"attempt_{attempt.id}.{ext}", ContentFile(audio_bytes), save=True)

    # Update rolling session summary (async-safe: never blocks the response)
    if session:
        _update_session_summary(session, transcript, evaluation.get("score"), evaluation)

    # Infer scenario from first transcript for tasks 3/4/5/8
    session_question = None
    if is_first_attempt and task_id in SCENARIO_TASKS and not session.question:
        try:
            scenario = _generate_scenario(task_id, task_name, transcript)
            session.question = scenario
            session.save(update_fields=["question"])
            session_question = scenario
        except Exception:
            pass  # Don't fail the request if scenario inference fails

    return JsonResponse({
        "id": attempt.id,
        "transcript": transcript,
        "audio_url": _audio_url(request, attempt),
        "session_question": session_question,
        "prev_score": prev_score,
        **evaluation,
    })


# ── Legacy endpoints (kept for compatibility) ─────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def transcribe(request):
    audio_data = request.body
    if not audio_data:
        return JsonResponse({"error": "No audio data received"}, status=400)
    content_type = request.headers.get("X-Audio-Type", "audio/webm")
    try:
        transcript = _deepgram_transcribe(audio_data, content_type)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=502)
    except requests.RequestException as e:
        return JsonResponse({"error": f"Deepgram request failed: {e}"}, status=502)
    return JsonResponse({"transcript": transcript})


@csrf_exempt
@require_http_methods(["POST"])
def evaluate(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    task_id = body.get("task_id")
    transcript = body.get("transcript", "").strip()
    duration_sec = body.get("duration_sec")
    question = body.get("question", "").strip()

    if not task_id or task_id not in TASK_NAMES:
        return JsonResponse({"error": "Invalid task_id (must be 1-8)"}, status=400)
    if not transcript:
        return JsonResponse({"error": "Transcript is empty"}, status=400)

    task_name = TASK_NAMES[task_id]
    try:
        evaluation = _openai_evaluate(task_id, task_name, transcript, duration_sec, question)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=502)

    attempt = Attempt.objects.create(
        task_id=task_id, task_name=task_name, transcript=transcript,
        score=evaluation.get("score"), evaluation_json=evaluation,
        duration_sec=duration_sec, question=question,
    )
    return JsonResponse({"id": attempt.id, **evaluation})


@csrf_exempt
@require_http_methods(["POST"])
def generate_question(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    task_id = body.get("task_id")
    if task_id not in QUESTION_PROMPTS:
        return JsonResponse({"error": "Question generation is only available for tasks 1, 2, 6, and 7"}, status=400)
    if not settings.OPENAI_API_KEY:
        return JsonResponse({"error": "OPENAI_API_KEY not configured"}, status=500)

    try:
        completion = _openai_client().chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.9,
            messages=[{"role": "user", "content": QUESTION_PROMPTS[task_id]}],
        )
    except Exception as e:
        return JsonResponse({"error": f"OpenAI request failed: {e}"}, status=502)

    return JsonResponse({"question": completion.choices[0].message.content.strip()})


@csrf_exempt
@require_http_methods(["GET"])
def activity_logs(request):
    logs = []

    # Index first attempt per session to derive user_name for session_started events
    first_attempt_by_session = {}
    for a in Attempt.objects.filter(session__isnull=False).order_by("created_at"):
        if a.session_id not in first_attempt_by_session:
            first_attempt_by_session[a.session_id] = a

    for s in Session.objects.all():
        fa = first_attempt_by_session.get(s.id)
        logs.append({
            "type": "session_started",
            "timestamp": s.created_at.isoformat(),
            "session_id": s.id,
            "session_name": s.name,
            "task_id": s.task_id,
            "task_name": s.task_name,
            "user_name": fa.user_name if fa else "",
        })

    for a in Attempt.objects.select_related("session").all():
        logs.append({
            "type": "attempt_submitted",
            "timestamp": a.created_at.isoformat(),
            "session_id": a.session_id,
            "session_name": a.session.name if a.session else "",
            "task_id": a.task_id,
            "task_name": a.task_name,
            "attempt_id": a.id,
            "score": a.score,
            "user_name": a.user_name,
        })

    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    return JsonResponse(logs[:300], safe=False)


@csrf_exempt
@require_http_methods(["GET"])
def list_attempts(request):
    qs = Attempt.objects.all()[:100]
    return JsonResponse([
        {
            "id": a.id,
            "created_at": a.created_at.isoformat(),
            "task_id": a.task_id,
            "task_name": a.task_name,
            "score": a.score,
            "duration_sec": a.duration_sec,
            "question": a.question,
            "audio_url": _audio_url(request, a),
            "session_id": a.session_id,
        }
        for a in qs
    ], safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def reevaluate_attempt(request, pk):
    try:
        attempt = Attempt.objects.get(pk=pk)
    except Attempt.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    if not attempt.transcript.strip():
        return JsonResponse({"error": "No transcript to evaluate"}, status=400)

    old_score = attempt.score

    # Find the attempt that came just before this one in the same session
    prev_transcript = None
    session_summary = None
    if attempt.session_id:
        prev = (
            Attempt.objects
            .filter(session_id=attempt.session_id, created_at__lt=attempt.created_at)
            .order_by("-created_at")
            .first()
        )
        if prev and prev.transcript:
            prev_transcript = prev.transcript
        session = attempt.session
        if session and session.response_summary:
            session_summary = session.response_summary

    try:
        evaluation = _openai_evaluate(
            attempt.task_id,
            attempt.task_name,
            attempt.transcript,
            attempt.duration_sec,
            attempt.question,
            prev_transcript=prev_transcript,
            session_summary=session_summary,
        )
    except Exception as e:
        return JsonResponse({"error": f"Evaluation failed: {e}"}, status=502)

    attempt.score = evaluation.get("score")
    attempt.evaluation_json = evaluation
    attempt.save(update_fields=["score", "evaluation_json"])

    return JsonResponse({"id": attempt.id, "old_score": old_score, **evaluation})


@csrf_exempt
def attempt_detail(request, pk):
    try:
        attempt = Attempt.objects.get(pk=pk)
    except Attempt.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    if request.method == "GET":
        return JsonResponse({
            "id": attempt.id,
            "created_at": attempt.created_at.isoformat(),
            "task_id": attempt.task_id,
            "task_name": attempt.task_name,
            "transcript": attempt.transcript,
            "score": attempt.score,
            "evaluation_json": attempt.evaluation_json,
            "duration_sec": attempt.duration_sec,
            "question": attempt.question,
            "audio_url": _audio_url(request, attempt),
            "session_id": attempt.session_id,
        })
    elif request.method == "DELETE":
        attempt.delete()
        return JsonResponse({"ok": True})
    return JsonResponse({"error": "Method not allowed"}, status=405)
