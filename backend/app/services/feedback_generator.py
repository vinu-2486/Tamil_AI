import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)

MODEL_NAME = "gpt-4o"


def generate_feedback(transcript):

    prompt = f"""
You are a Tamil pronunciation coach.

Transcript:
{transcript}

Analyze the pronunciation quality.

Return ONLY valid JSON:

{{
    "score": 85,
    "feedback": "Short feedback sentence.",
    "improvements": [
        "Improvement 1",
        "Improvement 2",
        "Improvement 3"
    ]
}}
"""

    try:

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        text = response.choices[0].message.content.strip()

        print("RAW MODEL RESPONSE:")
        print(text)

        # Remove markdown if model adds it
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

        parsed = json.loads(text)

        return parsed

    except Exception as e:

        print("BluesMinds Error:", str(e))

        return {
            "score": 0,
            "feedback": "Unable to generate feedback",
            "improvements": [
                "Please try again"
            ]
        }