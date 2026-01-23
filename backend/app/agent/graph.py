from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
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

# -------- meeting helpers --------
def _parse_iso_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _event_time_range(event: dict) -> tuple[datetime | None, datetime | None]:
    """
    Google events can have dateTime or date (all-day). We handle dateTime reliably.
    """
    start_raw = (event.get("start") or {}).get("dateTime") or (event.get("start") or {}).get("date")
    end_raw = (event.get("end") or {}).get("dateTime") or (event.get("end") or {}).get("date")
    if not start_raw or not end_raw:
        return None, None
    return _parse_iso_datetime(start_raw), _parse_iso_datetime(end_raw)


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    # Treat intervals as [start, end)
    return a_start < b_end and b_start < a_end


def extract_meeting_title(text: str) -> str | None:
    """
    Extract a meeting title from common patterns:
    - titled "X"
    - called "X"
    - named "X"
    - title: X
    - "X" (quoted text before time)
    - X (text before "from" or time pattern)
    """
    import re

    patterns = [
        r'(?:titled|called|named)\s+"([^"]+)"',
        r"(?:titled|called|named)\s+'([^']+)'",
        r"(?:title|subject)\s*:\s*([^\n]+)",
        r'"([^"]+)"',  # Any quoted text
        r"'([^']+)'",  # Any single-quoted text
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            title = m.group(1).strip()
            # Trim trailing punctuation
            title = title.strip(" .,!;:")
            if title and len(title) > 1:  # Must be at least 2 chars
                return title
    
    # If no quoted title, try to extract text before "from" or time pattern
    # Example: "Team Standup from 9am to 10am"
    time_pattern = r'\s+from\s+\d'
    if re.search(time_pattern, text, flags=re.IGNORECASE):
        # Extract text before "from"
        parts = re.split(time_pattern, text, flags=re.IGNORECASE, maxsplit=1)
        if len(parts) > 0:
            potential_title = parts[0].strip()
            # Remove common prefixes
            for prefix in ["schedule", "create", "book", "set up", "add", "a meeting", "meeting"]:
                if potential_title.lower().startswith(prefix):
                    potential_title = potential_title[len(prefix):].strip()
            # Remove trailing words that are likely not part of title
            potential_title = re.sub(r'\s+(for|on|at|with|to)\s*$', '', potential_title, flags=re.IGNORECASE)
            if potential_title and len(potential_title) > 1:
                return potential_title.strip(" .,!;:")
    
    return None


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
    '11pm to 12am' (handles midnight correctly)
    Returns (start_datetime, end_datetime) or (None, None)
    """

    match = re.search(r"from (\d{1,2})\s*(am|pm)?\s*to\s*(\d{1,2})\s*(am|pm)?", text, re.IGNORECASE)
    if not match:
        return None, None

    start_hour = int(match.group(1))
    end_hour = int(match.group(3))
    start_ampm = (match.group(2) or "").lower()
    end_ampm = (match.group(4) or "").lower()

    # Handle 12am (midnight) and 12pm (noon) correctly
    if start_hour == 12:
        start_hour = 0  # 12am = 0, 12pm = 12 (handled below)
    if end_hour == 12:
        end_hour = 0  # 12am = 0, 12pm = 12 (handled below)

    # AM/PM handling
    if start_ampm == "pm" and start_hour < 12:
        start_hour += 12
    if end_ampm == "pm" and end_hour < 12:
        end_hour += 12
    
    # Special case: if end is 12am (midnight), it's the next day
    if end_ampm == "am" and end_hour == 0 and start_hour >= 12:
        # This is likely "11pm to 12am" meaning 11pm to midnight (next day)
        pass  # We'll handle this below

    today = datetime.utcnow()
    is_tomorrow = "tomorrow" in text.lower()

    start_time = today.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end_time = today.replace(hour=end_hour, minute=0, second=0, microsecond=0)

    # Handle tomorrow
    if is_tomorrow:
        start_time += timedelta(days=1)
        end_time += timedelta(days=1)
    
    # Handle midnight crossing (e.g., 11pm to 12am)
    if end_hour == 0 and end_ampm == "am" and start_hour >= 12:
        # End time is midnight of next day
        if is_tomorrow:
            end_time += timedelta(days=1)
        else:
            end_time += timedelta(days=1)
    
    # Validation: end time must be after start time
    if end_time <= start_time:
        # If end is before or equal to start, assume it's next day
        end_time += timedelta(days=1)

    return start_time, end_time



def intent_router_node(state: AgentState, config):
    text = state.message.lower()

    # -------- CALENDAR INTENTS --------
    if "meeting" in text or "calendar" in text:

        # CREATE/SCHEDULE MEETING
        # Check for scheduling keywords OR time patterns (for follow-up messages)
        has_schedule_keyword = any(kw in text for kw in ["create", "schedule", "book", "set up", "add"])
        has_time_pattern = bool(extract_time_range(state.message)[0])  # Check if time can be extracted
        has_title_keyword = any(kw in text for kw in ["titled", "called", "named", "title"])
        
        if has_schedule_keyword or (has_time_pattern and has_title_keyword):
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

    try:
        events = fetch_upcoming_events(
            user_id=state.user_id,
            db=db,
            max_results=5
        )
    except TimeoutError as e:
        state.response = (
            "I couldn't fetch your calendar for today (Google Calendar API timeout).\n\n"
            "This might be due to:\n"
            "- Slow network connection\n"
            "- Google Calendar API being temporarily unavailable\n\n"
            "Try:\n"
            "- Click 'Connect Google' again to refresh permissions\n"
            "- Wait a moment and try again\n"
            "- Check your internet connection"
        )
        return state
    except Exception as e:
        state.response = (
            "I couldn't fetch your calendar for today (Google Calendar API error).\n\n"
            "Try:\n"
            "- Click 'Connect Google' again to refresh permissions\n"
            "- Then retry: 'What meetings do I have today?'\n\n"
            f"Details: {type(e).__name__}"
        )
        return state

    if not events:
        state.response = "You have no meetings scheduled for today."
        return state

    # Filter events for today
    today = datetime.utcnow().date()
    today_events = []
    for e in events:
        start_raw = e["start"].get("dateTime", e["start"].get("date"))
        try:
            start_dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
            if start_dt.date() == today:
                today_events.append(e)
        except Exception:
            # If date parsing fails, include it anyway (better than missing events)
            today_events.append(e)

    if not today_events:
        state.response = "You have no meetings scheduled for today."
        return state

    # Format meetings nicely - each on new line
    lines = []
    for e in today_events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        summary = e.get("summary", "Untitled meeting")
        # Format time nicely
        try:
            if "T" in start:
                dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                time_str = dt.strftime("%I:%M %p")
                lines.append(f"• {summary} at {time_str}")
            else:
                lines.append(f"• {summary} at {start}")
        except Exception:
            lines.append(f"• {summary} at {start}")

    state.response = "📅 Your Meetings Today\n\n" + "\n".join(lines)
    return state


# ---------- FALLBACK CHAT ----------
def chat_node(state: AgentState, config):
    """Chat node with memory context."""
    # Check if this might be a scheduling follow-up (has time or title keywords)
    text_lower = state.message.lower()
    has_time = bool(extract_time_range(state.message)[0])
    has_title = any(kw in text_lower for kw in ["titled", "called", "named", "title", "meeting"])
    
    # If chat node receives scheduling details as follow-up, extract and route
    # This handles cases where user says "I want to schedule" then provides details in next message
    if has_time and has_title:
        # Looks like scheduling details - extract and route to calendar_create
        start, end = extract_time_range(state.message)
        if start and end:
            state.intent = "calendar_create"
            state.start_time = start
            state.end_time = end
            # Return state with intent set - the graph will route it properly on next invocation
            # For now, just hint to user that they should provide full details
            state.response = (
                "I see you're providing meeting details! Please include everything in one message:\n\n"
                "Example: 'Schedule a meeting titled \"Team Standup\" tomorrow from 9am to 10am'\n\n"
                "Or: 'Create \"Project Review\" today from 2pm to 3pm'"
            )
            return state
    
    # Format memory for better readability
    memory_text = ""
    if state.memory:
        memory_items = [f"- {m['key']}: {m['value']}" for m in state.memory]
        memory_text = f"\n\nUser's remembered preferences and facts:\n" + "\n".join(memory_items)
    
    system_prompt = (
        "You are a Chief-of-Staff AI assistant.\n"
        "You help users manage their day, emails, and calendar.\n"
        "Use the user's remembered preferences when responding.\n"
        "If you cannot perform an action, explain politely."
        + memory_text
    )

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=state.message)
        ])
        state.response = response.content
    except ChatGoogleGenerativeAIError as e:
        # Handle rate limit errors gracefully
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
            state.response = (
                "⚠️ I've hit the daily rate limit for AI requests (free tier: 20 requests/day).\n\n"
                "Please wait a few minutes and try again, or continue tomorrow.\n\n"
                "You can still use calendar and email features that don't require AI!"
            )
        else:
            state.response = f"Sorry, I encountered an AI service error. Please try again later.\n\nError: {type(e).__name__}"
    except Exception as e:
        state.response = f"Sorry, I encountered an unexpected error. Please try again.\n\nError: {type(e).__name__}"
    
    return state


# ---------- MEMORY EXTRACTION ----------
def extract_memory_node(state: AgentState, config):
    """Extract and store memories from user messages."""
    db = config["configurable"]["db"]
    
    from app.agent.memory_extractor import extract_and_store_memory
    return extract_and_store_memory(state, db)

#------------Calendar tomorrow node-------------
def calendar_tomorrow_node(state: AgentState, config):
    db = config.get("configurable", {}).get("db")

    try:
        events = fetch_upcoming_events(
            user_id=state.user_id,
            db=db,
            max_results=5
        )
    except Exception as e:
        # Most common causes: Google API timeout, revoked consent, expired refresh token.
        state.response = (
            "I couldn't fetch your calendar for tomorrow (Google Calendar API error/timeout).\n\n"
            "Try:\n"
            "- Click “Connect Google” again to refresh permissions\n"
            "- Then retry: “What meetings do I have tomorrow?”\n\n"
            f"Details: {type(e).__name__}"
        )
        return state

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

    # Format meetings nicely - each on new line
    lines = []
    for e in tomorrow_events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        summary = e.get("summary", "Untitled meeting")
        # Format time nicely
        try:
            if "T" in start:
                dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                time_str = dt.strftime("%I:%M %p")
                lines.append(f"• {summary} at {time_str}")
            else:
                lines.append(f"• {summary} at {start}")
        except Exception:
            lines.append(f"• {summary} at {start}")

    state.response = "📆 Your Meetings Tomorrow\n\n" + "\n".join(lines)
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

    # Format emails professionally - each email clearly separated with better spacing
    formatted_emails = []
    for i, e in enumerate(emails, 1):
        subject = e.get('subject', 'No Subject')
        sender = e.get('from', 'Unknown Sender')
        # Clean up sender (remove email if it's in brackets)
        if '<' in sender:
            sender = sender.split('<')[0].strip().strip('"').strip("'")
        # Each email on its own block with clear separation
        formatted_emails.append(f"{i}. {subject}\n   From: {sender}")
    
    # Join with triple newlines for maximum visual separation between emails
    state.response = "📧 Emails Received Today\n\n" + "\n\n\n".join(formatted_emails)
    
    # Extract memory from email subjects/content
    email_text = "\n".join([f"From: {e['from']} | Subject: {e['subject']}" for e in emails])
    from app.agent.memory_extractor import extract_and_store_memory
    extract_and_store_memory(state, db, source="email", text=email_text)
    
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

    # Format emails professionally - each email clearly separated with better spacing
    formatted_emails = []
    for i, e in enumerate(emails, 1):
        subject = e.get('subject', 'No Subject')
        sender = e.get('from', 'Unknown Sender')
        # Clean up sender (remove email if it's in brackets)
        if '<' in sender:
            sender = sender.split('<')[0].strip().strip('"').strip("'")
        # Each email on its own block with clear separation
        formatted_emails.append(f"{i}. {subject}\n   From: {sender}")
    
    # Join with triple newlines for maximum visual separation between emails
    state.response = "📧 Emails Received Yesterday\n\n" + "\n\n\n".join(formatted_emails)
    
    # Extract memory from email subjects/content
    email_text = "\n".join([f"From: {e['from']} | Subject: {e['subject']}" for e in emails])
    from app.agent.memory_extractor import extract_and_store_memory
    extract_and_store_memory(state, db, source="email", text=email_text)
    
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

    # Format emails for LLM processing (cleaner format)
    email_list = []
    for e in emails:
        subject = e.get('subject', 'No Subject')
        sender = e.get('from', 'Unknown Sender')
        if '<' in sender:
            sender = sender.split('<')[0].strip().strip('"').strip("'")
        email_list.append(f"Subject: {subject}\nFrom: {sender}")
    email_text = "\n\n".join(email_list)

    # Format memory for context
    memory_text = ""
    if state.memory:
        memory_items = [f"- {m['key']}: {m['value']}" for m in state.memory]
        memory_text = f"\n\nUser's remembered preferences:\n" + "\n".join(memory_items)

    prompt = (
        "You are a Chief-of-Staff AI.\n"
        "From the emails below, identify which are important "
        "(work, deadlines, meetings, actions) and summarize them.\n"
        "Use the user's preferences when prioritizing."
        + memory_text
        + f"\n\nEmails:\n{email_text}"
    )

    try:
        # ChatGoogleGenerativeAI can be finicky with SystemMessage-only inputs in some versions.
        # Use a HumanMessage prompt for reliability.
        summary = llm.invoke([HumanMessage(content=prompt)])
        
        # Format the summary nicely
        summary_text = summary.content.strip()
        
        # Add header and formatting
        state.response = (
            "⭐ Important Emails Summary\n\n"
            + summary_text
            + "\n\n"
            f"📊 Based on {len(emails)} emails received today"
        )
    except ChatGoogleGenerativeAIError as e:
        # Handle rate limit errors gracefully
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
            state.response = (
                "⚠️ I've hit the daily rate limit for AI requests (free tier: 20 requests/day).\n\n"
                "I can still show you your emails, but I can't summarize them right now.\n"
                "Please wait a few minutes and try again, or ask: 'What emails did I receive today?'\n"
                "for a simple list instead."
            )
        else:
            state.response = (
                "I couldn't generate the important-email summary right now (AI service error).\n\n"
                "You can still ask:\n"
                "- “What emails did I receive today?”\n\n"
                f"Details: {type(e).__name__}"
            )
        return state
    except Exception as e:
        state.response = (
            "I couldn't generate the important-email summary right now (LLM error).\n\n"
            "You can still ask:\n"
            "- “What emails did I receive today?”\n\n"
            f"Details: {type(e).__name__}"
        )
        return state
    
    # Extract memory from email content
    from app.agent.memory_extractor import extract_and_store_memory
    extract_and_store_memory(state, db, source="email", text=email_text)
    
    return state

from app.tools.calendar_write_tool import create_calendar_event
from datetime import datetime, timedelta

def calendar_create_node(state: AgentState, config):
    db = config.get("configurable", {}).get("db")

    # Extract details from message
    title = extract_meeting_title(state.message)
    start_time = state.start_time
    end_time = state.end_time
    
    # Check what's missing and ask conversationally
    missing = []
    if not title:
        missing.append("**meeting name/title**")
    if not start_time or not end_time:
        missing.append("**time** (start and end)")
    
    if missing:
        # Format the missing items nicely
        if len(missing) == 2:
            missing_text = f"{missing[0]} and {missing[1]}"
        else:
            missing_text = missing[0]
        
        state.response = (
            "I'd be happy to schedule a meeting for you! 📅\n\n"
            f"I just need the {missing_text}.\n\n"
            "Please provide:\n"
        )
        
        if not title:
            state.response += "- Meeting name (e.g., 'Team Standup', 'Project Review')\n"
        if not start_time or not end_time:
            state.response += "- Time (e.g., 'from 9am to 10am' or '2pm to 3pm')\n"
            state.response += "- Date (today or tomorrow)\n"
        
        state.response += (
            "\nExample:\n"
            "Schedule a meeting titled \"Team Standup\" tomorrow from 9am to 10am\n"
            "or\n"
            "Create \"Project Review\" today from 2pm to 3pm"
        )
        return state

    # Check for clashes in the next week window (good enough for tomorrow/today scheduling).
    try:
        upcoming = fetch_upcoming_events(user_id=state.user_id, db=db, max_results=15)
    except Exception as e:
        state.response = (
            "I couldn't check your calendar for conflicts (Google Calendar API error/timeout).\n\n"
            f"Details: {type(e).__name__}"
        )
        return state

    clashes: list[str] = []
    same_exact = False
    for ev in upcoming or []:
        ev_start, ev_end = _event_time_range(ev)
        if not ev_start or not ev_end:
            continue
        if _overlaps(state.start_time, state.end_time, ev_start, ev_end):
            ev_title = ev.get("summary") or "Untitled meeting"
            ev_start_raw = (ev.get("start") or {}).get("dateTime") or (ev.get("start") or {}).get("date") or "unknown time"
            clashes.append(f"- {ev_title} at {ev_start_raw}")
            if ev_title.strip().lower() == title.strip().lower():
                # If same title and overlapping, treat as likely duplicate.
                same_exact = True

    if same_exact:
        state.response = (
            "This looks like a duplicate: you already have a meeting with the same title in that time window.\n"
            "I won't create it again."
        )
        return state

    if clashes:
        state.response = (
            "That time conflicts with existing events:\n"
            + "\n".join(clashes)
            + "\n\nPlease choose a different time."
        )
        return state

    # Validate time range before creating
    if state.end_time <= state.start_time:
        state.response = (
            "❌ Invalid time range: The end time must be after the start time.\n\n"
            f"Start: {state.start_time.strftime('%I:%M %p')}\n"
            f"End: {state.end_time.strftime('%I:%M %p')}\n\n"
            "Please provide a valid time range, for example:\n"
            "- 'from 9am to 10am'\n"
            "- 'from 11pm to 12am' (midnight)\n"
            "- 'from 2pm to 3pm'"
        )
        return state
    
    try:
        event = create_calendar_event(
            user_id=state.user_id,
            db=db,
            title=title,
            start_time=state.start_time,
            end_time=state.end_time,
        )
    except Exception as e:
        error_msg = str(e)
        if "time range is empty" in error_msg.lower() or "timeRangeEmpty" in error_msg:
            state.response = (
                "❌ Invalid time range: The end time must be after the start time.\n\n"
                "Please check your times. For example:\n"
                "- '11pm to 12am' means 11pm to midnight (next day)\n"
                "- '11pm to 12pm' is invalid (12pm is noon, not midnight)\n\n"
                "Try: '11pm to 12am' or '11pm to 11:59pm'"
            )
        else:
            state.response = (
                f"I couldn't create the meeting (Google Calendar API error).\n\n"
                f"Error: {type(e).__name__}\n\n"
                "Please try again or check your Google Calendar permissions."
            )
        return state

    # Format the response nicely
    start_formatted = state.start_time.strftime("%I:%M %p")
    end_formatted = state.end_time.strftime("%I:%M %p")
    date_str = state.start_time.strftime("%B %d, %Y")
    
    state.response = (
        f"✅ Meeting Scheduled Successfully!\n\n"
        f"📅 {title}\n"
        f"🕐 {start_formatted} - {end_formatted}\n"
        f"📆 {date_str}\n\n"
        f"🔗 View in Calendar: {event.get('htmlLink')}"
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


    # Add memory extraction to all nodes that process user data
    graph.add_edge("calendar_today", END)
    graph.add_edge("calendar_tomorrow", END)
    graph.add_edge("calendar_create", END)
    graph.add_edge("gmail_today", END)
    graph.add_edge("gmail_yesterday", END)
    graph.add_edge("gmail_today_summary", END)
    graph.add_edge("chat", "extract_memory")
    graph.add_edge("extract_memory", END)

    return graph.compile()
