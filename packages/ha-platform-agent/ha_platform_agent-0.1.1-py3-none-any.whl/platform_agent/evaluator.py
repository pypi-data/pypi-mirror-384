import datetime
import asyncio

from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])  # or hardcoded if testing

EVALUATION_PROMPT = """
You are an AI code evaluator.

Today's date is: {state.today}

Compare these two code snippets:

Author Code:
{state.author_code}

User Code:
{state.user_code}

Decide whether the user's code correctly implements the same functionality (logic must match). Differences in style or structure are okay.

Return a JSON only, e.g.:
{{ "match": true or false, "reason": "...", "score": <0-10> }}
"""

def create_agent():
    return LlmAgent(
        name="evaluation_agent",
        model="gemini-2.0-flash",
        instruction=EVALUATION_PROMPT,
    )

async def _run_agent_async(author_code: str, user_code: str) -> str:
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="platform-agent", user_id="user", session_id="session1"
    )

    runner = Runner(
        agent=create_agent(),
        app_name="platform-agent",
        session_service=session_service
    )

    # User message (empty text) just to trigger the run
    content = types.Content(role="user", parts=[types.Part(text="")])

    session.state["today"] = datetime.date.today().isoformat()
    session.state["author_code"] = author_code
    session.state["user_code"] = user_code

    events = runner.run_async(user_id="user", session_id="session1", new_message=content)
    async for ev in events:
        if ev.is_final_response():
            return ev.content.parts[0].text
    return ""

def evaluate_user_code(author_code: str, user_code: str) -> str:
    return asyncio.run(_run_agent_async(author_code, user_code))
