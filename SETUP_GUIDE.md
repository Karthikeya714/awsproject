# 🔐 Secure AI Caption Backend Setup Guide

## Overview
This backend provides secure authentication with Google Identity Platform and Cloud Storage integration using signed URLs. Users authenticate with Firebase, and the backend generates temporary signed URLs for secure file operations.

## 🏗️ Architecture

```
Frontend (React/Vue/etc) 
    ↓ Firebase ID Token
Backend (Flask) → Verify Token → Generate Signed URLs
    ↓ 
Google Cloud Storage (Private Buckets)
```

## 📋 Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Firebase Project** (can use same GCP project)
3. **Python 3.8+**
4. **Service Account Keys** for both Firebase and GCS

## 🚀 Step-by-Step Setup

### 1. Google Cloud Setup

#### Create Storage Bucket
```bash
# Create a private bucket
gsutil mb -p YOUR_PROJECT_ID gs://your-secure-bucket-name

# Set private access
gsutil iam ch allUsers:legacyObjectReader gs://your-secure-bucket-name
gsutil iam ch -d allUsers gs://your-secure-bucket-name
```

#### Create Service Account
```bash
# Create service account for storage access
gcloud iam service-accounts create storage-backend \
    --description="Backend service for secure storage access" \
    --display-name="Storage Backend"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:storage-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Generate key file
gcloud iam service-accounts keys create ./config/service-account.json \
    --iam-account=storage-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 2. Firebase Setup

#### Enable Identity Platform
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create/Select your project
3. Go to Authentication → Sign-in method
4. Enable desired providers (Email, Google, etc.)

#### Generate Firebase Admin SDK Key
1. Go to Project Settings → Service accounts
2. Click "Generate new private key"
3. Save as `./config/firebase-service-account.json`

### 3. Environment Configuration

#### Create `.env` file
```bash
cp .env.example .env
```

#### Update `.env` with your values:
```env
# Flask Configuration
FLASK_ENV=development
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters
PORT=5000

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_CLOUD_STORAGE_BUCKET=your-secure-bucket-name
GOOGLE_CLOUD_SERVICE_ACCOUNT_PATH=./config/service-account.json

# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH=./config/firebase-service-account.json
FIREBASE_PROJECT_ID=your-firebase-project-id

# CORS Origins (your frontend URLs)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### 4. Installation

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Create Config Directory
```bash
mkdir config
# Place your service account JSON files in ./config/
```

### 5. Security Configuration

#### IAM Conditions (Recommended)
Add IAM conditions to restrict access:

```json
{
  "bindings": [
    {
      "role": "roles/storage.objectViewer",
      "members": ["serviceAccount:storage-backend@PROJECT_ID.iam.gserviceaccount.com"],
      "condition": {
        "title": "User Directory Access",
        "description": "Only access user-specific directories",
        "expression": "resource.name.startsWith('projects/_/buckets/BUCKET/objects/uploads/')"
      }
    }
  ]
}
```

#### Bucket CORS Configuration
```json
[
  {
    "origin": ["http://localhost:3000", "https://yourdomain.com"],
    "method": ["GET", "PUT", "POST"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
```

Apply CORS:
```bash
gsutil cors set cors.json gs://your-bucket-name
```

## 🚀 Running the Application

### Development
```bash
python secure_backend.py
```

### Production (with Gunicorn)
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 secure_backend:app
```

### With Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "secure_backend:app"]
```

## 🔒 Security Features Implemented

### ✅ Authentication & Authorization
- Firebase ID token verification
- JWT tokens for backend sessions
- User-isolated file storage (`uploads/{user_id}/`)
- Permission validation for all operations

### ✅ Signed URLs
- Temporary access (15-30 minutes)
- Method-specific (GET for download, PUT for upload)
- Automatic expiration
- No permanent public access

### ✅ Input Validation
- File type restrictions (images only)
- Filename sanitization
- Content-Type validation
- Request payload validation

### ✅ Storage Security
- Private buckets (no public access)
- User directory isolation
- File quota management
- Secure file naming with UUIDs

