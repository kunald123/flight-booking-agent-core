"""Local FastAPI server for development/testing without AgentCore."""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from src.graph.graph import runnable

load_dotenv()

app = FastAPI(title="Flight Booking Agent")

CARD_ENCRYPTION_KEY = os.getenv("CARD_ENCRYPTION_KEY", "")
if not CARD_ENCRYPTION_KEY:
    CARD_ENCRYPTION_KEY = Fernet.generate_key().decode()
    print(f"WARNING: No CARD_ENCRYPTION_KEY set. Generated ephemeral key: {CARD_ENCRYPTION_KEY}")
fernet = Fernet(CARD_ENCRYPTION_KEY.encode() if isinstance(CARD_ENCRYPTION_KEY, str) else CARD_ENCRYPTION_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


class EncryptCardInput(BaseModel):
    card_number: str


@app.post("/encrypt_card")
async def encrypt_card(body: EncryptCardInput):
    """Encrypt card number server-side. Raw number never stored or logged."""
    cleaned = body.card_number.replace(" ", "").replace("-", "")
    encrypted = fernet.encrypt(cleaned.encode()).decode()
    last_four = cleaned[-4:]
    return {"encrypted_card_number": encrypted, "last_four": last_four}


class ChatInput(BaseModel):
    prompt: str
    history: list[dict] = []


@app.post("/chat")
async def chat(body: ChatInput):
    messages = []
    for msg in body.history:
        if msg.get("type") == "human":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg.get("type") == "ai":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=body.prompt))

    response = await runnable.ainvoke({"messages": messages, "user_query": body.prompt, "payment_status": ""})  # type: ignore
    return {"result": response["messages"][-1].content}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
