from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.schemas import AgentState
from app.agent.memory import load_user_memory, save_user_memory
from app.tools.calendar_read_tool import fetch_upcoming_events
from app.tools.gmail_read_tool import fetch_gmail_messages_for_date


from datetime import datetime, timedelta
import json

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

# ---------- MEMORY ----------
def load_memory_node(state: AgentState, config):
    db = config["configurable"]["db"]
    state.memory = load_user_memory(db, state.user_id)
    return state

# -------- re helper function --------
import re
from datetime import datetime, timedelta

def extract_time_range(text: str):
    """
    Extracts simple time ranges like:
    'from 10 to 11'
    '10am to 11am'
    Returns (start_datetime, end_datetime) or (None, None)
    """

    match = re.search(r"from (\d{1,2})\s*(am|pm)?\s*to\s*(\d{1,2})\s*(am|pm)?", text)
    if not match:
        return None, None

    start_hour = int(match.group(1))
    end_hour = int(match.group(3))

    # basic AM/PM handling
    if match.group(2) == "pm" and start_hour < 12:
        start_hour += 12
    if match.group(4) == "pm" and end_hour < 12:
        end_hour += 12

    today = datetime.utcnow()

    start_time = today.replace(hour=start_hour, minute=0, second=0)
    end_time = today.replace(hour=end_hour, minute=0, second=0)

    # tomorrow support
    if "tomorrow" in text.lower():
        start_time += timedelta(days=1)
        end_time += timedelta(days=1)

    return start_time, end_time



def intent_router_node(state: AgentState, config):
    text = state.message.lower()

    # -------- CALENDAR INTENTS --------
    if "meeting" in text or "calendar" in text:

        # CREATE MEETING
        if "create" in text or "schedule" in text:
            state.intent = "calendar_create"

            # ⏱ Extract time range if present
            start, end = extract_time_range(state.message)
            state.start_time = start
            state.end_time = end

            return state

        # READ MEETINGS
        if "today" in text:
            state.intent = "calendar_today"
            return state

        if "tomorrow" in text:
            state.intent = "calendar_tomorrow"
            return state

        # Missing info
        state.intent = "need_more_info"
        return state

    # -------- GMAIL INTENTS --------
    if "mail" in text or "email" in text:

        if "today" in text and ("important" in text or "summary" in text):
            state.intent = "gmail_today_summary"
            return state

        if "today" in text:
            state.intent = "gmail_today"
            return state

        if "yesterday" in text:
            state.intent = "gmail_yesterday"
            return state

        state.intent = "need_more_info"
        return state

    # -------- UNSUPPORTED --------
    state.intent = "unsupported"
    return state



# ---------- CALENDAR TOOL ----------
def calendar_today_node(state: AgentState, config):
    db = config["configurable"]["db"]

    events = fetch_upcoming_events(
        user_id=state.user_id,
        db=db,
        max_results=5
    )

    if not events:
        state.response = "You have no meetings scheduled for today."
        return state

    lines = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        summary = e.get("summary", "Untitled meeting")
        lines.append(f"- {summary} at {start}")

    state.response = "Here are your meetings today:\n" + "\n".join(lines)
    return state


# ---------- FALLBACK CHAT ----------
def chat_node(state: AgentState, config):
    system_prompt = (
        "You are a Chief-of-Staff AI assistant.\n"
        "If you cannot perform an action, explain politely.\n\n"
        f"User memory: {state.memory}"
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state.message)
    ])

    state.response = response.content
    return state


# ---------- MEMORY EXTRACTION ----------
def extract_memory_node(state: AgentState, config):
    db = config["configurable"]["db"]

    prompt = (
        "Extract long-term personal facts as JSON.\n"
        "Return [] if none.\n\n"
        f"Message: {state.message}"
    )

    result = llm.invoke([HumanMessage(content=prompt)])

    try:
        content = result.content.strip()
        start = content.find("[")
        end = content.rfind("]") + 1
        facts = json.loads(content[start:end])
        save_user_memory(db, state.user_id, facts)
    except Exception:
        pass

    return state