### ✅ Error Handling
- Detailed error responses
- Security-aware error messages
- Comprehensive logging
- Rate limiting ready

## 📱 Frontend Integration Example

### Authentication Flow
```javascript
// 1. User signs in with Firebase
import { signInWithEmailAndPassword } from 'firebase/auth';

const { user } = await signInWithEmailAndPassword(auth, email, password);
const idToken = await user.getIdToken();

// 2. Exchange Firebase token for backend JWT
const response = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ idToken })
});

const { access_token } = await response.json();

// 3. Use JWT for backend requests
const headers = { 'Authorization': `Bearer ${access_token}` };
```

### File Upload Flow
```javascript
// 1. Request upload URL
const uploadResponse = await fetch('/storage/upload-url', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    filename: file.name,
    contentType: file.type,
    fileSize: file.size
  })
});

const { upload_url, blob_name } = await uploadResponse.json();

// 2. Upload directly to Cloud Storage
await fetch(upload_url, {
  method: 'PUT',
  headers: { 'Content-Type': file.type },
  body: file
});

// 3. Generate caption
const captionResponse = await fetch('/ai/generate-caption', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({
    blobName: blob_name,
    style: 'Instagram'
  })
});
```

## 🔧 API Endpoints

### Authentication
- `POST /auth/login` - Exchange Firebase ID token for JWT
- `GET /health` - Health check

### Storage
- `POST /storage/upload-url` - Get signed URL for upload
- `POST /storage/download-url` - Get signed URL for download
- `GET /user/files` - List user's files
- `DELETE /user/files/<blob_name>` - Delete user's file

### AI Services
- `POST /ai/generate-caption` - Generate AI caption for image

### User Management
- `GET /user/quota` - Get storage quota information

## 🚀 Deployment Options

### Google Cloud Run
```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/secure-backend', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/secure-backend']
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'secure-backend',
           '--image', 'gcr.io/$PROJECT_ID/secure-backend',
           '--platform', 'managed',
           '--region', 'us-central1',
           '--allow-unauthenticated']
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: secure-backend
  template:
    metadata:
      labels:
        app: secure-backend
    spec:
      containers:
      - name: backend
        image: gcr.io/PROJECT_ID/secure-backend
        ports:
        - containerPort: 5000
        env:
        - name: GOOGLE_CLOUD_SERVICE_ACCOUNT_PATH
          value: "/secrets/service-account.json"
        volumeMounts:
        - name: service-account
          mountPath: /secrets
      volumes:
      - name: service-account
        secret:
          secretName: service-account-key
```

## 📊 Monitoring & Logging

### Cloud Logging
- All authentication attempts
- File operations with user context
- Error conditions with stack traces
- Performance metrics

### Recommended Alerts
- Failed authentication rate > 10/min
- Storage quota exceeded events
- AI model failures
- Unusual file access patterns

## 🛡️ Security Checklist

- [ ] Service account keys are not in version control
- [ ] Bucket has no public access
- [ ] CORS is configured properly
- [ ] IAM conditions are applied
- [ ] JWT secret is strong and unique
- [ ] Error messages don't leak sensitive info
- [ ] File uploads are validated
- [ ] User isolation is enforced
- [ ] Signed URLs have short expiration
- [ ] Rate limiting is implemented (if needed)

## 🔄 Next Steps

1. **Add rate limiting** with Redis
2. **Implement caching** for AI model results
3. **Add webhook support** for real-time updates
4. **Enhance monitoring** with custom metrics
5. **Add batch processing** for multiple images
6. **Implement content moderation**

## 🐛 Troubleshooting

### Common Issues

**Service Account Errors**
```bash
# Verify service account has proper permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:storage-backend@*"
```

**CORS Issues**
```bash
# Check current CORS configuration
gsutil cors get gs://your-bucket-name
```

**Firebase Token Errors**
- Ensure Firebase project ID matches
- Check service account has Firebase Admin privileges
- Verify ID token is not expired

This secure backend provides enterprise-grade security for your AI caption application with proper authentication, authorization, and data isolation. 🚀