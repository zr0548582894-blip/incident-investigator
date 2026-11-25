
import sys
import asyncio

from mock_data import (
    SERVICE_STATUS,
    LOGS,
    RECENT_CHANGES
)


SERVICE_STATUS.update({
    "orders": {
        "status": "healthy",
        "error_rate_percent": 0,
        "response_time_ms": 100
    },
    "database": {
        "status": "healthy",
        "active_connections": 15,
        "max_connections": 100
    },
    "payments": {
        "status": "degraded",
        "error_rate_percent": 85,
        "response_time_ms": 3000
    }
})

LOGS.update({
    "orders": [
        "INFO: Order created successfully"
    ],
    "database": [
        "INFO: Database operational"
    ],
    "payments": [
        "ERROR: Payment provider authentication failed",
        "ERROR: Payment request rejected"
    ]
})

RECENT_CHANGES.update({
    "orders": [],
    "database": [],
    "payments": [
        "Payment provider credentials updated"
    ]
})


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python run_scenario.py sdk|custom")

    elif sys.argv[1] == "sdk":
        from sdk_agent import main

        asyncio.run(main())

    elif sys.argv[1] == "custom":
        from custom_agent import main

        main()

    else:
        print("Unknown implementation")
