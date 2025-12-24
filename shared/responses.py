"""Standardized API response formatters."""

from typing import Any, Dict, List, Optional


def success_response(data: Any, status_code: int = 200) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data to include
        status_code: HTTP status code (default: 200)
    
    Returns:
        Formatted response dictionary
    """
    return {
        "statusCode": status_code,
        "data": data
    }


def error_response(error_message: str, status_code: int = 400) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error_message: Error message to include
        status_code: HTTP status code (default: 400)
    
    Returns:
        Formatted error response dictionary
    """
    return {
        "statusCode": status_code,
        "data": {
            "error": error_message
        }
    }


def paginated_response(
    items: List[Any],
    next_cursor: Optional[str] = None,
    status_code: int = 200
) -> Dict[str, Any]:
    """
    Create a standardized paginated response.
    
    Args:
        items: List of items to return
        next_cursor: Cursor for next page (None if last page)
        status_code: HTTP status code (default: 200)
    
    Returns:
        Formatted paginated response dictionary
    """
    return {
        "statusCode": status_code,
        "data": {
            "notes": items,
            "next_cursor": next_cursor
        }
    }

