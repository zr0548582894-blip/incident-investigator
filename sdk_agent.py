import truststore
truststore.inject_into_ssl()

import os
import asyncio

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.genai.errors import APIError

from prompts import SYSTEM_PROMPT
from tools import (
    search_logs,
    get_service_status,
    get_recent_changes
)

load_dotenv()

APP_NAME = "incident_investigator"
USER_ID = "local_user"
SESSION_ID = "investigation_1"
MAX_MODEL_CALLS = 10
MODEL_NAMES = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite"
]


# Callbacks

def before_model(callback_context, llm_request):
    count = callback_context.state.get("model_calls", 0) + 1
    callback_context.state["model_calls"] = count#תיעוד כמה פעמים הגענו לשלב הפנייה למודל

    print(f"\n[MODEL CALL #{count}]")
    return None


def before_tool(tool, args, tool_context):
    print(f"\n[TOOL CALL] {tool.name}")#אילו כלים הסוכן בחר.
    print(f"[ARGUMENTS] {args}")
    return None


def after_tool(tool, args, tool_context, tool_response):
    print(f"[TOOL RESULT] {tool_response}")#אילו תוצאות הכלים החזירו.
    return None


# Agent definition

def create_agent(model_name):
    return Agent(
        name="incident_investigator",
        model=model_name,
        description="Investigates service failures using evidence.",
        instruction=SYSTEM_PROMPT,
        tools=[
            search_logs,
            get_service_status,
            get_recent_changes
        ],
        before_model_callback=before_model,
        before_tool_callback=before_tool,
        after_tool_callback=after_tool
    )

# Execution

async def main():
    if not os.getenv("GOOGLE_API_KEY"):
        print("ERROR: Missing Google API key")
        return

    question = input("Describe the incident: ").strip()

    if not question:
        print("ERROR: Empty incident description")
        return

    message = types.Content(
        role="user",
        parts=[types.Part(text=question)]
    )

    for model_name in MODEL_NAMES:

        print(f"\n[TRY MODEL] {model_name}")

        try:
            agent = create_agent(model_name)

            session_service = InMemorySessionService()

            await session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=SESSION_ID
            )

            runner = Runner(
                agent=agent,
                app_name=APP_NAME,
                session_service=session_service
            )

            run_config = RunConfig(
                max_llm_calls=MAX_MODEL_CALLS
            )

            completed = False

            async for event in runner.run_async(
                user_id=USER_ID,
                session_id=SESSION_ID,
                new_message=message,
                run_config=run_config
            ):
                if event.is_final_response() and event.content:
                    for part in event.content.parts or []:
                        if part.text and not part.thought:
                            print("\n=== FINAL REPORT ===\n")
                            print(part.text)
                            completed = True

            if completed:
                print(f"\n[SUCCESS] {model_name}")
                print("[STOP] Investigation completed")
                return

            print("[STOP] No final report")
            return

        except APIError as error:
            print(f"[MODEL FAILED] {model_name}")
            print(f"[ERROR CODE] {error.code}")

            if error.code in (429, 503):
                print("[FALLBACK] Trying next model")
                continue

            print(f"[STOP] {error}")
            return

        except Exception as error:
            print(f"[STOP] {type(error).__name__}: {error}")
            return

    print("\n[STOP] All models failed")



if __name__ == "__main__":
    asyncio.run(main())
