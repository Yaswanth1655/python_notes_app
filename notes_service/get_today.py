"""Get today's notes handler."""

import sys
import os
import base64

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared import db, auth
from shared.responses import paginated_response, error_response


def handle_get_today(event: dict, user_id: str) -> dict:
    """
    Handle get today's notes request.
    
    Args:
        event: Lambda event dictionary
        user_id: User ID from authorizer context
    
    Returns:
        Response dictionary with paginated notes
    """
    try:
        # Get user timezone
        timezone = auth.extract_user_timezone(event)
        
        # Get start and end of today in user timezone
        start_of_day = auth.get_start_of_day_timestamp(timezone)
        end_of_day = auth.get_end_of_day_timestamp(timezone)
        
        # Get pagination parameters
        query_params = event.get('queryStringParameters') or {}
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
        
        # Query notes for today
        result = db.query_notes_by_date_range(
            user_id=user_id,
            start_date=start_of_day,
            end_date=end_of_day,
            limit=limit,
            exclusive_start_key=exclusive_start_key,
            scan_forward=True
        )
        
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
            items=result.get('Items', []),
            next_cursor=next_cursor
        )
        
    except ValueError:
        return error_response("Invalid limit parameter", 400)
    except Exception as e:
        print(f"Error getting today's notes: {e}")
        return error_response("Internal server error", 500)

