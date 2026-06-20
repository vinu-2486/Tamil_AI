# "கற்பது தமிழ் கற்பிப்பது AI"-Tamil Pronunciation Coach

An AI-powered web app that helps users practice and improve their **Tamil pronunciation**. Users record themselves speaking a given phrase, and the system analyzes their speech — comparing it against expected pronunciation, phonemes, and prosody — to give real-time feedback and a score.

Built for "DTEC 2026 Hackathon - Advancing Tamil Digital Learning with AI" 2026.

---

## Features

-  **Voice Recording** — Record your pronunciation attempt directly in the browser
-  **Speech-to-Text** — Converts spoken Tamil audio into text for analysis
-  **Pronunciation Scoring** — Compares phonemes and acoustic features against reference pronunciation
-  **Prosody Analysis** — Evaluates rhythm, stress, and intonation
-  **Feedback Generation** — Personalized, actionable feedback on what to improve
-  **TTS Coach** — Hear the correct pronunciation as a model to follow
-  **Score Card UI** — Visual breakdown of performance after each attempt

---

##  Tech Stack

**Frontend**
- React + TypeScript
- Vite
- Custom CSS theming

**Backend**
- Python (FastAPI)
- Speech-to-Text engine
- Acoustic & phoneme-based pronunciation scoring
- Text-to-Speech for model pronunciation

---

## Project Structure

```
proj_tamil_2.0/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── api/
│   │   │   └── pronunciation.py     # API routes
│   │   ├── data/
│   │   │   ├── lessons.json         # Practice lessons/phrases
│   │   │   └── tamil_rules.json     # Tamil phonetic rules
│   │   ├── models/                  # Request/response schemas
│   │   ├── services/                # Core logic (STT, scoring, TTS, etc.)
│   │   ├── utils/                   # Helper utilities
│   │   ├── generated_audio/         # TTS output audio
│   │   └── uploads/                 # User-recorded audio
│   ├── tests/                       # Backend test suite
│   ├── requirements.txt
│   └── .env
│
└── frontend2/
    ├── src/
    │   ├── app/                     # Pages (index, practice, result)
    │   ├── components/               # Recorder, ScoreCard, FeedbackCard
    │   ├── services/                 # API client
    │   └── styles/                  # Theming
    └── package.json
```

---

## Prerequisites

Make sure you have the following installed:

- **Python** 3.10.11
- **Node.js** 18+ and **npm**
- **Git**

---

## Getting Started

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd proj_tamil_2.0
```

### 2. Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` folder (if not already present) with the required environment variables, for example:

```env
# Example — replace with your actual keys/config
ENV=development
DEBUG=True
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./data/app.db
GEMINI_API_KEY=YOUR-GEMINI-KEY
API_KEY=OPENAI-KEY
BASE_URL=YOUR-BASE-URL-FOR-API-KEY
WHISPER_MODEL_SIZE=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_CPU_THREADS=1
WHISPER_NUM_WORKERS=1
```

Run the backend server:

```bash
uvicorn app.main:app --reload
```

The backend should now be running at:
 `http://127.0.0.1:8000`

You can view the interactive API docs at:
 `http://127.0.0.1:8000/docs`

### 3. Frontend Setup

Open a **new terminal window**, then:

```bash
cd frontend2
npm install
npm install react-router-dom
npm run dev
```

The frontend should now be running at:
 `http://localhost:5173`

### 4. Using the App

1. Open the frontend URL in your browser
2. Click record and speak the phrase in Tamil
3. Submit your recording for analysis
4. View your pronunciation score and feedback

---

##  Running Tests (Backend)

```bash
cd backend
pytest tests/
```

---

## Future Improvements

- Support for more Tamil dialects/accents
- Progress tracking and lesson history per user
- Gamified learning paths
- Mobile app version

---

## Team

- Mouleeshwarran A G — Team lead 
- Guru Prakash P — Frontend
- Vinu Priya V — Backend

---

## License

This project was built for hackathon purposes. License details TBD.
