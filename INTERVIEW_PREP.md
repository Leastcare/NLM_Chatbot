# NLM Chatbot — Complete Interview Preparation Guide

---

## PART 1 — THE SHORT BRIEF (say this in 30 seconds)

> "I built a full-stack AI chatbot called NLM Chatbot. The backend is Python Flask. It connects to Groq's free API to get answers from an AI model. The frontend is plain HTML, CSS, and JavaScript — no framework. It has 5 chat modes, a cherry blossom animated UI, falling petal canvas animation, 3D tilt effects on panels, and is deployed live on Vercel. I also set up automatic model fallback so if one AI model hits its rate limit, it switches to another one automatically."

---

## PART 2 — WHAT THE PROJECT DOES (simple explanation)

Think of it like this:

1. User opens the website
2. User types a question and clicks Send
3. The browser sends that question to our Flask server
4. Flask adds a "system prompt" (instructions for the AI) and sends everything to Groq's API
5. Groq's AI model reads it and sends back an answer
6. Flask returns that answer to the browser
7. The browser shows it in a nice chat bubble

That's the whole loop. Everything else is decoration and safety.

---

## PART 3 — PROJECT STRUCTURE (what each file does)

```
NLM_Chatbot/
│
├── app.py              ← The brain. All Python logic lives here.
├── wsgi.py             ← Just 2 lines. Tells Vercel how to start the app.
├── requirements.txt    ← List of Python packages to install.
├── vercel.json         ← Tells Vercel how to deploy the app.
├── Procfile            ← Tells Render/Railway how to start the app.
├── .env                ← Secret keys (never uploaded to GitHub).
├── .env.example        ← Template showing what keys are needed.
├── .gitignore          ← List of files Git should ignore (.env etc).
├── README.md           ← Project description on GitHub.
├── INTERVIEW_PREP.md   ← This file.
└── templates/
    └── index.html      ← The entire frontend. HTML + CSS + JavaScript.
```

---

## PART 4 — DETAILED EXPLANATION OF EVERY IMPORTANT THING

---

### 4.1 — What is Flask?

Flask is a Python library that lets you create a web server.

Think of it like a restaurant:
- Flask is the restaurant building
- Routes (`@app.route`) are the menu items
- Requests are customers ordering food
- Responses are the food being served back

```python
from flask import Flask
app = Flask(__name__)

@app.route("/")           # When someone visits the homepage
def index():
    return "Hello!"       # Send this back
```

---

### 4.2 — The 4 Routes in app.py

| Route | Method | What it does |
|---|---|---|
| `/` | GET | Sends the HTML page to the browser |
| `/chat` | POST | Receives a message, calls AI, returns reply |
| `/reset` | POST | Clears conversation history |
| `/health` | GET | Quick check — is the server alive? |

**GET** = "give me something" (like opening a webpage)
**POST** = "here is some data, process it" (like submitting a form)

---

### 4.3 — The `/chat` route step by step

This is the most important function. Here is what happens line by line:

```python
@app.route("/chat", methods=["POST"])
def chat():
    # Step 1 — Read what the user sent
    data_json = request.get_json(silent=True) or {}
    user_message = data_json.get("message", "").strip()
    mode = data_json.get("mode", "general").lower()
```
`request.get_json()` reads the JSON body the browser sent.
`silent=True` means don't crash if the body is empty — just return None.
`or {}` means if it IS None, use an empty dictionary instead.

```python
    # Step 2 — Validate the mode
    if mode not in {"general", "mca", "interview", "code", "sarcastic"}:
        mode = "general"
```
If someone sends a fake mode like "hacker", we ignore it and use "general".

```python
    # Step 3 — Check the question limit
    if get_question_count() >= QUESTION_LIMIT:
        return jsonify({"reply": "You've hit the 40-question limit...", "count": ...})
```
After 40 questions we stop. This prevents someone from hammering the API.

```python
    # Step 4 — Build the message list for the AI
    messages = (
        [{"role": "system", "content": system_prompt}]   # Instructions for the AI
        + history                                          # Previous conversation
        + [{"role": "user", "content": user_message}]    # New message
    )
```
The AI needs the full conversation every time — it has no memory of its own.

