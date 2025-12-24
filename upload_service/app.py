"""Upload service Lambda handler for generating S3 presigned URLs."""

import json
import os
import sys
import uuid
from datetime import datetime

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import boto3
from shared import validators
from shared.responses import success_response, error_response


def lambda_handler(event, context):
    """
    Lambda handler for upload service.
    
    Generates presigned URLs for S3 uploads.
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
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        filename = body.get('filename', '')
        content_type = body.get('content_type', '')
        
        # Validate filename
        is_valid_filename, error_msg_filename = validators.validate_filename(filename)
        if not is_valid_filename:
            return error_response(error_msg_filename, 400)
        
        # Validate file type (images only)
        is_valid_type, error_msg_type = validators.validate_file_type(content_type)
        if not is_valid_type:
            return error_response(error_msg_type, 400)
        
        # Get S3 bucket name from environment
        bucket_name = os.environ.get('S3_BUCKET')
        if not bucket_name:
            return error_response("S3 bucket not configured", 500)
        
        # Generate unique object key
        timestamp = int(datetime.utcnow().timestamp())
        unique_id = str(uuid.uuid4())[:8]
        file_extension = os.path.splitext(filename)[1]
        object_key = f"{user_id}/{timestamp}/{unique_id}{file_extension}"
        
        # Generate presigned URL (long expiration for testing - 24 hours)
        s3_client = boto3.client('s3', region_name=os.environ.get('REGION', 'ap-south-1'))
        
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_key,
                'ContentType': content_type
            },
            ExpiresIn=86400,  # 24 hours
            HttpMethod='PUT'
        )
        
        # Return success response
        return success_response({
            'upload_url': presigned_url,
            'object_key': object_key,
            'expires_in': 86400
        })
        
    except json.JSONDecodeError:
        return error_response("Invalid JSON in request body", 400)
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return error_response("Internal server error", 500)

