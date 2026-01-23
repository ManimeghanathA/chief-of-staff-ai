from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from langchain_core.messages import HumanMessage
import json

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

MEMORY_PROMPT = """
You are a memory extraction engine.

From the message below, extract long-term personal preferences or facts.
Only extract things that would be useful later (preferences, dislikes, habits).

Return ONLY valid JSON in this exact format:
[
  {{"key": "preference_or_fact", "value": "description"}}
]

If nothing is worth remembering, return [].

Message:
{message}
"""


def extract_and_store_memory(state, db, source: str = "chat", text: str = None):
    """
    Extract and store memories from text.
    
    Args:
        state: AgentState with user_id
        db: Database session
        source: "chat" or "email"
        text: Text to extract from (defaults to state.message)
    """
    try:
        text_to_extract = text if text is not None else state.message
        
        response = llm.invoke([
            HumanMessage(
                content=MEMORY_PROMPT.format(message=text_to_extract)
            )
        ])

        content = response.content.strip()

        # Try to find JSON array in response
        start = content.find("[")
        end = content.rfind("]") + 1
        
        if start == -1 or end == 0:
            return state

        facts = json.loads(content[start:end])
        
        if not facts:
            return state

        from app.agent.memory import save_user_memory
        save_user_memory(db, state.user_id, facts, source=source)

    except ChatGoogleGenerativeAIError as e:
        # Silently skip memory extraction if rate limited (non-critical feature)
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
            print(f"⚠️ Memory extraction skipped ({source}): Rate limit reached")
        else:
            print(f"⚠️ Memory extraction failed ({source}):", e)
    except Exception as e:
        print(f"⚠️ Memory extraction failed ({source}):", e)

    return state
