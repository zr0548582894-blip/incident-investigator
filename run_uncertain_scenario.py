
import sys
import asyncio

from mock_data import (
    SERVICE_STATUS,
    LOGS,
    RECENT_CHANGES
)

SERVICE_STATUS.update({
    "gateway": {
        "status": "healthy",
        "response_time_ms": 45
    },
    "orders": {
        "status": "degraded",
        "error_rate_percent": 40,
        "response_time_ms": 2000
    },
    "database": {
        "status": "healthy",
        "active_connections": 20,
        "max_connections": 100
    },
    "payments": {
        "status": "healthy",
        "response_time_ms": 120
    }
})

LOGS.update({
    "gateway": [
        "INFO: Gateway operational"
    ],
    "orders": [
        "ERROR: Request failed",
        "ERROR: Unexpected error"
    ],
    "database": [
        "INFO: Database operational"
    ],
    "payments": [
        "INFO: Payment service operational"
    ]
})

RECENT_CHANGES.update({
    "gateway": [],
    "orders": [],
    "database": [],
    "payments": []
})


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python run_uncertain_scenario.py sdk|custom")

    elif sys.argv[1] == "sdk":
        import sdk_agent

        sdk_agent.MODEL_NAMES = ["gemini-3.5-flash-lite"]

        asyncio.run(sdk_agent.main())

    elif sys.argv[1] == "custom":
        import custom_agent

        custom_agent.MODEL_NAMES = ["gemini-3.5-flash-lite"]

        custom_agent.main()

    else:
        print("Unknown implementation")
