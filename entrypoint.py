"""
Amazon Bedrock AgentCore Runtime entrypoint for the flight booking agent.

Local test:
    python entrypoint.py
    curl -X POST http://localhost:8080/invocations \
         -H "Content-Type: application/json" \
         -d '{"prompt": "Find flights from JFK to LAX on 2026-05-10 returning 2026-05-17"}'

Deploy:
    agentcore configure -e entrypoint.py
    agentcore deploy
    agentcore invoke '{"prompt": "Book me a flight from SFO to ORD on 2026-06-01"}'
"""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from src.graph.graph import runnable
from langchain_core.messages import HumanMessage, AIMessage

app = BedrockAgentCoreApp()


import asyncio

@app.entrypoint
def invoke(payload, context=None):
    user_message = payload.get(
        "prompt",
        "No prompt found. Send a JSON payload with a 'prompt' key.",
    )

    messages = []
    for msg in payload.get("history", []):
        if msg.get("type") == "human":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg.get("type") == "ai":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_message))

    response = asyncio.run(runnable.ainvoke({"messages": messages, "user_query": user_message, "payment_status": ""}))  # type: ignore
    return {"result": response["messages"][-1].content}


if __name__ == "__main__":
    app.run()
