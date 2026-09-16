# 🌸 NLM Chatbot

**Live Demo → [nlm-chatbot.vercel.app](https://nlm-chatbot.vercel.app/)**

A conversational AI chatbot built with Flask and powered by **Qwen 3 27B via Groq** — fast, free-tier, and surprisingly witty.

---

## ✦ Features

- **5 chat modes** — General · MCA Study · Interview Prep · Explain Code · Sarcastic
- **Cherry blossom UI** — falling petal canvas animation, sakura light theme, warm paper aesthetic
- **3-D tilt effects** — mouse-parallax on bubbles, sidebar, input, and chips
- **Lucide icons** — clean SVG icons throughout
- **Markdown rendering** — syntax-highlighted code blocks via marked.js + highlight.js
- **Per-session conversation history** — isolated per browser tab, no cross-user bleed
- **40-question session limit** with live shimmer progress bar
- **Copy / Explain more / Shorten** actions on every bot reply
- **Export chat** — download full conversation as `.txt`
- **Mobile responsive** — off-canvas sidebar, works on all screen sizes

---

## 🛠 Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python · Flask |
| AI Model | Qwen 3 27B (via Groq API) |
| Frontend | Vanilla HTML / CSS / JS |
| Markdown | marked.js · highlight.js |
| Icons | Lucide SVG |
| Deployment | Vercel |

---

## 🚀 Local Setup

**1. Clone the repo**
```bash
git clone https://github.com/Leastcare/NLM_Chatbot.git
cd NLM_Chatbot
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Create your `.env` file**
```bash
cp .env.example .env
```
Then fill in your values:
```
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=any_long_random_string
FLASK_DEBUG=false
PORT=5000
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

**5. Run**
```bash
python app.py
```
Open [http://localhost:5000](http://localhost:5000).

---

## ☁️ Deploy on Vercel

1. Fork / import this repo into [vercel.com](https://vercel.com)
2. Add environment variables in the Vercel dashboard:
   - `GROQ_API_KEY`
   - `SECRET_KEY`
   - `FLASK_DEBUG=false`
3. Deploy — the `vercel.json` is already configured

---

## 📁 Project Structure

```
NLM_Chatbot/
├── app.py              # Flask backend — routes, Groq API, session logic
├── requirements.txt    # Dependencies
├── vercel.json         # Vercel deployment config
├── Procfile            # Gunicorn entry point (Render / Railway)
├── .env.example        # Environment variable template
├── .gitignore
├── README.md
└── templates/
    └── index.html      # Entire frontend — HTML · CSS · JS · canvas petals
```

---

## 📸 Preview

> Cherry blossom light theme with falling petal animation, glassmorphic panels, and 3-D tilt on hover.

---

## 👤 Author

Built by **Leastcare**  
Powered by [Groq](https://groq.com) · Deployed on [Vercel](https://vercel.com)
