"""Search notes handler."""

import sys
import os
import base64

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared import db
from shared.responses import paginated_response, error_response
from boto3.dynamodb.conditions import Attr


def handle_search(event: dict, user_id: str) -> dict:
    """
    Handle search notes request.
    
    Args:
        event: Lambda event dictionary
        user_id: User ID from authorizer context
    
    Returns:
        Response dictionary with paginated notes
    """
    try:
        # Get search query from query parameters
        query_params = event.get('queryStringParameters') or {}
        search_query = query_params.get('q', '').strip()
        
        if not search_query:
            return error_response("Search query parameter 'q' is required", 400)
        
        # Get pagination parameters
        limit = int(query_params.get('limit', 20))
        cursor = query_params.get('cursor')
        
        # Decode cursor if provided
        exclusive_start_key = None
        if cursor:
            try:
                decoded = base64.b64decode(cursor.encode()).decode()
                import json
                exclusive_start_key = json.loads(decoded)
            except Exception:
                return error_response("Invalid cursor", 400)
        
        # Create filter expression for title contains (case-insensitive)
        filter_expr = Attr('title').contains(search_query)
        
        # Scan notes with filter
        result = db.scan_notes_by_user(
            user_id=user_id,
            limit=limit,
            exclusive_start_key=exclusive_start_key,
            filter_expression=filter_expr
        )
        
        # Filter results case-insensitively (DynamoDB contains is case-sensitive)
        items = result.get('Items', [])
        filtered_items = [
            item for item in items
            if search_query.lower() in item.get('title', '').lower()
        ]
        
        # Encode next cursor
        next_cursor = None
        if result.get('LastEvaluatedKey'):
            try:
                import json
                cursor_json = json.dumps(result['LastEvaluatedKey'])
                next_cursor = base64.b64encode(cursor_json.encode()).decode()
            except Exception:
                pass
        
        # Return paginated response
        return paginated_response(
            items=filtered_items,
            next_cursor=next_cursor
        )
        
    except ValueError:
        return error_response("Invalid limit parameter", 400)
    except Exception as e:
        print(f"Error searching notes: {e}")
        return error_response("Internal server error", 500)

