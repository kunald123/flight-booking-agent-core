from langchain_core.messages import SystemMessage, ToolMessage
from src.llm.llm import llm
from src.tools.tools import tools

llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = SystemMessage(content="""\
You are a helpful flight booking assistant.
You help users search for flights, book them, and process payments.

When the user asks to find or book a flight, extract:
- departure airport IATA code
- arrival airport IATA code
- departure date (YYYY-MM-DD)
- return date (YYYY-MM-DD), if mentioned

Workflow:
1. Use search_flights to show available options.
2. When the user picks a flight, use book_flight to create the reservation.
3. After booking, ask the user for payment details: card type (visa, mastercard, or amex), card number, and expiration date (MM/YYYY). The UI will collect these securely.
4. The user will provide: card type, an encrypted card token, the last four digits, and expiration date. Use process_payment with the flight_id, card_type, the encrypted_card_number token (NOT the last four digits), expiration_date, and the flight price as amount.
5. Only after successful payment, confirm the booking is complete.

IMPORTANT: Never log or display full card numbers. Only reference the last four digits when confirming with the user.
Always confirm booking details before calling book_flight.
Always confirm payment details before calling process_payment.
After a tool call, summarise the results clearly for the user.
""")

_tool_map = {t.name: t for t in tools}


def call_llm(state):
    messages = [SYSTEM_PROMPT] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


async def call_tool(state):
    last_message = state["messages"][-1]
    results = []
    payment_status = state.get("payment_status", "")
    for tc in last_message.tool_calls:
        output = await _tool_map[tc["name"]].ainvoke(tc["args"])
        results.append(
            ToolMessage(content=str(output), tool_call_id=tc["id"])
        )
        if tc["name"] == "process_payment":
            if "success" in str(output).lower():
                payment_status = "completed"
            else:
                payment_status = "failed"
        elif tc["name"] == "book_flight":
            payment_status = "pending"
    return {"messages": results, "payment_status": payment_status}
