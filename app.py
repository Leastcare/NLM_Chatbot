import logging
import os
import uuid
from datetime import datetime

import requests as http_requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# Use absolute path for templates so Vercel can find them regardless of cwd
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(_BASE_DIR, "templates"))
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(32)
if not os.getenv("SECRET_KEY"):
    log.warning("SECRET_KEY not set — sessions will not persist across requests.")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    log.warning("GROQ_API_KEY is not set. The /chat endpoint will fail.")

QUESTION_LIMIT = 40
# Primary model + fallback — if primary hits rate limit, fallback kicks in automatically
MODELS   = ["groq/compound-mini", "qwen/qwen3.8-27b"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------
BASE_PROMPT = (
    "You are NLM Chatbot, a sharp and helpful assistant. "
    "Reply ONLY to what the user actually asked in their last message. "
    "Do NOT repeat definitions or explanations the user did not ask for again. "
    "Do NOT summarise earlier conversation unless the user explicitly asks. "
    "Answer in clear, simple English like a friendly senior explaining concepts. "
    "Start with a 1–2 sentence direct answer, then add at most 2–3 short supporting points. "
    'If the user says things like "in detail" or "explain more", extend the answer freely. '
    "Use markdown formatting: code blocks for code, **bold** for key terms, bullet lists where helpful. "
    "If you are unsure about a factual detail, say so instead of guessing. "
    "Refuse harmful or illegal requests politely and suggest safer alternatives. "
    "Do not give medical, legal, or financial advice; suggest a qualified professional instead. "
    "You have no real-time internet or date access; never pretend you browsed the web. "
)


def build_system_prompt(mode: str) -> str:
    extras = {
        "mca": (
            "Focus mainly on MCA-related topics: programming, algorithms, data structures, "
            "databases, operating systems, networking, software engineering, and exam prep. "
            "Use simple examples a college student in India would understand. "
        ),
        "interview": (
            "Answer in a slightly formal tone suitable for technical or HR interview preparation. "
            "When appropriate, end with one short sentence on how the user might phrase this in an interview. "
        ),
        "code": (
            "The user may paste code. Explain clearly what it does, point out any bugs, "
            "and suggest improvements. Show corrected code in a single fenced code block "
            "followed by one short explanatory sentence. "
        ),
        "sarcastic": (
            "You are allowed — actually encouraged — to be witty and sarcastically funny. "
            "Use dry humour, gentle roasting, and clever observations while still giving a "
            "genuinely correct and helpful answer. Think of yourself as the smartest person "
            "in the room who can't help but let everyone know it, but in a fun way. "
            "Pepper in sarcastic asides and rhetorical questions. "
            "Never be mean-spirited or offensive — keep it playful and clever. "
            "End every answer with a short sarcastic one-liner or observation related to the topic. "
        ),
        "general": (
            "Answer general knowledge, reasoning, or everyday questions clearly and briefly. "
        ),
    }
    return BASE_PROMPT + extras.get(mode, extras["general"])


# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------
def log_qa(question: str, answer: str, mode: str) -> None:
    try:
        with open("chat_log.txt", "a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] "
                f"MODE={mode}\nQ: {question}\nA: {answer}\n\n"
            )
    except OSError as exc:
        log.warning("Could not write to chat_log.txt: %s", exc)


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------
def get_history() -> list:
    """Return the conversation history list for the current session."""
    if "history" not in session:
        session["history"] = []
    return session["history"]


def get_question_count() -> int:
    return session.get("question_count", 0)


def increment_question_count() -> int:
    session["question_count"] = session.get("question_count", 0) + 1
    return session["question_count"]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/health")
def health():
    """Quick liveness check — no AI call."""
    return jsonify({
        "status": "ok",
        "groq_key_set": bool(GROQ_API_KEY),
        "secret_key_set": bool(os.getenv("SECRET_KEY")),
        "models": MODELS,
    })


@app.route("/chat", methods=["POST"])
def chat():
    data_json = request.get_json(silent=True) or {}
    user_message = data_json.get("message", "").strip()
    mode = data_json.get("mode", "general").lower()

    if mode not in {"general", "mca", "interview", "code", "sarcastic"}:
        mode = "general"

    if not user_message:
        return jsonify({"reply": "Please type a message first.", "count": get_question_count()})

    if get_question_count() >= QUESTION_LIMIT:
        return jsonify({
            "reply": (
                "You've hit the 40-question limit for this session. "
                "Click **New Chat** to start fresh."
            ),
            "count": get_question_count(),
        })

    history = get_history()
    system_prompt = build_system_prompt(mode)

    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": user_message}]
    )

    try:
        bot_reply = None
        last_status = None
        for model in MODELS:
            resp = http_requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model":       model,
                    "messages":    messages,
                    "max_tokens":  600,
                    "temperature": 0.7,
                    "top_p":       0.9,
                },
                timeout=50,
            )
            last_status = resp.status_code
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"].strip()
                if content:          # some models return 200 with empty content
                    bot_reply = content
                    break
                else:
                    log.warning("Model %s returned empty content, trying next.", model)
            elif resp.status_code == 429:
                log.warning("Model %s rate-limited (429), trying next.", model)
            else:
                log.error("Model %s returned %s: %s", model, resp.status_code, resp.text[:200])
                break                # non-rate-limit error — don't retry

        if not bot_reply:
            if last_status == 429:
                return jsonify({"reply": "I'm a bit overwhelmed right now — all models are rate-limited. Wait a few seconds and try again.", "count": get_question_count()})
            return jsonify({"reply": f"AI service error ({last_status}). Please try again shortly.", "count": get_question_count()})

    except http_requests.Timeout:
        log.error("Groq API timed out")
        return jsonify({"reply": "The AI took too long to respond. Please try again.", "count": get_question_count()})
    except Exception as exc:
        log.exception("Unexpected error calling Groq: %s", exc)
        return jsonify({"reply": "Something went wrong. Please try again.", "count": get_question_count()})

    # Update session history (keep last 20 messages = 10 exchanges)
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": bot_reply})
    if len(history) > 20:
        history[:] = history[-20:]
    session["history"] = history
    session.modified = True

    count = increment_question_count()
    log_qa(user_message, bot_reply, mode)

    return jsonify({"reply": bot_reply, "count": count})


@app.route("/reset", methods=["POST"])
def reset():
    """Clear this session's conversation history and question counter."""
    session.pop("history", None)
    session.pop("question_count", None)
    log.info("Session %s reset.", session.get("session_id", "unknown"))
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# Entry point (dev only — use gunicorn in production)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug)
