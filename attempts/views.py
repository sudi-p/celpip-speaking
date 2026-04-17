import json
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Attempt, Question, Session

TASK_NAMES = {
    1: "Giving Advice",
    2: "Personal Experience",
    3: "Describing a Scene",
    4: "Making Predictions",
    5: "Comparing & Persuading",
    6: "Difficult Situation",
    7: "Expressing Opinions",
    8: "Unusual Situation",
    9: "Writing Task 1",
    10: "Writing Task 2",
}

WRITING_TASKS = {9, 10}

# Tasks where a scenario is inferred from the first transcript
SCENARIO_TASKS = {3, 4, 5, 8}

_TASK1_DOMAINS = (
    "finances, health, career change, starting a business, returning to school, "
    "parenting, aging parents, immigration, housing, marriage, friendship conflict, "
    "fitness goals, social media habits, volunteering, learning a new skill, "
    "dealing with a difficult coworker, managing debt, adopting a pet, "
    "long-distance relationship, work-life balance, retirement planning"
)

_TASK2_DOMAINS = (
    "overcoming fear, dealing with failure, unexpected kindness from a stranger, "
    "learning something the hard way, a time you changed your mind, "
    "a difficult conversation you had, a risk that paid off, "
    "adapting to a new culture or city, a mentor who influenced you, "
    "a moment you felt proud, handling an embarrassing situation, "
    "a time you had to make a quick decision, working on a team challenge"
)

_TASK6_DOMAINS = (
    "billing dispute with a service provider, misunderstanding with a landlord, "
    "conflict with a classmate over a group project, a neighbour complaint, "
    "receiving incorrect information from an official, a coworker taking credit for your work, "
    "being double-charged at a store, a miscommunication with a manager, "
    "a damaged package delivery, being left off an important email chain, "
    "a scheduling conflict with a client, noise complaint in an apartment building"
)

_TASK7_TOPICS = (
    "mandatory physical education in high school, four-day work weeks, "
    "banning single-use plastics, social media age limits, "
    "remote work as a permanent option, public surveillance cameras, "
    "gap years before university, universal basic income, "
    "smartphones in classrooms, electric vehicles replacing gas cars, "
    "standardized testing in schools, free public transit in cities"
)

_WRITING1_SCENARIOS = (
    "workplace complaint, noise complaint to a landlord, requesting a refund, "
    "apologizing to a client, inviting a colleague to an event, "
    "inquiring about a community program, requesting a schedule change from a manager, "
    "reporting a billing error to a utility company, asking a professor for an extension, "
    "thanking a volunteer coordinator, following up on a job application, "
    "reporting a safety concern to building management"
)

_WRITING2_TOPICS = (
    "screen time limits for adults, mandatory volunteering in schools, "
    "open-plan offices vs. private workspaces, reducing car use in cities, "
    "online shopping vs. local businesses, homework policies in elementary school, "
    "universal healthcare funding, social media's effect on self-esteem, "
    "merit-based vs. seniority-based promotions, reducing meat consumption, "
    "retraining programs for workers displaced by automation"
)

