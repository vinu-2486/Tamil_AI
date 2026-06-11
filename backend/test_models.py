from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

print("KEY FOUND:", bool(os.getenv("BLUESMINDS_API_KEY")))

client = OpenAI(
    api_key=os.getenv("BLUESMINDS_API_KEY"),
    base_url="https://api.bluesminds.com/v1"
)

for model in client.models.list().data:
    print(repr(model.id))