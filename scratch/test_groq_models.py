import os
from dotenv import load_dotenv
load_dotenv(override=True)
from groq import Groq

client = Groq(api_key=os.getenv('GROQ_API_KEY'))
candidates = ['openai/gpt-oss-120b', 'qwen/qwen3.8-27b', 'openai/gpt-oss-20b']

for model_name in candidates:
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{'role': 'user', 'content': 'Say "Groq model active"'}],
            max_tokens=25
        )
        print(f"SUCCESS {model_name}: {resp.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"FAILED {model_name}: {e}")
