"""Delete note handler."""

import sys
import os

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared import db
from shared.responses import success_response, error_response


def handle_delete(event: dict, user_id: str) -> dict:
    """
    Handle delete note request (soft delete).
    
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
        
        # Verify note exists and belongs to user
        existing_note = db.get_note(user_id, note_id)
        if not existing_note:
            return error_response("Note not found", 404)
        
        if existing_note.get('is_deleted', False):
            return error_response("Note is already deleted", 404)
        
        # Soft delete note
        success = db.delete_note(user_id, note_id)
        
        if not success:
            return error_response("Failed to delete note", 500)
        
        # Return success response
        return success_response({'message': 'Note deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting note: {e}")
        return error_response("Internal server error", 500)

