"""Update note handler."""

import json
import sys
import os

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared import validators, db
from shared.responses import success_response, error_response


def handle_update(event: dict, user_id: str) -> dict:
    """
    Handle update note request.
    
    Args:
        event: Lambda event dictionary
        user_id: User ID from authorizer context
    
    Returns:
        Response dictionary
    """
    try:
        # Extract note_id from path parameters
        note_id = event.get('pathParameters', {}).get('note_id')
        if not note_id:
            return error_response("note_id is required in path", 400)
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Get existing note to verify ownership and check if deleted
        existing_note = db.get_note(user_id, note_id)
        if not existing_note:
            return error_response("Note not found", 404)
        
        if existing_note.get('is_deleted', False):
            return error_response("Note is deleted", 404)
        
        # Prepare update fields
        update_data = {}
        if 'title' in body:
            update_data['title'] = body['title'].strip()
        if 'content' in body:
            update_data['content'] = body.get('content', '').strip() or ''
        if 'attachment_key' in body:
            update_data['attachment_key'] = body.get('attachment_key')
        
        # Validate title if provided
        if 'title' in update_data and not update_data['title']:
            return error_response("Title cannot be empty", 400)
        
        # Update note (note_date is preserved, not updated)
        updated_note = db.update_note(
            user_id=user_id,
            note_id=note_id,
            title=update_data.get('title'),
            content=update_data.get('content'),
            attachment_key=update_data.get('attachment_key')
        )
        
        if not updated_note:
            return error_response("Failed to update note", 500)
        
        # Return success response
        return success_response({'note': updated_note})
        
    except json.JSONDecodeError:
        return error_response("Invalid JSON in request body", 400)
    except Exception as e:
        print(f"Error updating note: {e}")
        return error_response("Internal server error", 500)