```python
    # Step 5 — Try each model in order
    for model in MODELS:
        resp = http_requests.post(GROQ_URL, ...)
        if resp.status_code == 200 and content:
            bot_reply = content
            break                 # Got a good answer, stop trying
        elif resp.status_code == 429:
            continue              # Rate limited, try next model
```
MODELS = `["groq/compound-mini", "qwen/qwen3.8-27b"]`
We try compound-mini first. If it's rate limited (429), we try qwen. This is called a **fallback chain**.

```python
    # Step 6 — Save to session and return
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": bot_reply})
    session["history"] = history
    return jsonify({"reply": bot_reply, "count": count})
```

---

### 4.4 — What is a Session?

A session is a way to remember things about a specific user between requests.

Without sessions, every time someone sends a message, Flask would forget who they are and what they said before.

Flask sessions work using **cookies** — a small piece of data stored in the browser. Every request the browser sends that cookie back, and Flask uses it to find that user's data.

```python
session["history"] = [...]     # Save data
session.get("history", [])     # Read data
session.pop("history", None)   # Delete data
```

The `SECRET_KEY` is used to **sign** (encrypt) the cookie so nobody can fake it.

---

### 4.5 — What is a System Prompt?

A system prompt is a secret instruction given to the AI before the user's message. The user never sees it.

Example:
```
"You are NLM Chatbot. Reply ONLY to what was asked.
Use markdown. Never give medical advice..."
```

We have a **base prompt** (common rules for all modes) and then add **extra instructions** based on the mode.

```python
def build_system_prompt(mode: str) -> str:
    return BASE_PROMPT + extras.get(mode, extras["general"])
```

This is why the AI behaves differently in "Sarcastic" mode vs "MCA Study" mode — same AI, different instructions.

---

### 4.6 — What is the Groq API?

Groq is a company that runs AI models on very fast hardware. They give a free tier.

We send them a POST request with our messages. They run the AI model and send back a reply.

```python
resp = http_requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": "Bearer " + GROQ_API_KEY},
    json={
        "model": "groq/compound-mini",
        "messages": messages,
        "max_tokens": 600,      # Maximum length of reply
        "temperature": 0.7,     # 0 = robotic, 1 = creative
        "top_p": 0.9            # Controls word choice variety
    },
    timeout=50   # Give up after 50 seconds
)
```

The reply looks like this:
```json
{
  "choices": [{
    "message": {
      "content": "The AI's reply goes here"
    }
  }]
}
```

We extract it with:
```python
bot_reply = resp.json()["choices"][0]["message"]["content"].strip()
```

---

### 4.7 — Why we switched from Groq SDK to requests

Originally we used the official `groq` Python package. But Vercel's serverless environment has a sandboxed network — the `groq` SDK uses `httpx` internally which caused silent failures.

We replaced it with the plain `requests` library which calls the same API URL directly. Same result, zero compatibility issues.

This is a key debugging decision — when a library fails in a specific environment, go one level lower and use HTTP directly.

---

### 4.8 — What is the Fallback Chain?

```python
MODELS = ["groq/compound-mini", "qwen/qwen3.8-27b"]

for model in MODELS:
    resp = http_requests.post(...)
    if resp.status_code == 200 and content:
        bot_reply = content
        break
    elif resp.status_code == 429:   # Rate limited
        continue                     # Try next model
    else:
        break                        # Real error, stop
```

**Why?** Free tier AI APIs have rate limits — you can only make X calls per minute. If `compound-mini` is busy, we automatically switch to `qwen`. User never notices.

**429** means "Too Many Requests" — you're sending too fast.

---

### 4.9 — What is the .env file?

A `.env` file stores secret values that your code needs but should never be public.

```
GROQ_API_KEY=gsk_xxx...
SECRET_KEY=6b07c2f...
FLASK_DEBUG=false
PORT=5000
```

`python-dotenv` reads this file and loads these as environment variables.

```python
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("GROQ_API_KEY")   # Read the value
```

**Why not just put the key in the code?**
Because code goes on GitHub. GitHub is public. Anyone can see it and steal your key.

---

### 4.10 — The Frontend (index.html)

The entire frontend is one HTML file. No React, no Vue, no framework.

**Key JavaScript functions:**

