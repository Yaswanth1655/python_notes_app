#  Serverless Notes Application

A cloud-native backend system for managing notes with time-based classification (past, present, and future). Built using AWS serverless services including Lambda, API Gateway, DynamoDB, and S3.

## Architecture Overview

The application follows a serverless microservices architecture:

```
Client Application
    ↓ HTTPS
API Gateway
    ↓ JWT Validation
Authorizer Lambda (Auto-refresh tokens)
    ↓
┌─────────────────┬──────────────────┬──────────────────┐
│                 │                  │                  │
Auth Service    Notes Service     Upload Service
│                 │                  │                  │
└─────────────────┴──────────────────┴──────────────────┘
    ↓                    ↓                    ↓
Users Table         Notes Table          S3 Bucket
(DynamoDB)         (DynamoDB + GSI)     (Attachments)
```

## Features

- **User Authentication**: Signup and login with JWT tokens
- **Automatic Token Refresh**: Authorizer handles token refresh automatically
- **Notes CRUD**: Create, read, update, and delete notes
- **Time-based Queries**: Get notes for today, past, or future
- **Search**: Search notes by title
- **File Uploads**: Generate presigned URLs for image attachments (2MB limit)
- **Soft Delete**: Notes are soft-deleted (is_deleted flag)
- **Pagination**: Cursor-based pagination for all list endpoints
- **Timezone Support**: User timezone-aware date filtering

## Prerequisites

- Python 3.9+
- AWS CLI configured with appropriate credentials
- AWS SAM CLI installed
- AWS Account with permissions to create:
  - Lambda functions
  - API Gateway
  - DynamoDB tables
  - S3 buckets
  - IAM roles

## Project Structure

```
simple_crud_app/
├── template.yaml                 # AWS SAM template
├── samconfig.toml                # SAM configuration
├── .gitignore
├── README.md
├── .github/
│   └── workflows/
│       └── deploy.yml            # CI/CD pipeline
├── shared/                       # Shared utilities
│   ├── __init__.py
│   ├── db.py                     # DynamoDB helpers
│   ├── auth.py                   # JWT & password utilities
│   ├── responses.py              # Standardized API responses
│   └── validators.py             # Input validation
├── auth_service/                 # Authentication Lambda
│   ├── __init__.py
│   ├── app.py
│   ├── signup.py
│   ├── login.py
│   └── requirements.txt
├── authorizer_service/           # JWT Authorizer Lambda
│   ├── __init__.py
│   ├── app.py
│   └── requirements.txt
├── notes_service/                 # Notes CRUD Lambda
│   ├── __init__.py
│   ├── app.py
│   ├── create.py
│   ├── update.py
│   ├── delete.py
│   ├── get_today.py
│   ├── get_past.py
│   ├── get_future.py
│   ├── search.py
│   └── requirements.txt
└── upload_service/                # Upload URL Lambda
    ├── __init__.py
    ├── app.py
    └── requirements.txt
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd simple_crud_app
```

### 2. Configure AWS Credentials

Ensure your AWS credentials are configured:

```bash
aws configure
```

### 3. Set Up JWT Secret

Create an SSM parameter for the JWT secret:

```bash
aws ssm put-parameter \
  --name /notes-app/jwt-secret \
  --value "your-secret-key-here" \
  --type String \
  --region ap-south-1
```

Or update the `JWTSecret` parameter in `template.yaml` to use a different source.

### 4. Build the Application

```bash
sam build
```

### 5. Deploy to AWS

```bash
sam deploy --guided
```

Follow the prompts, or use the existing `samconfig.toml`:

```bash
sam deploy
```

## Local Development

### Running Locally with SAM CLI

1. **Start Local API**:

```bash
sam local start-api
```

2. **Test Endpoints**:

The API will be available at `http://localhost:3000`

### Testing with curl

```bash
# Signup
curl -X POST http://localhost:3000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Create Note (replace TOKEN with access_token from login)
curl -X POST http://localhost:3000/notes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "title": "My Note",
    "content": "Note content",
    "note_date": 1704067200
  }'
```

## API Documentation

### Authentication Endpoints

#### POST /auth/signup

Register a new user.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response** (200):
```json
{
  "statusCode": 200,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "uuid-string",
    "user_id": "uuid-string"
  }
}
```

#### POST /auth/login

Login with existing credentials.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response** (200):
```json
{
  "statusCode": 200,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "uuid-string",
    "user_id": "uuid-string"
  }
}
```

### Notes Endpoints (All require JWT authentication)

#### POST /notes

Create a new note.

**Request Body**:
```json
{
  "title": "Note Title",
  "content": "Note content (optional)",
  "note_date": 1704067200,
  "attachment_key": "user_id/timestamp/file.jpg (optional)"
}
```

**Response** (200):
```json
{
  "statusCode": 200,
  "data": {
    "note": {
      "user_id": "uuid",
      "note_id": "uuid",
      "title": "Note Title",
      "content": "Note content",
      "note_date": 1704067200,
      "attachment_key": "user_id/timestamp/file.jpg",
      "is_deleted": false,
      "created_at": 1704067200,
      "updated_at": 1704067200
    }
  }
}
```

#### PUT /notes/{note_id}

Update an existing note.

**Request Body**:
```json
{
  "title": "Updated Title",
  "content": "Updated content",
  "attachment_key": "new-key.jpg"
}
```

