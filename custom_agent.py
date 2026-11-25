
from urllib import response

import truststore

truststore.inject_into_ssl()

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
from tools import (
    search_logs,
    get_service_status,
    get_recent_changes
)
from prompts import SYSTEM_PROMPT

load_dotenv()

MODEL_NAMES = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite"
]


TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="search_logs",
        description="Search service logs for a keyword.",
        parameters={
            "type": "OBJECT",
            "properties": {
                "service": {
                    "type": "STRING",
                    "enum": [
                        "gateway",
                        "orders",
                        "database",
                        "payments"
                    ]
                },
                "keyword": {
                    "type": "STRING",
                    "description": "Word or phrase to search for."
                }
            },
            "required": ["service", "keyword"]
        }
    ),

    types.FunctionDeclaration(
        name="get_service_status",
        description="Get the current status and metrics of a service.",
        parameters={
            "type": "OBJECT",
            "properties": {
                "service": {
                    "type": "STRING",
                    "enum": [
                        "gateway",
                        "orders",
                        "database",
                        "payments"
                    ]
                }
            },
            "required": ["service"]
        }
    ),

    types.FunctionDeclaration(
        name="get_recent_changes",
        description="Get recent configuration or deployment changes.",
        parameters={
            "type": "OBJECT",
            "properties": {
                "service": {
                    "type": "STRING",
                    "enum": [
                        "gateway",
                        "orders",
                        "database",
                        "payments"
                    ]
                }
            },
            "required": ["service"]
        }
    )
]

TOOL_REGISTRY = {
    "search_logs": search_logs,
    "get_service_status": get_service_status,
    "get_recent_changes": get_recent_changes
}
MAX_MODEL_CALLS = 10


def execute_tool(function_call):

    name = function_call.name
    args = function_call.args or {}

    print(f"\n[TOOL CALL] {name}")
    print(f"[ARGUMENTS] {args}")

    if name not in TOOL_REGISTRY:
        result = {"error": "Unknown tool"}

    elif not all(
        isinstance(value, str)
        for value in args.values()
    ):
        result = {"error": "Invalid argument types"}

    else:
        try:
            tool = TOOL_REGISTRY[name]
            result = tool(**args)

        except TypeError:
            result = {"error": "Invalid tool arguments"}

        except Exception:
            result = {"error": "Tool execution failed"}

    print(f"[TOOL RESULT] {result}")

    return result


AGENT_TOOLS = types.Tool(
    function_declarations=TOOL_DECLARATIONS
)


def run_investigation(client, model_name, question):

    history = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=question)
            ]
        )
    ]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[AGENT_TOOLS],
        automatic_function_calling=(
            types.AutomaticFunctionCallingConfig(
                disable=True
            )
        )
    )

    for iteration in range(1, MAX_MODEL_CALLS + 1):

        print(f"\n[MODEL CALL #{iteration}]")
        print(f"[HISTORY SIZE] {len(history)}")

        response = client.models.generate_content(
            model=model_name,
            contents=history,
            config=config
        )

        if not response.candidates:
            print("[STOP] No candidates received")
            return False

        candidate = response.candidates[0]

        print(f"[FINISH REASON] {candidate.finish_reason}")

        if candidate.finish_reason != types.FinishReason.STOP:
            print("[STOP] Model response did not complete normally")
            return False

        if not candidate.content:
            print("[STOP] No content received")
            return False

        history.append(candidate.content)

        function_calls = response.function_calls or []

        if not function_calls:
            if not response.text:
                print("[STOP] Empty final response")
                return False

            print("\n=== FINAL REPORT ===\n")
            print(response.text)

            print("[STOP] Investigation completed")
            return True

        if iteration == MAX_MODEL_CALLS:
            break

        tool_responses = []

        for function_call in function_calls:

            result = execute_tool(function_call)

            response_part = types.Part(
                function_response=types.FunctionResponse(
                    id=function_call.id,
                    name=function_call.name,
                    response=result
                )
            )

            tool_responses.append(response_part)

        history.append(
            types.Content(
                role="user",
                parts=tool_responses
            )
        )

    print("[STOP] Maximum model calls reached")
    return False



def main():

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("ERROR: Missing Google API key")
        return

    question = input("Describe the incident: ").strip()

    if not question:
        print("ERROR: Empty incident description")
        return

    with genai.Client(api_key=api_key) as client:

        for model_name in MODEL_NAMES:

            print(f"\n[TRY MODEL] {model_name}")

            try:
                completed = run_investigation(
                    client,
                    model_name,
                    question
                )

                if completed:
                    print(f"\n[SUCCESS] {model_name}")
                else:
                    print("[INCOMPLETE INVESTIGATION]")

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

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("ERROR: Missing Google API key")
        return

    with genai.Client(api_key=api_key) as client:

        for model_name in MODEL_NAMES:

            print(f"\n[TRY MODEL] {model_name}")

            try:


                history = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(
                                text="Check the current status of the orders service."
                            )
                        ]
                    )
                ]

                config = types.GenerateContentConfig(
                    tools=[AGENT_TOOLS],
                    automatic_function_calling=(
                        types.AutomaticFunctionCallingConfig(
                            disable=True
                        )
                    )
                )

                print("\n[MODEL CALL #1]")

                response = client.models.generate_content(
                    model=model_name,
                    contents=history,
                    config=config
                )

                if not response.function_calls:
                    print("[STOP] No tool calls received")
                    return

                history.append(response.candidates[0].content)

                tool_responses = []

                for function_call in response.function_calls:
                    result = execute_tool(function_call)

                    response_part = types.Part(
                        function_response=types.FunctionResponse(
                            id=function_call.id,
                            name=function_call.name,
                            response=result
                        )
                    )

                    tool_responses.append(response_part)

                history.append(
                    types.Content(
                        role="user",
                        parts=tool_responses
                    )
                )

                print(f"\n[HISTORY SIZE] {len(history)}")
                print("\n[MODEL CALL #2]")

                response = client.models.generate_content(
                    model=model_name,
                    contents=history,
                    config=config
                )

                if response.function_calls:
                    print("[STOP] Additional tool calls requested")
                    return

                print("\n[FINAL RESPONSE]")
                print(response.text)

                print(f"\n[SUCCESS] {model_name}")
                return


                for function_call in response.function_calls or []:
                    result = execute_tool(function_call)
                print(f"\n[SUCCESS] {model_name}")
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
    main()
