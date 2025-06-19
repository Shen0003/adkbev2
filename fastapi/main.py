from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests

app = FastAPI()

# --- Configuration ---
BASE_URL = "http://localhost:8000"  # ADK backend
AGENT_NAME = "multi_tool_agent"
USER_ID = "u_2222"
SESSION_ID = "s_2222"

@app.get("/")
async def root():
    return {"message": "Hello from the ADK FastAPI wrapper!"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.post("/ask-agent")
async def ask_agent(request: Request):
    body = await request.json()
    user_query = body.get("query")

    if not user_query:
        return JSONResponse(status_code=400, content={"error": "Missing 'query' in request body."})

    # 1. Create a session (optional if already exists)
    session_url = f"{BASE_URL}/apps/{AGENT_NAME}/users/{USER_ID}/sessions/{SESSION_ID}"
    session_payload = {"state": {"key1": "value1", "key2": 42}}
    requests.post(session_url, json=session_payload)  # We assume idempotent

    # 2. Send a message to the agent
    run_url = f"{BASE_URL}/run"
    run_payload = {
        "appName": AGENT_NAME,
        "userId": USER_ID,
        "sessionId": SESSION_ID,
        "newMessage": {
            "role": "user",
            "parts": [
                {"text": user_query}
            ]
        }
    }

    run_resp = requests.post(run_url, json=run_payload)
    try:
        data = run_resp.json()
        text_responses = []
        for item in data:
            parts = item.get("content", {}).get("parts", [])
            for part in parts:
                if "text" in part:
                    text_responses.append(part["text"])

        if text_responses:
            return {"response": text_responses[-1].strip()}
        else:
            return {"response": "No text found in agent response."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
