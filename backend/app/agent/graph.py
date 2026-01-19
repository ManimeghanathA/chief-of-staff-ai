from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.schemas import AgentState
from app.agent.memory import load_user_memory, save_user_memory

import json
import re
import os

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)





def load_memory_node(state: AgentState, config):
    db = config.get("configurable", {}).get("db")
    if db:
        memory = load_user_memory(db, state.user_id)
        state.memory = memory
    return state


def chat_node(state: AgentState, config):
    system_prompt = (
        "You are a personal AI assistant. "
        "Use the user's memory if relevant.\n\n"
        f"User memory: {state.memory}"
    )

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=state.message)
        ])
        state.response = response.content
    except Exception:
        state.response = "I'm temporarily unavailable. Please try again."

    return state


def extract_memory_node(state: AgentState, config):
    db = config.get("configurable", {}).get("db")
    if not db:
        return state

    extract_prompt = (
        "From the message below, extract any long-term personal facts "
        "as key-value pairs.\n"
        "Return ONLY valid JSON like:\n"
        "[{\"key\": \"...\", \"value\": \"...\"}]\n"
        "If none, return []\n\n"
        f"Message: {state.message}"
    )

    result = llm.invoke([
        HumanMessage(content=extract_prompt)
    ])

    try:
        content = result.content.strip()
        # Try to isolate JSON
        start = content.find("[")
        end = content.rfind("]") + 1
        if start != -1 and end != -1:
            facts = json.loads(content[start:end])
            if isinstance(facts, list):
                save_user_memory(db, state.user_id, facts)
    except Exception:
        # ✅ SILENT FAIL (EXPECTED)
        pass

    return state



def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("load_memory", load_memory_node)
    graph.add_node("chat", chat_node)
    graph.add_node("extract_memory", extract_memory_node)

    graph.set_entry_point("load_memory")
    graph.add_edge("load_memory", "chat")
    graph.add_edge("chat", "extract_memory")
    graph.add_edge("extract_memory", END)

    return graph.compile()
