from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Simple in-memory conversation history (single user/demo)
conversation_history = []
question_count = 0
QUESTION_LIMIT = 40  # free-session style limit


def build_system_prompt(mode: str) -> str:
    """
    Returns a system prompt based on selected mode.
    mode: 'general', 'mca', 'interview', 'code'
    """
    base = (
        "You are NLM Chatbot, a helpful assistant that can answer questions on any topic, "
        "with extra skill in MCA-related subjects. "
        "Always answer the user's latest message in the context of the full conversation. "
        "Start every reply with 1–2 sentences that directly answer the question. "
        "Then, if useful, add at most 2–3 short supporting sentences or bullet points. "
        "Answer directly without long introductions, self-descriptions, or disclaimers. "
        "Use clear, simple English and usually keep answers to 3–5 concise sentences, "
        "unless the user explicitly asks for a very detailed explanation of the topic. "
        "If you are not sure about a factual detail, say you are uncertain instead of guessing. "
        "Refuse harmful or illegal requests politely and suggest safer alternatives. "
        "Do not give medical, legal, or financial advice; instead suggest consulting a qualified professional. "
        "You do not have real-time internet or current date access; never pretend you browsed the web. "
    )

    if mode == "mca":
        extra = (
            "Focus mainly on MCA-related topics: programming, algorithms, data structures, "
            "databases, operating systems, networking, software engineering, and exam preparation. "
            "Use simple examples a college student in India would understand. "
        )
    elif mode == "interview":
        extra = (
            "Answer in a slightly formal tone, suitable for technical or HR interview preparation. "
            "When appropriate, end with one short sentence suggesting how the user might phrase this "
            "answer in an interview. "
        )
    elif mode == "code":
        extra = (
            "Assume the user may paste code. Explain clearly what the code does, point out bugs, "
            "and suggest improvements. When showing corrected code, use a single fenced code block "
            "and then one short explanatory sentence. "
        )
    else:  # general
        extra = (
            "You may also answer general knowledge, reasoning, or everyday questions clearly and briefly. "
        )

    return base + extra


def log_qa(question: str, answer: str, mode: str):
    """Append each Q&A pair to a simple log file with timestamp and mode."""
    try:
        with open("chat_log.txt", "a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] "
                f"MODE={mode}\nQ: {question}\nA: {answer}\n\n"
            )
    except Exception:
        # Logging errors should not crash the app
        pass


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    global question_count

    data_json = request.get_json()
    user_message = data_json.get('message', '').strip()
    mode = data_json.get('mode', 'general').lower()  # 'general' | 'mca' | 'interview' | 'code'

    if not user_message:
        return jsonify({"reply": "Please type a message first."})

    # Simple free-session style limit
    if question_count >= QUESTION_LIMIT:
        reply = (
            "You have reached the question limit for this free demo session. "
            "Click 'New Chat' to start a fresh conversation."
        )
        return jsonify({"reply": reply})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "NLM Chatbot"
    }

    system_prompt = build_system_prompt(mode)

    # Messages: system + limited history + new user message
    messages = [
        {"role": "system", "content": system_prompt}
    ] + conversation_history + [
        {"role": "user", "content": user_message}
    ]

    data = {
        "model": "mistralai/mixtral-8x7b-instruct",
        "messages": messages,
        "max_tokens": 400,
        "temperature": 0.4,
        "top_p": 0.9
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
    except Exception:
        return jsonify({"reply": "Network error while contacting the AI service. Please try again."})

    print("STATUS:", response.status_code)
    print("BODY:", response.text)

    if response.status_code != 200:
        reply = (
            f"The AI service returned an error (code {response.status_code}). "
            "Please try again after some time."
        )
        return jsonify({"reply": reply})

    try:
        j = response.json()
        if "choices" in j and j["choices"]:
            bot_reply = j["choices"][0]["message"]["content"]
        else:
            bot_reply = "Sorry, I couldn't get a valid reply from the AI."
    except Exception:
        bot_reply = "Sorry, something went wrong reading the AI response."

    bot_reply = bot_reply.strip()

    # Update history
    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": bot_reply})

    # Keep only last 10 exchanges (20 messages)
    if len(conversation_history) > 20:
        conversation_history[:] = conversation_history[-20:]

    # Increment question count and log for report
    question_count += 1
    log_qa(user_message, bot_reply, mode)

    return jsonify({"reply": bot_reply})


@app.route('/reset', methods=['POST'])
def reset():
    """Clear server-side conversation history and question counter."""
    conversation_history.clear()
    global question_count
    question_count = 0
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
