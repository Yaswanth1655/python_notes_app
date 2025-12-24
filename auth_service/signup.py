"""User signup handler."""

import json
import sys
import os

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared import validators, auth, db
from shared.responses import success_response, error_response


def handle_signup(event: dict) -> dict:
    """
    Handle user signup request.
    
    Args:
        event: Lambda event dictionary
    
    Returns:
        Response dictionary
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').strip().lower()
        password = body.get('password', '')
        
        # Validate email
        if not validators.validate_email(email):
            return error_response("Invalid email format", 400)
        
        # Validate password
        is_valid, error_msg = validators.validate_password(password)
        if not is_valid:
            return error_response(error_msg, 400)
        
        # Check if email already exists
        existing_user = db.get_user_by_email(email)
        if existing_user:
            return error_response("Email already registered", 400)
        
        # Hash password
        password_hash = auth.hash_password(password)
        
        # Generate refresh token and expiry
        refresh_token = auth.generate_refresh_token()
        refresh_token_expiry = auth.get_refresh_token_expiry()
        
        # Create user
        user = db.create_user(email, password_hash, refresh_token, refresh_token_expiry)
        
        # Generate access token
        access_token = auth.generate_access_token(user['user_id'])
        
        # Return success response
        return success_response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': user['user_id']
        })
        
    except json.JSONDecodeError:
        return error_response("Invalid JSON in request body", 400)
    except Exception as e:
        print(f"Error in signup: {e}")
        return error_response("Internal server error", 500)

