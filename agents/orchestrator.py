import os, openai

GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_BASE_URL = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")

client = openai.OpenAI(api_key=GROK_API_KEY, base_url=GROK_BASE_URL)

def plan_task(task_description):
    response = client.chat.completions.create(
        model="grok-1",
        messages=[
            {"role": "system", "content": "You are a software architect. Break down the task into microservice actions."},
            {"role": "user", "content": task_description}
        ]
    )
    return response.choices[0].text
