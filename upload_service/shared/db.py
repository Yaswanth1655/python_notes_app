"""DynamoDB database utilities."""

import os
import uuid
import boto3
from typing import Dict, Any, Optional, List
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'ap-south-1'))

# Table names from environment
USERS_TABLE_NAME = os.environ.get('USERS_TABLE')
NOTES_TABLE_NAME = os.environ.get('NOTES_TABLE')

# Get table references
users_table = dynamodb.Table(USERS_TABLE_NAME) if USERS_TABLE_NAME else None
notes_table = dynamodb.Table(NOTES_TABLE_NAME) if NOTES_TABLE_NAME else None


# ==================== Users Table Operations ====================

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get user by email using GSI.
    
    Args:
        email: User email address
    
    Returns:
        User dictionary if found, None otherwise
    """
    try:
        response = users_table.query(
            IndexName='email-index',
            KeyConditionExpression=Key('email').eq(email)
        )
        items = response.get('Items', [])
        return items[0] if items else None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user by user_id.
    
    Args:
        user_id: User ID
    
    Returns:
        User dictionary if found, None otherwise
    """
    try:
        response = users_table.get_item(Key={'user_id': user_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None


def create_user(email: str, password_hash: str, refresh_token: str, refresh_token_expiry: int) -> Dict[str, Any]:
    """
    Create a new user.
    
    Args:
        email: User email
        password_hash: Hashed password
        refresh_token: Refresh token
        refresh_token_expiry: Refresh token expiry timestamp
    
    Returns:
        Created user dictionary
    """
    import time
    user_id = str(uuid.uuid4())
    created_at = int(time.time())
    
    user = {
        'user_id': user_id,
        'email': email,
        'password_hash': password_hash,
        'refresh_token': refresh_token,
        'refresh_token_expiry': refresh_token_expiry,
        'created_at': created_at
    }
    
    try:
        users_table.put_item(Item=user)
        return user
    except Exception as e:
        print(f"Error creating user: {e}")
        raise


def update_refresh_token(user_id: str, refresh_token: str, refresh_token_expiry: int) -> bool:
    """
    Update refresh token for a user.
    
    Args:
        user_id: User ID
        refresh_token: New refresh token
        refresh_token_expiry: New refresh token expiry timestamp
    
    Returns:
        True if successful, False otherwise
    """
    try:
        users_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET refresh_token = :token, refresh_token_expiry = :expiry',
            ExpressionAttributeValues={
                ':token': refresh_token,
                ':expiry': refresh_token_expiry
            }
        )
        return True
    except Exception as e:
        print(f"Error updating refresh token: {e}")
        return False


# ==================== Notes Table Operations ====================

def create_note(user_id: str, title: str, content: Optional[str], note_date: int, 
                attachment_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new note.
    
    Args:
        user_id: User ID
        title: Note title
        content: Note content (optional)
        note_date: Note date timestamp
        attachment_key: S3 attachment key (optional)
    
    Returns:
        Created note dictionary
    """
    import time
    note_id = str(uuid.uuid4())
    created_at = int(time.time())
    
    note = {
        'user_id': user_id,
        'note_id': note_id,
        'title': title,
        'content': content or '',
        'note_date': note_date,
        'is_deleted': False,
        'created_at': created_at,
        'updated_at': created_at
    }
    
    if attachment_key:
        note['attachment_key'] = attachment_key
    
    try:
        notes_table.put_item(Item=note)
        return note
    except Exception as e:
        print(f"Error creating note: {e}")
        raise


def get_note(user_id: str, note_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a note by user_id and note_id.
    
    Args:
        user_id: User ID
        note_id: Note ID
    
    Returns:
        Note dictionary if found, None otherwise
    """
    try:
        response = notes_table.get_item(
            Key={
                'user_id': user_id,
                'note_id': note_id
            }
        )
        return response.get('Item')
    except Exception as e:
        print(f"Error getting note: {e}")
        return None


def update_note(user_id: str, note_id: str, title: Optional[str] = None, 
                content: Optional[str] = None, attachment_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Update a note.
    
    Args:
        user_id: User ID
        note_id: Note ID
        title: New title (optional)
        content: New content (optional)
        attachment_key: New attachment key (optional)
    
    Returns:
        Updated note dictionary if successful, None otherwise
    """
    import time
    updated_at = int(time.time())
    
    update_expression_parts = []
    expression_attribute_values = {}
    
    if title is not None:
        update_expression_parts.append('title = :title')
        expression_attribute_values[':title'] = title
    
    if content is not None:
        update_expression_parts.append('content = :content')
        expression_attribute_values[':content'] = content
    
    if attachment_key is not None:
        update_expression_parts.append('attachment_key = :attachment_key')
        expression_attribute_values[':attachment_key'] = attachment_key
    
    update_expression_parts.append('updated_at = :updated_at')
    expression_attribute_values[':updated_at'] = updated_at
    
    update_expression = 'SET ' + ', '.join(update_expression_parts)
    
    try:
        response = notes_table.update_item(
            Key={
                'user_id': user_id,
                'note_id': note_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ConditionExpression=Attr('is_deleted').eq(False),
            ReturnValues='ALL_NEW'
        )
        return response.get('Attributes')
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(f"Note {note_id} is deleted or does not exist")
        else:
            print(f"Error updating note: {e}")
        return None
    except Exception as e:
        print(f"Error updating note: {e}")
        return None


def delete_note(user_id: str, note_id: str) -> bool:
    """
    Soft delete a note (set is_deleted = True).
    
    Args:
        user_id: User ID
        note_id: Note ID
    
    Returns:
        True if successful, False otherwise
    """
    import time
    updated_at = int(time.time())
    
    try:
        notes_table.update_item(
            Key={
                'user_id': user_id,
                'note_id': note_id
            },
            UpdateExpression='SET is_deleted = :deleted, updated_at = :updated_at',
            ExpressionAttributeValues={
                ':deleted': True,
                ':updated_at': updated_at
            },
            ConditionExpression=Attr('is_deleted').eq(False)
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(f"Note {note_id} is already deleted or does not exist")
        else:
            print(f"Error deleting note: {e}")
        return False
    except Exception as e:
        print(f"Error deleting note: {e}")
        return False


def query_notes_by_date_range(user_id: str, start_date: int, end_date: int, 
                               limit: int = 20, exclusive_start_key: Optional[Dict] = None,
                               scan_forward: bool = True) -> Dict[str, Any]:
    """
    Query notes by date range using GSI.
    
    Args:
        user_id: User ID
        start_date: Start date timestamp
        end_date: End date timestamp
        limit: Maximum number of items to return
        exclusive_start_key: Exclusive start key for pagination
        scan_forward: Whether to scan forward (True) or backward (False)
    
    Returns:
        Dictionary with 'Items' and 'LastEvaluatedKey'
    """
    try:
        query_params = {
            'IndexName': 'date-index',
            'KeyConditionExpression': Key('user_id').eq(user_id) & Key('note_date').between(start_date, end_date),
            'FilterExpression': Attr('is_deleted').eq(False),
            'Limit': limit,
            'ScanIndexForward': scan_forward
        }
        
        if exclusive_start_key:
            query_params['ExclusiveStartKey'] = exclusive_start_key
        
        response = notes_table.query(**query_params)
        
        return {
            'Items': response.get('Items', []),
            'LastEvaluatedKey': response.get('LastEvaluatedKey')
        }
    except Exception as e:
        print(f"Error querying notes by date range: {e}")
        return {'Items': [], 'LastEvaluatedKey': None}


def query_notes_before_date(user_id: str, before_date: int, limit: int = 20,
                            exclusive_start_key: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Query notes before a specific date using GSI.
    
    Args:
        user_id: User ID
        before_date: Date timestamp (exclusive)
        limit: Maximum number of items to return
        exclusive_start_key: Exclusive start key for pagination
    
    Returns:
        Dictionary with 'Items' and 'LastEvaluatedKey'
    """
    try:
        query_params = {
            'IndexName': 'date-index',
            'KeyConditionExpression': Key('user_id').eq(user_id) & Key('note_date').lt(before_date),
            'FilterExpression': Attr('is_deleted').eq(False),
            'Limit': limit,
            'ScanIndexForward': False  # Descending order (newest first)
        }
        
        if exclusive_start_key:
            query_params['ExclusiveStartKey'] = exclusive_start_key
        
        response = notes_table.query(**query_params)
        
        return {
            'Items': response.get('Items', []),
            'LastEvaluatedKey': response.get('LastEvaluatedKey')
        }
    except Exception as e:
        print(f"Error querying notes before date: {e}")
        return {'Items': [], 'LastEvaluatedKey': None}


def query_notes_after_date(user_id: str, after_date: int, limit: int = 20,
                           exclusive_start_key: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Query notes after a specific date using GSI.
    
    Args:
        user_id: User ID
        after_date: Date timestamp (exclusive)
        limit: Maximum number of items to return
        exclusive_start_key: Exclusive start key for pagination
    
    Returns:
        Dictionary with 'Items' and 'LastEvaluatedKey'
    """
    try:
        query_params = {
            'IndexName': 'date-index',
            'KeyConditionExpression': Key('user_id').eq(user_id) & Key('note_date').gt(after_date),
            'FilterExpression': Attr('is_deleted').eq(False),
            'Limit': limit,
            'ScanIndexForward': True  # Ascending order (oldest first)
        }
        
        if exclusive_start_key:
            query_params['ExclusiveStartKey'] = exclusive_start_key
        
        response = notes_table.query(**query_params)
        
        return {
            'Items': response.get('Items', []),
            'LastEvaluatedKey': response.get('LastEvaluatedKey')
        }
    except Exception as e:
        print(f"Error querying notes after date: {e}")
        return {'Items': [], 'LastEvaluatedKey': None}


def scan_notes_by_user(user_id: str, limit: int = 20, 
                       exclusive_start_key: Optional[Dict] = None,
                       filter_expression: Optional[Any] = None) -> Dict[str, Any]:
    """
    Scan notes for a user (for search functionality).
    
    Args:
        user_id: User ID
        limit: Maximum number of items to return
        exclusive_start_key: Exclusive start key for pagination
        filter_expression: Additional filter expression
    
    Returns:
        Dictionary with 'Items' and 'LastEvaluatedKey'
    """
    try:
        scan_params = {
            'FilterExpression': Attr('user_id').eq(user_id) & Attr('is_deleted').eq(False),
            'Limit': limit
        }
        
        if filter_expression:
            scan_params['FilterExpression'] = scan_params['FilterExpression'] & filter_expression
        
        if exclusive_start_key:
            scan_params['ExclusiveStartKey'] = exclusive_start_key
        
        response = notes_table.scan(**scan_params)
        
        return {
            'Items': response.get('Items', []),
            'LastEvaluatedKey': response.get('LastEvaluatedKey')
        }
    except Exception as e:
        print(f"Error scanning notes: {e}")
        return {'Items': [], 'LastEvaluatedKey': None}

