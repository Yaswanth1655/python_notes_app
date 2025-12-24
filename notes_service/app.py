"""Notes service Lambda handler."""

import sys
import os

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from create import handle_create
from update import handle_update
from delete import handle_delete
from get_today import handle_get_today
from get_past import handle_get_past
from get_future import handle_get_future
from search import handle_search


def lambda_handler(event, context):
    """
    Lambda handler for notes service.
    
    Routes requests based on HTTP method and path.
    """
    try:
        # Extract user_id from authorizer context
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {}) or {}
        context_dict = authorizer.get('context', {}) or {}
        user_id = context_dict.get('user_id')
        
        if not user_id:
            return {
                'statusCode': 401,
                'data': {'error': 'Unauthorized'}
            }
        
        # Get path and method
        path = event.get('path', '')
        http_method = event.get('httpMethod', '')
        
        # Route to appropriate handler
        if path == '/notes' and http_method == 'POST':
            return handle_create(event, user_id)
        elif path.startswith('/notes/') and http_method == 'PUT':
            return handle_update(event, user_id)
        elif path.startswith('/notes/') and http_method == 'DELETE':
            return handle_delete(event, user_id)
        elif path == '/notes/today' and http_method == 'GET':
            return handle_get_today(event, user_id)
        elif path == '/notes/past' and http_method == 'GET':
            return handle_get_past(event, user_id)
        elif path == '/notes/future' and http_method == 'GET':
            return handle_get_future(event, user_id)
        elif path == '/notes/search' and http_method == 'GET':
            return handle_search(event, user_id)
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