#------------Calendar tomorrow node-------------
def calendar_tomorrow_node(state: AgentState, config):
    db = config.get("configurable", {}).get("db")

    events = fetch_upcoming_events(
        user_id=state.user_id,
        db=db,
        max_results=5
    )

    tomorrow = (datetime.utcnow() + timedelta(days=1)).date()

    tomorrow_events = []
    for e in events:
        start_raw = e["start"].get("dateTime", e["start"].get("date"))
        start_dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))

        if start_dt.date() == tomorrow:
            tomorrow_events.append(e)

    if not tomorrow_events:
        state.response = "You have no meetings scheduled for tomorrow."
        return state

    lines = []
    for e in tomorrow_events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        summary = e.get("summary", "Untitled meeting")
        lines.append(f"- {summary} at {start}")

    state.response = "Here are your meetings tomorrow:\n" + "\n".join(lines)
    return state

# ------------ gmail today ----------
def gmail_today_node(state: AgentState, config):
    db = config.get("configurable", {}).get("db")

    emails = fetch_gmail_messages_for_date(
        user_id=state.user_id,
        db=db,
        days_ago=0
    )

    if not emails:
        state.response = "You didn’t receive any emails today."
        return state

    lines = [
        f"- {e['subject']} (from {e['from']})"
        for e in emails
    ]

    state.response = "Here are the emails you received today:\n" + "\n".join(lines)
    return state

#------------- gmail yesterday ---------
def gmail_yesterday_node(state: AgentState, config):
    db = config.get("configurable", {}).get("db")

    emails = fetch_gmail_messages_for_date(
        user_id=state.user_id,
        db=db,
        days_ago=1
    )

    if not emails:
        state.response = "You didn’t receive any emails yesterday."
        return state

    lines = [
        f"- {e['subject']} (from {e['from']})"
        for e in emails
    ]

    state.response = "Here are the emails you received yesterday:\n" + "\n".join(lines)
    return state

# -------------- gmail today summary -----------
def gmail_today_summary_node(state: AgentState, config):
    db = config.get("configurable", {}).get("db")

    emails = fetch_gmail_messages_for_date(
        user_id=state.user_id,
        db=db,
        days_ago=0,
        max_results=15
    )

    if not emails:
        state.response = "You didn’t receive any emails today."
        return state

    email_text = "\n".join(
        f"From: {e['from']} | Subject: {e['subject']}"
        for e in emails
    )

    prompt = (
        "You are a Chief-of-Staff AI.\n"
        "From the emails below, identify which are important "
        "(work, deadlines, meetings, actions) and summarize them.\n\n"
        f"{email_text}"
    )

    summary = llm.invoke(prompt)
    state.response = summary.content
    return state

from app.tools.calendar_write_tool import create_calendar_event
from datetime import datetime, timedelta

def calendar_create_node(state: AgentState, config):
    db = config.get("configurable", {}).get("db")

    # Safety check (very important)
    if not state.start_time or not state.end_time:
        state.response = (
            "I need the start time and end time to create the meeting. "
            "Please tell me the time."
        )
        return state

    # Default title
    title = "Meeting"

    event = create_calendar_event(
        user_id=state.user_id,
        db=db,
        title=title,
        start_time=state.start_time,
        end_time=state.end_time,
    )

    state.response = (
        f"✅ Your meeting has been created successfully.\n"
        f"🗓 {title}\n"
        f"🔗 {event.get('htmlLink')}"
    )

    return state





# ---------- GRAPH ----------
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("load_memory", load_memory_node)
    graph.add_node("intent_router", intent_router_node)
    graph.add_node("calendar_today", calendar_today_node)
    graph.add_node("calendar_tomorrow", calendar_tomorrow_node)
    graph.add_node("gmail_today", gmail_today_node)
    graph.add_node("gmail_yesterday", gmail_yesterday_node)
    graph.add_node("gmail_today_summary", gmail_today_summary_node)
    graph.add_node("calendar_create", calendar_create_node)
    graph.add_node("chat", chat_node)
    graph.add_node("extract_memory", extract_memory_node)

    graph.set_entry_point("load_memory")

    graph.add_edge("load_memory", "intent_router")

    graph.add_conditional_edges(
        "intent_router",
        lambda state: state.intent,
        {
            "calendar_today": "calendar_today",
            "calendar_tomorrow": "calendar_tomorrow",
            "calendar_create": "calendar_create", 
            "gmail_today": "gmail_today",
            "gmail_yesterday": "gmail_yesterday",
            "gmail_today_summary": "gmail_today_summary",
            "need_more_info": "chat",
            "unsupported": "chat",
        }
    )


    graph.add_edge("calendar_today", END)
    graph.add_edge("chat", "extract_memory")
    graph.add_edge("extract_memory", END)

    return graph.compile()
