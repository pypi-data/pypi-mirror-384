import os

from unifiedai import UnifiedAI

api_key = os.getenv("CEREBRAS_API_KEY", "<your-cerebras-api-key>")
client = UnifiedAI(provider="cerebras", credentials={"api_key": api_key})
resp = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}], model="qwen-3-32b"
)
print("resp", resp.choices[0].message["content"])
