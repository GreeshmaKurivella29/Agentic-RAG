import os
from dotenv import load_dotenv
load_dotenv(override=True)
from groq import Groq

client = Groq(api_key=os.getenv('GROQ_API_KEY'))
model = os.getenv('GROQ_MODEL', 'qwen/qwen3.8-27b')

prompt = """You are NyayaRoute, an Indian legal research assistant. Use only supplied sources. Do not give legal advice, invent authorities, or state that a source proves more than it says. Use exactly these headings: **Short answer**, **Relevant authority**, **What this means**, **Limits / next verification**. Cite each material proposition as [S1], [S2], etc. End with: 'This is legal research information, not legal advice.'

Question: What does Article 21 of the Constitution protect?

Sources:
[S1] Constitution of India — Article 21
Source: India Code
URL: https://www.indiacode.nic.in/
Article 21. Protection of life and personal liberty.—No person shall be deprived of his life or personal liberty except according to procedure established by law.
"""

resp = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "You are a legal research assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.1,
    max_tokens=600
)

print(f"MODEL USED: {model}")
print(resp.choices[0].message.content)
