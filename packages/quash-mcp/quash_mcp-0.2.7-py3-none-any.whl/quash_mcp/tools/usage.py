"""
Usage tool - View usage statistics and costs from backend.
Queries the backend API for usage statistics instead of local tracking.
"""

from typing import Dict, Any, Optional


async def usage(api_key: Optional[str] = None, show_recent: int = 5) -> Dict[str, Any]:
    """
    View usage statistics for Quash executions from backend.

    Note: In v0.2.0, all usage tracking happens on the backend.
    This tool would need backend API support to fetch usage stats.

    Args:
        api_key: Specific API key to query (optional - shows all if not provided)
        show_recent: Number of recent executions to show (default: 5)

    Returns:
        Dict with usage statistics and execution history
    """

    # TODO: Implement backend API call to fetch usage stats
    # For now, return a message directing users to the web portal

    return {
        "status": "info",
        "message": "📊 Usage statistics are tracked on the backend. Please visit https://quashbugs.com/dashboard to view your usage, costs, and execution history.",
        "note": "All usage tracking, token counts, and costs are now managed server-side for security."
    }