"""Auth service Lambda handler."""

import sys
import os

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from signup import handle_signup
from login import handle_login


def lambda_handler(event, context):
    """
    Lambda handler for authentication service.
    
    Routes requests to signup or login handlers based on path.
    """
    try:
        # Get path from event
        path = event.get('path', '')
        http_method = event.get('httpMethod', '')
        
        # Route to appropriate handler
        if path == '/auth/signup' and http_method == 'POST':
            return handle_signup(event)
        elif path == '/auth/login' and http_method == 'POST':
            return handle_login(event)
        else:
            return {
                'statusCode': 404,
                'data': {'error': 'Not found'}
            }
            
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'data': {'error': 'Internal server error'}
        }