**Response** (200):
```json
{
  "statusCode": 200,
  "data": {
    "note": { /* updated note object */ }
  }
}
```

#### DELETE /notes/{note_id}

Soft delete a note.

**Response** (200):
```json
{
  "statusCode": 200,
  "data": {
    "message": "Note deleted successfully"
  }
}
```

#### GET /notes/today

Get notes for today (in user's timezone).

**Query Parameters**:
- `cursor` (optional): Pagination cursor
- `limit` (optional, default: 20): Number of items per page

**Response** (200):
```json
{
  "statusCode": 200,
  "data": {
    "notes": [ /* array of note objects */ ],
    "next_cursor": "base64-encoded-cursor-or-null"
  }
}
```

#### GET /notes/past

Get past notes (before today).

**Query Parameters**: Same as `/notes/today`

**Response** (200): Same format as `/notes/today`

#### GET /notes/future

Get future notes (after today).

**Query Parameters**: Same as `/notes/today`

**Response** (200): Same format as `/notes/today`

#### GET /notes/search

Search notes by title.

**Query Parameters**:
- `q` (required): Search query
- `cursor` (optional): Pagination cursor
- `limit` (optional, default: 20): Number of items per page

**Response** (200): Same format as `/notes/today`

### Upload Endpoints

#### POST /notes/upload-url

Generate a presigned URL for uploading an image.

**Request Body**:
```json
{
  "filename": "image.jpg",
  "content_type": "image/jpeg"
}
```

**Response** (200):
```json
{
  "statusCode": 200,
  "data": {
    "upload_url": "https://s3.amazonaws.com/...",
    "object_key": "user_id/timestamp/uuid.jpg",
    "expires_in": 86400
  }
}
```

## Environment Variables

The following environment variables are automatically set by the SAM template:

- `JWT_SECRET`: Secret key for JWT signing (from SSM Parameter)
- `USERS_TABLE`: DynamoDB Users table name
- `NOTES_TABLE`: DynamoDB Notes table name
- `S3_BUCKET`: S3 bucket name for attachments
- `REGION`: AWS region (ap-south-1)

## Database Schema

### Users Table

- **Partition Key**: `user_id` (String, UUID)
- **Attributes**:
  - `email` (String, indexed via GSI)
  - `password_hash` (String)
  - `refresh_token` (String)
  - `refresh_token_expiry` (Number, timestamp)
  - `created_at` (Number, timestamp)
- **GSI**: `email-index` (Partition Key: `email`)

### Notes Table

- **Partition Key**: `user_id` (String, UUID)
- **Sort Key**: `note_id` (String, UUID)
- **Attributes**:
  - `title` (String, required)
  - `content` (String, optional)
  - `note_date` (Number, timestamp)
  - `attachment_key` (String, optional)
  - `is_deleted` (Boolean, default: false)
  - `created_at` (Number, timestamp)
  - `updated_at` (Number, timestamp)
- **GSI**: `date-index` (Partition Key: `user_id`, Sort Key: `note_date`)

## Deployment

### Manual Deployment

```bash
sam build
sam deploy
```

### CI/CD Deployment

The application includes a GitHub Actions workflow that automatically deploys on push to the `main` branch.

**Required GitHub Secrets**:
- `AWS_ACCESS_KEY_ID`: AWS access key ID
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key
- `JWT_SECRET`: JWT secret key for token signing

To set up GitHub Secrets:

1. Go to your repository settings
2. Navigate to Secrets and variables → Actions
3. Add the required secrets

The workflow will:
1. Checkout code
2. Set up Python 3.9
3. Configure AWS credentials
4. Install AWS SAM CLI
5. Build the application
6. Deploy to AWS (ap-south-1)

## Security Considerations

- **JWT Tokens**: Signed with HS256, 48-hour expiration
- **Password Hashing**: bcrypt with 12 salt rounds
- **Refresh Tokens**: Stored in DynamoDB with 48-hour expiry
- **IAM Roles**: Least privilege permissions per Lambda
- **Presigned URLs**: 24-hour expiration, 2MB size limit
- **Input Validation**: All inputs validated before processing
- **CORS**: Configured in API Gateway

## Error Handling

All errors follow a standardized format:

```json
{
  "statusCode": 400,
  "data": {
    "error": "Error message here"
  }
}
```

**HTTP Status Codes**:
- `200`: Success
- `400`: Bad Request (validation errors)
- `401`: Unauthorized (authentication required)
- `404`: Not Found
- `500`: Internal Server Error

## Limitations

- File uploads limited to images only (2MB max)
- Search is case-insensitive but limited to title field
- Pagination uses cursor-based approach (not page numbers)
- Timezone extracted from request headers (defaults to UTC)

## Troubleshooting

### Common Issues

1. **JWT Secret Not Found**:
   - Ensure SSM parameter `/notes-app/jwt-secret` exists
   - Or update `template.yaml` to use a different parameter

2. **DynamoDB Table Not Found**:
   - Check that tables were created during deployment
   - Verify table names in environment variables

3. **S3 Upload Fails**:
   - Verify S3 bucket exists and Lambda has write permissions
   - Check presigned URL expiration (24 hours)

4. **Authorizer Fails**:
   - Ensure JWT token is in Authorization header: `Bearer <token>`
   - Check token expiration (48 hours)
   - Verify refresh token is valid if token expired

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

