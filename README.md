# NLM Chatbot

A fast, sarcastic-when-needed Flask chatbot powered by **Groq** (LLaMA 3.3 70B) — free tier, near-instant responses.

---

## Features

- 5 chat modes: General · MCA Study · Interview Prep · Explain Code · 😏 Sarcastic
- Markdown rendering with syntax-highlighted code blocks
- Per-user session isolation (no conversation bleed between users)
- 40-question session limit with live counter
- Copy button with visual feedback
- Auto-growing textarea (Shift+Enter for new line)
- Mobile responsive layout
- Persistent chat log to `chat_log.txt`

---

## Setup

### 1. Clone and create a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get a free Groq API key
1. Sign up at [console.groq.com](https://console.groq.com)
2. Create an API key
3. Copy `.env.example` to `.env` and fill in your key:

```bash
cp .env.example .env
```

`.env` contents:
```
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=any_long_random_string_here
FLASK_DEBUG=false
PORT=5000
```

### 4. Run locally
```bash
python app.py
```
Open [http://localhost:5000](http://localhost:5000)

---

## Production Deployment (e.g. Render, Railway, Fly.io)

All have a free tier. Use gunicorn:

```bash
gunicorn app:app
```

Set the following environment variables in your hosting dashboard:
- `GROQ_API_KEY`
- `SECRET_KEY` (any long random string — keep it secret)
- `PORT` (usually set automatically by the host)
- `FLASK_DEBUG=false`

A `Procfile` is included:
```
web: gunicorn app:app
```

---

## Groq Free Tier Limits (as of 2025)

| Model | Requests/day | Tokens/minute |
|---|---|---|
| llama-3.3-70b-versatile | 14,400 | 6,000 |

More than enough for personal/demo use.

---

## Project Structure

```
NLM_Chatbot/
├── app.py              # Flask backend
├── requirements.txt    # Dependencies
├── .env                # API keys (never commit this)
├── .env.example        # Template for .env
├── .gitignore
├── Procfile            # For gunicorn/deployment
├── README.md
├── chat_log.txt        # Auto-created on first message
└── templates/
    └── index.html      # Full frontend (HTML/CSS/JS)
```

---

## Tech Stack

- **Backend**: Python · Flask · Groq SDK
- **AI Model**: LLaMA 3.3 70B Versatile (via Groq)
- **Frontend**: Vanilla HTML/CSS/JS · marked.js · highlight.js
- **Deployment**: Gunicorn
