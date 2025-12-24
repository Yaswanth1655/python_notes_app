"""Authorizer Lambda function for JWT validation and auto-refresh."""

import sys
import os

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared import auth, db


def generate_policy(principal_id: str, effect: str, resource: str, context: dict = None) -> dict:
    """
    Generate IAM policy for API Gateway.
    
    Args:
        principal_id: Principal ID (user_id)
        effect: Allow or Deny
        resource: Resource ARN
        context: Additional context to pass to Lambda
    
    Returns:
        IAM policy dictionary
    """
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        }
    }
    
    if context:
        policy['context'] = context
    
    return policy


def lambda_handler(event, context):
    """
    Lambda authorizer handler.
    
    Validates JWT token and handles automatic refresh if expired.
    """
    try:
        # Extract token from Authorization header
        token = None
        headers = event.get('headers', {}) or {}
        
        auth_header = headers.get('Authorization') or headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '').strip()
        
        if not token:
            raise Exception('Unauthorized')
        
        # Validate token
        payload = auth.validate_token(token)
        
        # If token is expired, try to refresh using refresh token
        if not payload:
            # Token is expired or invalid, try to get refresh token from headers
            refresh_token = headers.get('X-Refresh-Token') or headers.get('x-refresh-token')
            
            if refresh_token:
                # Decode expired token to get user_id (without verification)
                try:
                    import jwt
                    secret = auth.get_jwt_secret()
                    expired_payload = jwt.decode(token, secret, algorithms=['HS256'], options={"verify_exp": False})
                    user_id = expired_payload.get('user_id')
                    
                    if user_id:
                        # Get user and validate refresh token
                        user = db.get_user_by_id(user_id)
                        if user and auth.is_refresh_token_valid(
                            refresh_token,
                            user.get('refresh_token', ''),
                            user.get('refresh_token_expiry', 0)
                        ):
                            # Generate new access token
                            new_access_token = auth.generate_access_token(user_id)
                            
                            # Return policy with new token in context
                            method_arn = event.get('methodArn', '')
                            context_dict = {
                                'user_id': user_id,
                                'new_access_token': new_access_token
                            }
                            return generate_policy(user_id, 'Allow', method_arn, context_dict)
                except Exception as e:
                    print(f"Error refreshing token: {e}")
            
            # If refresh failed, deny access
            raise Exception('Unauthorized')
        
        # Token is valid, extract user_id
        user_id = payload.get('user_id')
        if not user_id:
            raise Exception('Unauthorized')
        
        # Generate policy
        method_arn = event.get('methodArn', '')
        context_dict = {
            'user_id': user_id
        }
        
        return generate_policy(user_id, 'Allow', method_arn, context_dict)
        
    except Exception as e:
        print(f"Authorization error: {e}")
        # Return deny policy
        method_arn = event.get('methodArn', '*')
        return generate_policy('user', 'Deny', method_arn)

