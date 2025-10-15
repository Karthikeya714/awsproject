# � Secure AI Caption Generator

A secure backend system that combines **Google Identity Platform authentication** with **Cloud Storage signed URLs** for AI-powered image captioning. This implementation follows security best practices with user-isolated storage and temporary access tokens.

## 🏗️ Architecture Overview

```
Frontend (Web/Mobile)
    ↓ Firebase ID Token
Backend (Flask) 
    ↓ Verify Token & Generate Signed URLs  
Google Cloud Storage (Private Buckets)
    ↓ Secure File Operations
AI Processing (BLIP Model)
```

## ✨ Key Security Features

- **🔐 Firebase Authentication**: Secure user authentication with ID token verification
- **📝 Signed URLs**: Temporary, secure access to Cloud Storage (15-30 min expiration)
- **🏠 User Isolation**: Each user can only access their own files (`uploads/{user_id}/`)
- **🛡️ Input Validation**: File type restrictions, content validation, and sanitization
- **📊 Quota Management**: Per-user storage limits and usage tracking
- **🚫 No Public Access**: Private buckets with no permanent public URLs
- **⚡ JWT Tokens**: Backend session management with automatic expiration

## 🚀 Quick Start

### 1. Prerequisites Setup

#### Google Cloud Project
```bash
# Create project and enable APIs
gcloud projects create your-project-id
gcloud config set project your-project-id
gcloud services enable storage.googleapis.com
gcloud services enable firebase.googleapis.com
```

#### Create Storage Bucket (Private)
```bash
gsutil mb -p your-project-id gs://your-secure-bucket
gsutil iam ch -d allUsers gs://your-secure-bucket
```

#### Service Account Setup
```bash
# Create service account
gcloud iam service-accounts create storage-backend \
    --description="Secure backend storage access" \
    --display-name="Storage Backend Service"

# Grant permissions
gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:storage-backend@your-project-id.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Generate key
gcloud iam service-accounts keys create ./config/service-account.json \
    --iam-account=storage-backend@your-project-id.iam.gserviceaccount.com
```

### 2. Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create/select your project
3. Enable Authentication → Sign-in methods (Email, Google, etc.)
4. Download service account key: Project Settings → Service accounts → Generate key
5. Save as `./config/firebase-service-account.json`

### 3. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Installation & Run

#### Local Development
```bash
pip install -r requirements.txt
python secure_backend.py
```

#### Docker Deployment
```bash
docker-compose up --build
```

## 📱 Frontend Integration

### Authentication Flow
```javascript
// 1. Firebase authentication
const { user } = await signInWithEmailAndPassword(auth, email, password);
const idToken = await user.getIdToken();

// 2. Backend JWT exchange
const response = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idToken })
});
const { access_token } = await response.json();
```

### Secure File Upload
```javascript
// 1. Request signed upload URL
const uploadResponse = await fetch('/storage/upload-url', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${access_token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        filename: file.name,
        contentType: file.type,
        fileSize: file.size
    })
});

const { upload_url, blob_name } = await uploadResponse.json();

// 2. Direct upload to Cloud Storage (bypasses backend)
await fetch(upload_url, {
    method: 'PUT',
    headers: { 'Content-Type': file.type },
    body: file
});

// 3. Generate AI caption
const captionResponse = await fetch('/ai/generate-caption', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${access_token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        blobName: blob_name,
        style: 'Instagram' // Funny, Poetic, Aesthetic
    })
});
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Exchange Firebase ID token for JWT |
| `/storage/upload-url` | POST | Get signed URL for file upload |
| `/storage/download-url` | POST | Get signed URL for file download |
| `/ai/generate-caption` | POST | Generate AI caption for image |
| `/user/files` | GET | List user's files |
| `/user/quota` | GET | Get storage quota info |
| `/health` | GET | Service health check |

## 🛡️ Security Implementation

### User Isolation
```python
# All user files are stored with path isolation
blob_name = f"uploads/{user_id}/{timestamp}_{uuid}_{filename}"

# Access validation on every operation
def validate_user_access(blob_name, user_id):
    return blob_name.startswith(f"uploads/{user_id}/")
```

### Signed URL Generation
```python
# Temporary access with automatic expiration
url = blob.generate_signed_url(
    version="v4",
    expiration=timedelta(minutes=15),  # Short expiration
    method="GET",  # or PUT for uploads
    headers={'Content-Type': 'image/jpeg'} if method == 'PUT' else None
)
```

### Input Validation
```python
# File type validation
ALLOWED_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}

# Content sanitization
def sanitize_filename(filename):
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    return filename[:100]  # Length limit
```

## 📊 Monitoring & Security

### Cloud Logging Integration
- Authentication attempts and failures
- File operations with user context
- Security violations and access attempts
- Performance metrics and errors

### Recommended Security Measures
- [ ] Enable Cloud Armor for DDoS protection
- [ ] Set up IAM conditions for additional restrictions
- [ ] Implement rate limiting with Redis
- [ ] Add content scanning for uploaded files
- [ ] Configure alerts for suspicious activity
- [ ] Regular security audits and key rotation

## 🚀 Production Deployment

### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/secure-backend
gcloud run deploy secure-backend \
    --image gcr.io/PROJECT_ID/secure-backend \
    --platform managed \
    --region us-central1 \
    --set-env-vars="GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket"
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
    spec:
      containers:
      - name: backend
        image: gcr.io/PROJECT_ID/secure-backend
        env:
        - name: GOOGLE_CLOUD_SERVICE_ACCOUNT_PATH
          value: "/secrets/service-account.json"
        volumeMounts:
        - name: service-account
          mountPath: /secrets
```

## 📈 Performance Optimization

- **Model Caching**: AI models loaded once on startup
- **Connection Pooling**: Reused Cloud Storage connections  
- **Signed URL Caching**: Cache upload URLs for batch operations
- **Async Processing**: Background jobs for heavy AI operations
- **CDN Integration**: CloudFlare for global distribution

## 🐛 Troubleshooting

### Common Issues

**Firebase Authentication Errors**
```bash
# Check service account permissions
gcloud projects get-iam-policy PROJECT_ID --flatten="bindings[].members"
```

**Storage Access Issues**
```bash
# Verify bucket permissions
gsutil iam get gs://your-bucket-name
```

**CORS Problems**
```bash
# Set CORS policy
gsutil cors set cors.json gs://your-bucket-name
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Cloud Platform** for secure infrastructure
- **Firebase** for authentication services
- **Hugging Face Transformers** for AI models
- **Flask** for the backend framework

---

**🔒 Security Note**: This implementation prioritizes security with user isolation, signed URLs, and no permanent public access. Perfect for production applications requiring secure file handling with AI processing capabilities.