"""Create note handler."""

import json
import sys
import os

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared import validators, db, auth
from shared.responses import success_response, error_response


def handle_create(event: dict, user_id: str) -> dict:
    """
    Handle create note request.
    
    Args:
        event: Lambda event dictionary
        user_id: User ID from authorizer context
    
    Returns:
        Response dictionary
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate note data
        is_valid, error_msg = validators.validate_note_data(body)
        if not is_valid:
            return error_response(error_msg, 400)
        
        # Extract fields
        title = body.get('title', '').strip()
        content = body.get('content', '').strip() or ''
        note_date = body.get('note_date')
        attachment_key = body.get('attachment_key')
        
        # Validate timestamp
        is_valid_ts, error_msg_ts = validators.validate_timestamp(note_date)
        if not is_valid_ts:
            return error_response(error_msg_ts, 400)
        
        # Create note
        note = db.create_note(
            user_id=user_id,
            title=title,
            content=content,
            note_date=int(note_date),
            attachment_key=attachment_key
        )
        
        # Return success response
        return success_response({'note': note})
        
    except json.JSONDecodeError:
        return error_response("Invalid JSON in request body", 400)
    except Exception as e:
        print(f"Error creating note: {e}")
        return error_response("Internal server error", 500)

