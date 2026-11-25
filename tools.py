
from mock_data import SERVICE_STATUS, LOGS, RECENT_CHANGES


def search_logs(service: str, keyword: str) -> dict:
    """Search service logs for a keyword.

    Args:
        service: Service name: gateway, orders, database or payments.
        keyword: Word or phrase to search for.
    """
    if service not in LOGS:
        return {"error": "Unknown service"}

    if not keyword.strip():
        return {"error": "Keyword cannot be empty"}

    matches = []

    for log in LOGS[service]:
        if keyword.lower() in log.lower():
            matches.append(log)

    return {
        "service": service,
        "logs": matches,
        "count": len(matches)
    }


def get_service_status(service: str) -> dict:
    """Get the current status and metrics of a service.

    Args:
        service: Service name: gateway, orders, database or payments.
    """
    if service not in SERVICE_STATUS:
        return {"error": "Unknown service"}

    return {
        "service": service,
        **SERVICE_STATUS[service]
    }


def get_recent_changes(service: str) -> dict:
    """Get recent configuration or deployment changes.

    Args:
        service: Service name: gateway, orders, database or payments.
    """
    if service not in RECENT_CHANGES:
        return {"error": "Unknown service"}

    return {
        "service": service,
        "changes": RECENT_CHANGES[service].copy()
    }
