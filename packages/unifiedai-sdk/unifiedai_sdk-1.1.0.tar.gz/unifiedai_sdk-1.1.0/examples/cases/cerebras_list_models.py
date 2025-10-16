import json
import os

from unifiedai import Cerebras

client = Cerebras(api_key=os.getenv("CEREBRAS_API_KEY"))

# Returns ModelListResponse (matches Cerebras SDK format)
response = client.models.list()

# Access models via .data (just like Cerebras SDK)
models_data = [model.model_dump() for model in response.data]
print(json.dumps(models_data, indent=2))
