
SERVICE_STATUS = {
    "gateway": {
        "status": "healthy",
        "response_time_ms": 45
    },
    "orders": {
        "status": "degraded",
        "error_rate_percent": 65,
        "response_time_ms": 5000
    },
    "database": {
        "status": "degraded",
        "active_connections": 100,
        "max_connections": 100
    },
    "payments": {
        "status": "healthy",
        "response_time_ms": 120
    }
}


LOGS = {
    "gateway": [
        "INFO: Gateway started successfully",
        "INFO: Incoming request to orders"
    ],
    "orders": [
        "INFO: Processing new order",
        "ERROR: Database connection timeout",
        "ERROR: Failed to create order"
    ],
    "database": [
        "WARNING: Connection pool nearly full",
        "ERROR: Maximum connections reached",
        "ERROR: New connection rejected"
    ],
    "payments": [
        "INFO: Payment processed successfully",
        "INFO: Payment service operational"
    ]
}


RECENT_CHANGES = {
    "gateway": [],
    "orders": [
        "Connection pool size increased from 10 to 100"
    ],
    "database": [],
    "payments": [
        "Updated payment confirmation message"
    ]
}
