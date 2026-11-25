
from types import SimpleNamespace
from custom_agent import execute_tool


test_cases = [
    SimpleNamespace(
        name="get_service_status",
        args={"service": "orders"}
    ),
    SimpleNamespace(
        name="delete_database",
        args={}
    ),
    SimpleNamespace(
        name="get_service_status",
        args={"service": "unknown"}
    ),
    SimpleNamespace(
        name="get_service_status",
        args={"service": 123}
    ),
    SimpleNamespace(
        name="get_service_status",
        args={}
    )
]

for index, test_case in enumerate(test_cases, start=1):

    print(f"\n=== TEST {index} ===")

    result = execute_tool(test_case)


from unittest.mock import Mock, patch
from google.genai import types
import custom_agent as agent


print("\n=== TEST 6: Execution Budget ===")

function_call = types.FunctionCall(
    name="get_service_status",
    args={"service": "orders"}
)

fake_response = SimpleNamespace(
    candidates=[
        SimpleNamespace(
            finish_reason=types.FinishReason.STOP,
            content=types.Content(
                role="model",
                parts=[
                    types.Part(function_call=function_call)
                ]
            )
        )
    ],
    function_calls=[function_call]
)

fake_client = Mock()

fake_client.models.generate_content.return_value = fake_response

with patch.object(agent, "MAX_MODEL_CALLS", 3):

    completed = agent.run_investigation(
        fake_client,
        "test-model",
        "Investigate orders"
    )

assert completed is False
assert fake_client.models.generate_content.call_count == 3

print("[PASS] Execution budget enforced")


print("\n=== TEST 7: Model Fallback ===")


class FakeAPIError(Exception):

    def __init__(self, code):
        self.code = code


with (
    patch.dict("os.environ", {
        "GOOGLE_API_KEY": "test-key"
    }),
    patch("builtins.input", return_value="Investigate orders"),
    patch.object(agent.genai, "Client"),
    patch.object(agent, "APIError", FakeAPIError),
    patch.object(agent, "MODEL_NAMES", [
        "test-model-1",
        "test-model-2"
    ]),
    patch.object(
        agent,
        "run_investigation",
        side_effect=[FakeAPIError(503), True]
    ) as investigation
):

    agent.main()

    assert investigation.call_count == 2

    assert investigation.call_args_list[0].args[1] == "test-model-1"
    assert investigation.call_args_list[1].args[1] == "test-model-2"

print("[PASS] Model fallback works")
