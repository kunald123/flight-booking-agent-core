from typing import TypedDict, Annotated, List
import operator
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """State for the flight booking agent."""
    messages: Annotated[List[BaseMessage], operator.add]
    user_query: str
    payment_status: str
