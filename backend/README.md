# Tamil Pronunciation API Backend

A FastAPI backend service for evaluating and providing feedback on Tamil pronunciation.

## Project Structure

```
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── pronunciation.py
│   ├── services/
│   │   ├── speech_to_text.py
│   │   ├── phonemes.py
│   │   ├── acoustic_scorer.py
│   │   ├── pronunciation_scorer.py
│   │   └── feedback_generator.py
│   ├── models/
│   │   ├── request_models.py
│   │   └── response_models.py
│   ├── utils/
│   │   ├── audio_utils.py
│   │   └── text_utils.py
│   └── data/
│       ├── lessons.json
│       └── tamil_rules.json
├── uploads/
│   └── temp_audio/
├── tests/
│   ├── test_stt.py
│   ├── test_phonemes.py
│   └── test_scoring.py
├── requirements.txt
├── .env
└── README.md
```

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python -m app.main
   ```

## API Endpoints

- `POST /api/evaluate` - Evaluate pronunciation from audio file

## Testing

Run tests with pytest:
```bash
pytest tests/
```