```javascript
// Send a message
async function sendMsg() {
    const text = inp.value.trim();
    if (!text) return;
    addMsg(text, 'user', false);   // Show user bubble
    await callAPI(text);            // Call Flask
}

// Call the Flask backend
async function callAPI(message) {
    const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, mode })  // Send as JSON
    });
    const data = await res.json();
    addMsg(data.reply, 'bot', true);    // Show bot bubble
    updateCount(data.count);            // Update progress bar
}

// Add a message bubble to the screen
function addMsg(text, sender, isMarkdown) {
    const row = document.createElement('div');
    row.className = 'msg-row ' + sender;
    // ... builds the HTML for the bubble
    chatbox.appendChild(row);
    chatbox.scrollTop = chatbox.scrollHeight;  // Scroll to bottom
}
```

---

### 4.11 — The Canvas Petal Animation

```javascript
// Each petal is an object with these properties:
{
    x, y,       // Position on screen
    speed,      // How fast it falls
    drift,      // Left/right drift
    rot,        // Current rotation angle
    rotS,       // Rotation speed
    swing,      // Sway frequency
    color,      // Pink shade (rgba)
    opacity     // Transparency
}

// Every frame:
function animate() {
    ctx.clearRect(0, 0, W, H);   // Wipe the canvas
    petals.forEach((p, i) => {
        p.y += p.speed;           // Fall down
        p.x += Math.sin(p.t);    // Sway left/right
        p.rot += p.rotS;          // Rotate
        drawPetal(p);             // Draw it
        if (p.y > H) petals[i] = newPetal(true);  // Recycle off-screen
    });
    requestAnimationFrame(animate);  // Loop
}
```

`requestAnimationFrame` is a browser function that runs your code ~60 times per second — smooth animation.

---

### 4.12 — The 3D Tilt Effect

