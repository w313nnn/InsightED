import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GONKA_API_KEY"),
    base_url="https://api.gonkarouter.io/v1"
)

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V4-Flash-0731",
    messages=[
        {"role": "user", "content": "Say hello and tell me you are working."}
    ]
)

print(response.choices[0].message.content)