from langgraph.graph import StateGraph, END
from src.state.state import AgentState
from src.nodes.nodes import call_llm, call_tool


graph = StateGraph(AgentState)

graph.add_node("llm", call_llm)
graph.add_node("tool", call_tool)


def should_continue(state):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool"
    return "end"


graph.add_conditional_edges("llm", should_continue, {"tool": "tool", "end": END})
graph.add_edge("tool", "llm")
graph.set_entry_point("llm")

runnable = graph.compile()