QUESTION_PROMPTS = {
    1: (
        "Write a single CELPIP Speaking Task 1 (Giving Advice) question. "
        "A friend or family member is in a realistic life situation and has asked the test-taker for advice. "
        f"Choose a domain randomly from this list and build a unique, specific scenario around it: {_TASK1_DOMAINS}. "
        "Do NOT use job offers in another city or any scenario about moving for work — those are overused. "
        "End with 'What advice would you give?' or a natural equivalent. "
        "Write only the question text, no labels or explanations."
    ),
    2: (
        "Write a single CELPIP Speaking Task 2 (Describing a Personal Experience) question. "
        "Ask the test-taker to talk about a specific personal memory or experience. "
        f"Pick a fresh angle from this list: {_TASK2_DOMAINS}. "
        "Use natural prompting language such as 'Describe a time when…' or 'Talk about an experience where…'. "
        "Each question must feel distinct — avoid generic prompts about 'a challenge' or 'an important decision'. "
        "Write only the question text, no labels or explanations."
    ),
    6: (
        "Write a single CELPIP Speaking Task 6 (Dealing with a Difficult Situation) question. "
        "Place the test-taker in an awkward or stressful real-life scenario and ask how they would handle it. "
        f"Draw from this list of domains: {_TASK6_DOMAINS}. "
        "Be specific — name a concrete situation, not a vague one. "
        "Write only the question text, no labels or explanations."
    ),
    7: (
        "Write a single CELPIP Speaking Task 7 (Expressing an Opinion) question. "
        "Present a debatable statement and ask whether the test-taker agrees or disagrees, with reasons. "
        f"Pick one topic from this list: {_TASK7_TOPICS}. "
        "Rotate through topics — do not keep returning to technology or education. "
        "Write only the question text, no labels or explanations."
    ),
    9: (
        "Write a single CELPIP Writing Task 1 (Email) question. "
        "The test-taker must write a formal or semi-formal email of approximately 150–200 words. "
        f"Build a scenario around one of these: {_WRITING1_SCENARIOS}. "
        "Start with 1–2 sentences beginning with 'You are...' to set the context, "
        "then include 3–4 bullet points of key information to address. "
        "Vary the scenario — do not reuse workplaces or landlord disputes repeatedly. "
        "Write only the task text, with no labels, no word count instructions, and no extra explanations."
    ),
    10: (
        "Write a single CELPIP Writing Task 2 (Survey Response) question. "
        "The test-taker must write approximately 150–200 words expressing an opinion. "
        "Begin with 1–2 survey-style context sentences, then ask a clear opinion question. "
        f"Pick a topic from this varied list: {_WRITING2_TOPICS}. "
        "Rotate topics — avoid reusing technology or environment themes back-to-back. "
        "Do not include bullet-point prompts, structure guidance, or word count instructions. "
        "Write only the task text, no labels, no formatting guidance."
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

WRITING_EVAL_SYSTEM_PROMPT = (
    "You are a certified CELPIP writing examiner with strict but fair grading standards. "
    "Evaluate the candidate's written response using the official CELPIP 12-point scale.\n\n"

    "CELPIP Writing Task 1 is a formal or semi-formal email (~150–200 words). "
    "CELPIP Writing Task 2 is a written opinion or survey response (~150–200 words).\n\n"

    "Scoring guide:\n"
    "Band 10–12: Fully addresses all required points; excellent organization; wide vocabulary range; "
    "very few grammar errors; natural, fluent prose.\n"
    "Band 8–9: Adequately addresses the task; generally well-organized; good vocabulary; "
    "some grammar errors that do not impede understanding.\n"
    "Band 6–7: Partially addresses the task; basic organization; limited but adequate vocabulary; "
    "noticeable grammar errors that occasionally affect clarity.\n"
    "Band 4–5: Partially addresses the task; weak organization; restricted vocabulary; "
    "frequent errors that impede understanding.\n"
    "Band 1–3: Barely addresses the task; very weak or no organization; very restricted vocabulary; "
    "pervasive errors that severely impede understanding.\n\n"

    "Evaluation rules:\n"
    "- Task Fulfillment is the primary criterion — verify ALL required bullet points are addressed.\n"
    "- Grade holistically; do not count errors mechanically.\n"
    "- A clear, organized response that addresses all points should typically be Band 8–9.\n"
    "- Only deduct to Band 6–7 if grammar issues noticeably affect readability or task completion.\n\n"

    "Return ONLY a valid JSON object with these keys:\n"
    "score (integer 1–12),\n"
    "content (string — assessment of ideas, development, and coherence),\n"
    "grammar (string — assessment of grammatical accuracy),\n"
    "vocabulary (string — assessment of vocabulary range and precision),\n"
    "readability (string — assessment of organization, sentence variety, and overall flow),\n"
    "task_fulfillment (string — how well the candidate addressed all required points in the prompt),\n"
    "strengths (array of strings),\n"
    "weaknesses (array of strings — high-level weakness categories),\n"
    "text_issues (array of objects — detailed issues found in the written response; "
    "each object has: quote (exact problematic phrase copied verbatim from the response), "
    "type (one of: Grammar, Vocabulary, Readability, Coherence), "
    "problem (concise explanation of what is wrong), "
    "fix (the corrected version of that phrase). "
    "Include ALL notable issues — aim for thoroughness. "
    "If the response is strong, still include at least 2–3 minor improvements.),\n"
    "improvements (array of strings),\n"
    "example_better_response (string).\n\n"

    "When a previous attempt response is provided, also include:\n"
    "comparison (object with keys: improvements (array of strings describing what the candidate did better), "
    "regressions (array of strings describing what got worse)). "
    "Reference specific language from both responses. "
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


def _openai_evaluate_writing(task_id, task_name, response_text, duration_sec, question,
                              prev_response=None, session_summary=None):
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    word_count = len(response_text.split())
    question_line = f"Task prompt given to candidate:\n{question}\n\n" if question else ""
    user_prompt = (
        f"CELPIP {task_name}\n\n"
        f"{question_line}"
        f"Candidate's written response ({word_count} words):\n{response_text}\n\n"
    )
    if session_summary:
        user_prompt += (
            f"Session history summary (candidate's patterns across prior attempts):\n"
            f"{session_summary}\n\n"
        )
    if prev_response:
        user_prompt += (
            f"Previous attempt response:\n{prev_response}\n\n"
            "Compare the current response to the previous attempt and include a 'comparison' key in your JSON."
        )
    else:
        user_prompt += "Provide your evaluation as a JSON object."

    completion = _openai_client().chat.completions.create(
        model="gpt-4o",
        temperature=0.4,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": WRITING_EVAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    evaluation = json.loads(completion.choices[0].message.content)
    required = {"score", "content", "grammar", "vocabulary", "readability",
                "task_fulfillment", "strengths", "weaknesses", "improvements", "example_better_response"}
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
        task_type = "writing" if task_id in WRITING_TASKS else "speaking"
        n = Session.objects.filter(task_id=task_id).count() + 1

        question_ref = None
        if question:
            question_ref, _ = Question.objects.get_or_create(
                task_id=task_id,
                text=question,
                defaults={"task_name": task_name, "task_type": task_type, "source": "manual"},
            )

        session = Session.objects.create(
            task_id=task_id,
            task_name=task_name,
            task_type=task_type,
            name=f"{task_name} — Session {n}",
            question=question,
            question_ref=question_ref,
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
        "task_type": session.task_type,
        "attempts": [
            {
                "id": a.id,
                "created_at": a.created_at.isoformat(),
                "score": a.score,
                "duration_sec": a.duration_sec,
                "task_type": a.task_type,
                "transcript": a.transcript,
                "response_text": a.response_text,
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


# ── Writing submit ────────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def submit_writing(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    task_id    = body.get("task_id")
    question   = body.get("question", "").strip()
    response_text = body.get("response_text", "").strip()
    duration_sec  = body.get("duration_sec")
    session_id    = body.get("session_id", "")
    user_name     = body.get("user_name", "").strip()

    if not task_id:
        return JsonResponse({"error": "task_id is required"}, status=400)
    try:
        task_id = int(task_id)
    except (ValueError, TypeError):
        return JsonResponse({"error": "task_id must be an integer"}, status=400)
    if task_id not in WRITING_TASKS:
        return JsonResponse({"error": "Invalid task_id for writing (must be 9 or 10)"}, status=400)
    if not response_text:
        return JsonResponse({"error": "Response text is empty"}, status=400)

    session = None
    if session_id:
        try:
            session = Session.objects.get(pk=int(session_id))
            if not question and session.question:
                question = session.question
        except (Session.DoesNotExist, ValueError):
            pass

    prev_score    = None
    prev_response = None
    session_summary = None
    if session and session.attempts.count() > 0:
        last = session.attempts.order_by("-created_at").first()
        if last:
            prev_score = last.score
            if last.response_text:
                prev_response = last.response_text
        if session.response_summary:
            session_summary = session.response_summary

    task_name = TASK_NAMES[task_id]

    try:
        evaluation = _openai_evaluate_writing(
            task_id, task_name, response_text, duration_sec, question,
            prev_response=prev_response,
            session_summary=session_summary,
        )
    except Exception as e:
        return JsonResponse({"error": f"Evaluation failed: {e}"}, status=502)

    attempt = Attempt.objects.create(
        task_id=task_id,
        task_name=task_name,
        task_type="writing",
        response_text=response_text,
        score=evaluation.get("score"),
        evaluation_json=evaluation,
        duration_sec=int(duration_sec) if duration_sec else None,
        question=question,
        user_name=user_name,
        session=session,
    )

    if session:
        _update_session_summary(session, response_text, evaluation.get("score"), evaluation)

    return JsonResponse({
        "id": attempt.id,
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
        return JsonResponse({"error": "Question generation is not available for this task"}, status=400)
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

    text = completion.choices[0].message.content.strip()
    task_name = TASK_NAMES[task_id]
    task_type = "writing" if task_id in WRITING_TASKS else "speaking"
    Question.objects.get_or_create(
        task_id=task_id,
        text=text,
        defaults={"task_name": task_name, "task_type": task_type, "source": "ai"},
    )
    return JsonResponse({"question": text})


@csrf_exempt
@require_http_methods(["GET"])
def list_questions(request):
    qs = Question.objects.all()
    return JsonResponse([
        {
            "id": q.id,
            "task_id": q.task_id,
            "task_name": q.task_name,
            "task_type": q.task_type,
            "text": q.text,
            "source": q.source,
            "created_at": q.created_at.isoformat(),
        }
        for q in qs
    ], safe=False)


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
            "task_type": a.task_type,
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

    is_writing = attempt.task_type == "writing"
    response_content = attempt.response_text if is_writing else attempt.transcript

    if not response_content.strip():
        return JsonResponse({"error": "No response to evaluate"}, status=400)

    old_score = attempt.score

    prev_content = None
    session_summary = None
    if attempt.session_id:
        prev = (
            Attempt.objects
            .filter(session_id=attempt.session_id, created_at__lt=attempt.created_at)
            .order_by("-created_at")
            .first()
        )
        if prev:
            prev_content = prev.response_text if is_writing else prev.transcript
        session = attempt.session
        if session and session.response_summary:
            session_summary = session.response_summary

    try:
        if is_writing:
            evaluation = _openai_evaluate_writing(
                attempt.task_id, attempt.task_name, response_content,
                attempt.duration_sec, attempt.question,
                prev_response=prev_content,
                session_summary=session_summary,
            )
        else:
            evaluation = _openai_evaluate(
                attempt.task_id, attempt.task_name, response_content,
                attempt.duration_sec, attempt.question,
                prev_transcript=prev_content,
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
            "task_type": attempt.task_type,
            "transcript": attempt.transcript,
            "response_text": attempt.response_text,
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
