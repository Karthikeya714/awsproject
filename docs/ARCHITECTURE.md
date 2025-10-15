# Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Users / Browsers                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Amazon CloudFront (CDN)                      │
│                    ┌──────────────────────┐                      │
│                    │  AWS WAF (Optional)  │                      │
│                    └──────────────────────┘                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Application Load Balancer (ALB)                  │
│                      ┌───────────────────┐                       │
│                      │  Target Group      │                       │
│                      │  Health Checks     │                       │
│                      └───────────────────┘                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ECS Fargate Cluster                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  ECS Service (Auto-scaling)              │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │   │
│  │  │  Task 1    │  │  Task 2    │  │  Task N    │        │   │
│  │  │ Container  │  │ Container  │  │ Container  │        │   │
│  │  │ Streamlit  │  │ Streamlit  │  │ Streamlit  │        │   │
│  │  └────────────┘  └────────────┘  └────────────┘        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  AWS Cognito     │ │   Amazon S3      │ │   DynamoDB       │
│  User Pool       │ │   (Encrypted)    │ │   (Encrypted)    │
│  - Hosted UI     │ │   - Images       │ │   - Captions     │
│  - JWT Tokens    │ │   - Thumbnails   │ │   - Metadata     │
└──────────────────┘ └──────────────────┘ └──────────────────┘
           │
           │                 ┌──────────────────────────────────┐
           │                 │      AI/ML Services              │
           │                 │  ┌────────────────────────────┐  │
           └─────────────────┼─►│  Amazon Bedrock (Primary)  │  │
                             │  │  - Claude 3 Sonnet         │  │
                             │  └────────────────────────────┘  │
                             │  ┌────────────────────────────┐  │
                             │  │  Amazon Rekognition        │  │
                             │  │  - Label Detection         │  │
                             │  └────────────────────────────┘  │
                             │  ┌────────────────────────────┐  │
                             │  │  SageMaker (Fallback)      │  │
                             │  │  - BLIP / ViT-GPT2         │  │
                             │  └────────────────────────────┘  │
                             │  ┌────────────────────────────┐  │
                             │  │  Hugging Face API          │  │
                             │  │  - Tertiary Fallback       │  │
                             │  └────────────────────────────┘  │
                             └──────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring & Logging                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │  CloudWatch    │  │  CloudWatch    │  │  SNS Alerts    │   │
│  │  Logs          │  │  Metrics       │  │  (Email)       │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Secrets Management                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  AWS Secrets Manager (KMS Encrypted)                   │     │
│  │  - API Keys                                            │     │
│  │  - Database Credentials                               │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Authentication
1. User accesses application URL
2. CloudFront serves request to ALB
3. Streamlit app redirects to Cognito Hosted UI
4. User authenticates (username/password or social)
5. Cognito returns JWT tokens
6. User session established in Streamlit

### 2. Image Upload & Caption Generation
1. User selects image file (<10 MB)
2. Streamlit validates file (type, size)
3. Rate limiter checks user quota
4. Image uploaded to S3 (encrypted):
   - Original stored at `s3://bucket/images/{user_id}/{image_id}/original.jpg`
   - Thumbnail generated and stored
5. Optional: Rekognition detects labels
6. Caption service calls primary provider (Bedrock):
   - If fails, fallback to SageMaker
   - If fails, fallback to Hugging Face
7. Two captions generated (concise + creative)
8. Metadata saved to DynamoDB:
   ```json
   {
     "PK": "USER#{user_id}",
     "SK": "IMAGE#{image_id}",
     "concise_caption": "A cat on a mat",
     "creative_caption": "A fluffy cat...",
     "labels": ["cat", "animal"],
     "timestamp": "2025-10-14T12:00:00Z"
   }
   ```
9. Results displayed to user with presigned URLs

### 3. View History
1. User navigates to History tab
2. DynamoDB query: `PK = USER#{user_id}, SK begins_with IMAGE#`
3. Results paginated (20 per page)
4. Thumbnails served via presigned URLs (1-hour expiry)

### 4. Delete User Data
1. User confirms deletion
2. S3: Delete all objects with prefix `images/{user_id}/`
3. DynamoDB: Delete all items with `PK = USER#{user_id}`
4. Confirmation displayed

## Security Architecture

### Network Security
- **VPC**: Default VPC with public subnets
- **Security Groups**:
  - ALB: Allows 80, 443 from 0.0.0.0/0
  - ECS Tasks: Allows 8501 from ALB only
- **TLS**: Enforced via CloudFront and ALB
- **WAF**: Rate limiting, common attack patterns

### Identity & Access
- **User Authentication**: Cognito User Pool with MFA support
- **API Authentication**: JWT tokens from Cognito
- **IAM Roles**: Least-privilege policies per service
- **Secrets**: Stored in Secrets Manager (KMS encrypted)

### Data Protection
- **S3 Encryption**: SSE-AES256 at rest
- **DynamoDB Encryption**: KMS encryption at rest
- **TLS 1.2+**: In transit encryption enforced
- **Presigned URLs**: Time-limited access (1 hour)
- **EXIF Stripping**: Privacy protection

## Scalability

### Horizontal Scaling
- **ECS Fargate**: Auto-scales 2-10 tasks based on CPU/Memory
- **DynamoDB**: On-demand capacity (automatic scaling)
- **S3**: Unlimited storage, automatic partitioning
- **CloudFront**: Global CDN with edge locations

### Performance Optimization
- **CloudFront Caching**: Static assets and thumbnails
- **Connection Pooling**: boto3 client reuse
- **Lazy Loading**: Services initialized on first use
- **Thumbnail Generation**: 300px max dimension

## Monitoring & Observability

### Metrics
- **ECS**: CPU, Memory, Task count
- **ALB**: Request count, latency, errors
- **DynamoDB**: Consumed capacity, throttles
- **Application**: Custom metrics via CloudWatch

### Logging
- **Application Logs**: CloudWatch Logs (30-day retention)
- **Access Logs**: ALB access logs to S3
- **Audit Logs**: CloudTrail for API calls

### Alarms
- High error rate (5XX > 10/5min)
- High latency (>2s)
- ECS CPU > 80%
- DynamoDB throttling

## Cost Optimization

### Current Optimizations
- Fargate: Right-sized tasks (512 CPU, 1024 MB)
- DynamoDB: Pay-per-request billing
- S3: Lifecycle policies (90-day retention, Glacier after 60 days)
- CloudWatch: 30-day log retention

### Future Optimizations
- Fargate Spot instances for dev/staging
- S3 Intelligent-Tiering
- Reserved capacity for DynamoDB (if predictable load)
- CloudFront caching optimization

## Disaster Recovery

### Backup Strategy
- **S3**: Versioning enabled, cross-region replication (optional)
- **DynamoDB**: Point-in-time recovery enabled, on-demand backups
- **Terraform State**: S3 backend with versioning

### Recovery Time Objectives
- **RTO**: < 1 hour (redeploy with Terraform)
- **RPO**: < 1 hour (DynamoDB PITR)

### Failover
- Multi-AZ deployment via ECS Fargate
- ALB health checks with automatic replacement
- Provider fallback chain (Bedrock → SageMaker → HF)

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-14