```javascript
bubble.addEventListener('mousemove', e => {
    const rect = bubble.getBoundingClientRect();
    const x = e.clientX - rect.left;    // Mouse X inside bubble
    const y = e.clientY - rect.top;     // Mouse Y inside bubble
    const cx = rect.width / 2;           // Center X
    const cy = rect.height / 2;          // Center Y
    
    // How far from center (as fraction)
    const tiltX = ((y - cy) / cy) * -7;  // Max 7 degrees
    const tiltY = ((x - cx) / cx) * 7;
    
    bubble.style.transform =
        `perspective(600px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale(1.012)`;
});
```

`perspective` creates the 3D illusion. The further you are from center, the more it tilts.

---

### 4.13 — Markdown Rendering

The AI replies in markdown — `**bold**`, ` ```code``` `, `- bullet points`.

We use the `marked.js` library to convert markdown to HTML:

```javascript
marked.setOptions({ breaks: true, gfm: true });

function renderMD(text) {
    return marked.parse(text)
        .replace(/<script[\s\S]*?<\/script>/gi, '');  // Security: remove scripts
}
```

The `.replace` at the end removes any `<script>` tags — this prevents XSS attacks where the AI could theoretically return malicious JavaScript.

---

### 4.14 — Why Vercel Deployment Was Tricky (debugging story)

**Problem 1:** `TemplateNotFound` — Flask couldn't find `index.html`

**Why:** Vercel's serverless functions run in a temporary directory, not the repo root. `templates/` was a relative path that didn't resolve correctly.

**Fix:**
```python
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(_BASE_DIR, "templates"))
```
`os.path.abspath(__file__)` gives the full real path of `app.py` no matter where Python runs from.

---

**Problem 2:** 429 Rate Limit errors

**Why:** `qwen/qwen3.8-27b` has tight free tier limits — too many requests too fast.

**Fix:** Fallback chain — try `compound-mini` first, auto-switch on 429.

---

**Problem 3:** `groq` SDK failed silently on Vercel

**Why:** The SDK uses `httpx` internally which had proxy/sandbox issues in Vercel's Lambda environment.

**Fix:** Replaced the entire SDK with a direct `requests.post` call to the same REST API.

---

**Problem 4:** Sessions breaking between requests

**Why:** `SECRET_KEY` was not set as env var on Vercel. Code was using `os.urandom(32)` which generates a NEW random key on every cold start. Sessions signed with the old key become invalid.

**Fix:** Set `SECRET_KEY` as a permanent environment variable in Vercel dashboard.

---

**Problem 5:** Timeout on "More detail" button

**Why:** Vercel's default serverless function timeout is 10 seconds. Detailed AI responses take longer.

**Fix:** Added `"maxDuration": 60` in `vercel.json`.

---

## PART 5 — INTERVIEW QUESTIONS

---

### LEVEL 1 — Basic / Fresher Questions

These are easy questions. Answer confidently.

---

**Q1. What is your project about? Explain in simple words.**

"I built a chatbot web application. The user types a question on the website, it gets sent to a Python server, the server calls an AI API (Groq), gets the answer, and sends it back to the user's browser. The whole thing is live on Vercel."

---

**Q2. What technology did you use?**

- Backend: Python, Flask
- AI: Groq API (models: compound-mini and qwen3.8-27b)
- Frontend: HTML, CSS, JavaScript (no framework)
- Libraries: marked.js (markdown), highlight.js (code coloring), Lucide (icons)
- Deployment: Vercel
- Version control: Git + GitHub

---

**Q3. What is Flask?**

Flask is a lightweight Python web framework. It lets you create routes (URLs) and handle HTTP requests and responses. I used it to create the backend server with 4 routes: `/`, `/chat`, `/reset`, and `/health`.

---

**Q4. What is an API?**

API stands for Application Programming Interface. It's a way for two programs to talk to each other. I use Groq's API — I send them a message, they process it with an AI model and send back a reply. It's like a waiter — I give my order, the kitchen (AI) prepares it, the waiter brings it back.

---

**Q5. What is a GET vs POST request?**

- **GET**: Used to retrieve data. Like opening a webpage. No body.
- **POST**: Used to send data. Like submitting a form. Has a body with data.

In my project, `/` is GET (browser asks for the page), `/chat` is POST (browser sends the user's message).

---

**Q6. What is JSON?**

JSON stands for JavaScript Object Notation. It's a standard format for sending data between a server and browser. It looks like a Python dictionary:
```json
{"message": "Hello", "mode": "general"}
```
Flask receives JSON with `request.get_json()` and sends it back with `jsonify()`.

---

**Q7. What is an environment variable? Why did you use .env?**

An environment variable is a value stored outside your code — on the computer or server — so you don't hardcode secrets like API keys in your code. If I put my API key in `app.py` and pushed to GitHub, anyone could steal it and use my account. The `.env` file stores secrets locally, and `.gitignore` prevents it from being uploaded.

---

**Q8. What does `requirements.txt` do?**

It lists all Python packages the project needs. When someone clones the project and runs `pip install -r requirements.txt`, all packages install automatically. Mine has: flask, requests, python-dotenv, gunicorn.

---

**Q9. What is Git and GitHub?**

Git is version control — it tracks all changes to your code. GitHub is a website that stores your Git repository online. I used `git add`, `git commit`, and `git push` to upload my project.

---

**Q10. What is Vercel?**

Vercel is a cloud hosting platform. It connects to GitHub — whenever I push code, Vercel automatically deploys the new version. It's free for small projects. It runs Python code as serverless functions.

---

### LEVEL 2 — Mid Level / Technical Questions

These need a bit more explanation. Take a breath and think.

---

**Q11. What is a session in Flask? How does it work?**

A session stores user-specific data between requests. HTTP is stateless — every request is independent. Sessions solve this by storing data in a **signed cookie** on the browser.

When a user sends a message:
1. Flask reads the session cookie
2. Finds that user's conversation history
3. Uses it when calling the AI
4. Updates and saves it back

The `SECRET_KEY` is used to cryptographically sign the cookie so it can't be tampered with. If `SECRET_KEY` changes, all existing sessions become invalid — which is why I store it as a fixed environment variable.

---

**Q12. Why did you keep conversation history? How did you implement it?**

The AI has no memory. Every API call is independent. So I maintain the last 20 messages (10 exchanges) in the session and send them with every request.

```python
messages = [system_prompt] + history + [new_user_message]
```

To prevent the history from growing forever (which increases cost and hits token limits):
```python
if len(history) > 20:
    history[:] = history[-20:]   # Keep only the last 20
```

---

**Q13. What is a system prompt? Why is it important?**

A system prompt is a hidden instruction sent to the AI before the user's message. It shapes the AI's personality and behavior.

I have a base prompt (applies to all modes) and mode-specific extras. For example, in "Sarcastic" mode I add: *"Be witty and sarcastically funny while still being correct."*

This is called **prompt engineering** — crafting instructions to control AI output.

---

**Q14. What is the fallback model chain? Why did you build it?**

Free AI APIs have rate limits. If you send too many requests, they return HTTP 429 (Too Many Requests).

My solution — try models in order:
```python
MODELS = ["groq/compound-mini", "qwen/qwen3.8-27b"]
for model in MODELS:
    resp = http_requests.post(...)
    if status == 200 and content: break     # Success
    if status == 429: continue              # Rate limited, try next
    else: break                             # Real error, stop
```

This gives the app higher availability — it degrades gracefully instead of failing.

---

**Q15. What is HTTP status code 429? Name other important codes.**

| Code | Meaning |
|---|---|
| 200 | OK — success |
| 201 | Created |
| 400 | Bad Request — invalid input |
| 401 | Unauthorized — not logged in |
| 403 | Forbidden — logged in but no permission |
| 404 | Not Found |
| 429 | Too Many Requests — rate limited |
| 500 | Internal Server Error — server crashed |
| 503 | Service Unavailable |

---

**Q16. What is XSS? How did you prevent it?**

XSS stands for Cross-Site Scripting. It's when an attacker injects malicious JavaScript into a webpage.

In my case, the AI could theoretically return a response containing `<script>alert('hacked')</script>`. If I rendered that as HTML, it would execute.

My fix:
```javascript
function renderMD(text) {
    return marked.parse(text)
        .replace(/<script[\s\S]*?<\/script>/gi, '');  // Strip all script tags
}
```
I sanitize the AI's output before putting it on the page.

---

**Q17. Why did you use `os.path.abspath(__file__)` for templates?**

`__file__` gives the path of the current Python file. `os.path.abspath` converts it to an absolute path (full path from root, not relative).

On Vercel, the serverless function runs from a temp directory. Relative paths like `./templates` break. Absolute path always works.

```python
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# This always = the folder where app.py lives, regardless of where Python is run from
```

---

**Q18. What is `requestAnimationFrame`? Why use it for animation?**

`requestAnimationFrame` is a browser API that calls your function right before the next screen repaint (~60 times per second). It's the right way to do animation because:

1. It syncs with the display refresh rate — smooth, no tearing
2. It pauses when the tab is not visible — saves battery/CPU
3. It's more efficient than `setInterval`

I use it for the falling petal animation loop.

---

**Q19. What is `async/await` in JavaScript?**

It's a way to write asynchronous code that looks synchronous — easier to read.

```javascript
// Old way (callback hell)
fetch('/chat').then(res => res.json()).then(data => { ... });

// New way (async/await)
async function callAPI(message) {
    const res = await fetch('/chat', { method: 'POST', ... });
    const data = await res.json();
    addMsg(data.reply, 'bot', true);
}
```

`await` pauses execution until the promise resolves. The function must be `async`.

---

**Q20. What is the difference between `localStorage` and session cookies?**

| | localStorage | Session Cookie |
|---|---|---|
| Stored | In browser | In browser, sent to server |
| Accessible by | JavaScript only | Server + JavaScript |
| Expires | Never (until cleared) | When browser closes (or set expiry) |
| I used | Not used | Flask session (for history) |

Flask sessions use signed cookies — the server can verify they haven't been tampered with.

---

**Q21. What is gunicorn? Why is it in requirements.txt?**

Gunicorn is a production WSGI server for Python. Flask's built-in server is for development only — it handles one request at a time and is not secure.

Gunicorn handles multiple requests simultaneously. The `Procfile` says:
```
web: gunicorn app:app
```
This tells Render/Railway: "Start the app using gunicorn, find the `app` object inside `app.py`."

Vercel uses its own serverless runtime instead of gunicorn.

---

**Q22. What is `wsgi.py`? Why did you create it?**

WSGI (Web Server Gateway Interface) is the standard interface between Python web apps and web servers.

Vercel's Python runtime looks for a Python file with an `app` object. `wsgi.py` is the explicit entry point:

```python
from app import app

if __name__ == "__main__":
    app.run()
```

It imports the Flask `app` from `app.py` and exposes it. Vercel finds it, wraps it, and runs it as a serverless function.

---

### LEVEL 3 — Advanced / High Level Questions

These are for senior interviews. Think about the "why" behind decisions.

---

**Q23. How does the AI conversation context work? What are the limitations?**

Every message to the AI includes the full conversation history. AI models have a **context window** — a maximum number of tokens (words) they can process at once.

I limit history to 20 messages (10 exchanges) to stay within limits and control cost. The tradeoff: conversations longer than 10 exchanges lose their earliest context.

A better solution for production: store conversation in a database (Redis or PostgreSQL), summarize old messages instead of dropping them.

---

**Q24. What are the security vulnerabilities in your project and how did you address them?**

| Vulnerability | My mitigation |
|---|---|
| API key exposure | Stored in `.env`, added `.gitignore`, never committed |
| XSS via AI output | Strip `<script>` tags from markdown output |
| Session tampering | Flask signs cookies with `SECRET_KEY` |
| Shared global state | Moved from module-level globals to Flask session — per-user isolation |
| Prompt injection | Base prompt instructs AI to refuse harmful requests |
| Rate abuse | 40 question limit per session |
| Debug mode in prod | `FLASK_DEBUG` read from env var, defaults to false |

---

**Q25. What was the biggest bug you faced and how did you debug it?**

The most interesting bug was the `TemplateNotFound` error on Vercel. Locally the app worked perfectly. On Vercel, every page load returned a 500 error.

**Debugging process:**
1. Added a `/health` route that returns JSON — confirmed the server was alive
2. The health route worked but `/` didn't — narrowed it to template loading
3. Researched Vercel's serverless execution model — discovered it runs from a temp directory
4. Checked `os.getcwd()` would return something different from where `app.py` lives
5. Fixed by using `os.path.abspath(__file__)` to build an absolute template path

The lesson: when something works locally but not in production, the environment is the first suspect, not the code.

---

**Q26. Why not use React or Vue for the frontend?**

Deliberate choice for this project:
- No build step needed — just open the file
- Zero JavaScript bundle overhead — page loads faster
- Simpler deployment — one HTML file, no npm, no webpack
- For a chatbot UI, vanilla JS is completely sufficient — DOM manipulation, fetch, events

The downside: more verbose code. For a larger app with complex state, a framework would be worth it.

---

**Q27. How does the temperature parameter affect AI output?**

Temperature controls randomness in the AI's word selection:

- `temperature = 0.0` → Deterministic, always picks the most likely word → robotic, repetitive
- `temperature = 0.7` → Balanced → natural, varied responses (what I use)
- `temperature = 1.0+` → Very random → creative but sometimes incoherent

I use `0.7` because it gives natural-sounding answers while staying on topic.

---

**Q28. How would you scale this app for 10,000 users?**

Current limitations:
1. Flask session = cookie-based = fine for many users (no server memory used)
2. Groq API = rate limited per API key = bottleneck
3. Vercel serverless = auto-scales = fine

Changes needed for scale:
1. **Multiple API keys** — rotate between them to multiply rate limit
2. **Redis for session storage** — for shared session state across serverless instances
3. **Queue system** (Celery/RQ) — for handling request spikes without timeout
4. **Response caching** — cache common questions (deadlock, TCP vs UDP) to avoid redundant API calls
5. **Streaming** — use SSE (Server-Sent Events) to stream tokens as they arrive instead of waiting

---

**Q29. What is the difference between `requests.post` and `fetch` in JavaScript?**

Both make HTTP POST requests — but from different places:

| | `requests.post` (Python) | `fetch` (JavaScript) |
|---|---|---|
| Runs on | Server (Flask) | Browser (client) |
| Used for | Calling Groq API | Calling Flask `/chat` |
| Returns | `Response` object | `Promise<Response>` |
| Async | Blocking (by default) | Non-blocking (async/await) |

In my app: browser `fetch` → Flask → `requests.post` → Groq → back up the chain.

---

**Q30. Why use `session.modified = True`?**

Flask only sends the session cookie back to the browser if it detects a change. When you mutate a mutable object inside the session (like appending to a list), Flask doesn't always detect it automatically.

```python
session["history"].append(...)  # Flask might not detect this change
session.modified = True          # Force Flask to resend the cookie
```

Without this, the conversation history could silently fail to persist.

---

**Q31. What is the difference between `400`, `401`, `403` and when would each appear in your app?**

- **400 Bad Request** — Client sent invalid data. In my app: if the request body isn't valid JSON, `request.get_json(silent=True)` returns None and I fall back to `{}` — no crash.
- **401 Unauthorized** — Not authenticated. Would happen if I had a login system and someone tried to chat without logging in.
- **403 Forbidden** — Authenticated but no permission. Not currently applicable but relevant if I added user roles.

My app handles 400 gracefully. 401/403 would need a login system.

---

**Q32. How does the `marked.js` + `highlight.js` pipeline work?**

```
AI reply (markdown text)
        ↓
marked.parse(text)       ← Converts markdown to HTML
        ↓
Strip <script> tags      ← Security sanitization
        ↓
innerHTML = result       ← Inject HTML into bubble
        ↓
hljs.highlightElement()  ← Find <code> blocks, add syntax colors
```

`marked.js` turns `**bold**` into `<strong>bold</strong>` and ` ```python ``` ` into `<pre><code class="language-python">`.

`highlight.js` then finds those `<code>` elements and adds coloring based on the language class.

---

## PART 6 — THINGS TO REMEMBER BY HEART

These are the exact things interviewers ask you to write on a whiteboard or explain without notes.

---

**The request-response cycle:**
```
Browser → fetch('/chat', POST) → Flask → requests.post(Groq) → AI
AI → Groq → Flask → jsonify(reply) → Browser → addMsg(bubble)
```

---

**Flask session in 3 lines:**
```python
session["key"] = value      # Store
value = session.get("key")  # Read
session.pop("key", None)    # Delete
```

---

**Why SECRET_KEY matters:**
Flask uses it to sign session cookies. Without a fixed key, every server restart invalidates all sessions.

---

**The 429 fallback in plain English:**
"Try model A. If rate limited, try model B. If both fail, tell the user nicely."

---

**Why absolute path for templates:**
`os.path.abspath(__file__)` always gives the real location of `app.py` regardless of where the server is started from. Vercel runs from a different working directory.

---

**HTTP methods:**
- GET = fetch a resource
- POST = send data to process
- PUT = replace a resource
- DELETE = remove a resource

---

**The system prompt role:**
It's like giving the AI a job description before the interview starts. It sets personality, constraints, and tone without the user seeing it.

---

## PART 7 — ONE-LINE ANSWERS FOR RAPID FIRE ROUND

| Question | Answer |
|---|---|
| What language is the backend in? | Python |
| What framework? | Flask |
| What AI model? | Groq compound-mini (primary), qwen3.8-27b (fallback) |
| Where is it deployed? | Vercel |
| How many routes? | 4 — `/`, `/chat`, `/reset`, `/health` |
| What does 429 mean? | Rate limited — too many requests |
| What is a session? | Server-side user memory stored via cookies |
| Why `.gitignore` the `.env`? | Contains secret API keys — must not be public |
| What is gunicorn? | Production Python web server |
| What does `wsgi.py` do? | Entry point for Vercel — imports and exposes Flask app |
| What is temperature in AI? | Controls randomness — 0 = deterministic, 1 = creative |
| What is XSS? | Injecting malicious scripts into a webpage |
| What is `requestAnimationFrame`? | Browser API for smooth 60fps animation loops |
| What is `async/await`? | Syntax for non-blocking asynchronous JavaScript |
| How many questions per session? | 40 (then user must start a new chat) |
| How many messages kept in history? | 20 (last 10 exchanges) |
| What is marked.js? | JavaScript library that converts markdown to HTML |
| What is highlight.js? | Adds syntax coloring to code blocks |
| What is the `health` route for? | Quick check that server is alive without calling AI |
| Why `session.modified = True`? | Forces Flask to resend cookie after mutating session data |

---

*Built by Leastcare · NLM Chatbot · Live at [nlm-chatbot.vercel.app](https://nlm-chatbot.vercel.app/)*
