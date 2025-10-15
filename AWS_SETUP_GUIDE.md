# AWS Setup Guide - Using DynamoDB with LocalStack

## 🎯 Overview

This guide will help you set up AWS services locally using LocalStack (Docker) or connect to real AWS.

---

## 📋 Prerequisites

1. ✅ Python installed (you have this)
2. ✅ Virtual environment created (you have this)
3. ❌ Docker Desktop (we'll install this)

---

## 🐳 OPTION 1: Local Testing with LocalStack (FREE)

### Step 1: Install Docker Desktop

**Download and Install:**
1. Go to: https://www.docker.com/products/docker-desktop
2. Download "Docker Desktop for Windows"
3. Run the installer
4. **IMPORTANT:** During installation:
   - Enable "Use WSL 2 instead of Hyper-V" (recommended)
   - Restart computer when prompted
5. After restart, launch Docker Desktop
6. Wait for Docker to start (whale icon in system tray should be green)

**Verify Installation:**
```powershell
docker --version
# Should show: Docker version 24.x.x

docker-compose --version
# Should show: docker-compose version 2.x.x
```

---

### Step 2: Start LocalStack

LocalStack simulates AWS services on your computer for FREE!

**Start LocalStack:**
```powershell
cd d:\genaiproject

# Start LocalStack in background
docker-compose up -d

# Check it's running
docker-compose ps

# You should see:
# NAME            STATE     PORTS
# localstack      running   0.0.0.0:4566->4566/tcp
```

**Wait 30 seconds** for LocalStack to fully initialize.

---

### Step 3: Create DynamoDB Tables

```powershell
# Install AWS CLI tools
pip install awscli-local

# Create Users table
awslocal dynamodb create-table \
    --table-name local-caption-metadata-users \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
        AttributeName=email,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
    --global-secondary-indexes \
        "IndexName=email-index,KeySchema=[{AttributeName=email,KeyType=HASH}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5

# Create Sessions table
awslocal dynamodb create-table \
    --table-name local-caption-metadata-sessions \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
    --key-schema \
        AttributeName=session_id,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5

# Create Captions table
awslocal dynamodb create-table \
    --table-name local-caption-metadata \
    --attribute-definitions \
        AttributeName=PK,AttributeType=S \
        AttributeName=SK,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=PK,KeyType=HASH \
        AttributeName=SK,KeyType=RANGE \
    --global-secondary-indexes \
        "IndexName=user-index,KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=SK,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5}" \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5

# Verify tables created
awslocal dynamodb list-tables
```

---

### Step 4: Update Environment Variables

Edit your `.env` file:

```env
# AWS Configuration (LocalStack)
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_ENDPOINT_URL=http://localhost:4566

# S3 Configuration
S3_BUCKET_NAME=local-test-bucket
S3_PRESIGNED_URL_EXPIRY=3600

# DynamoDB Configuration
DYNAMODB_TABLE_NAME=local-caption-metadata
DYNAMODB_ENDPOINT_URL=http://localhost:4566

# Caption Provider Settings
CAPTION_PROVIDER=huggingface
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Hugging Face
HF_API_TOKEN=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

# Rekognition
USE_REKOGNITION=false

# Environment
ENVIRONMENT=local

# App Configuration
APP_NAME=image-caption-generator
LOG_LEVEL=INFO
```

---

### Step 5: Run App with DynamoDB

```powershell
cd d:\genaiproject
.\venv\Scripts\Activate.ps1
python -m streamlit run app\streamlit_app_auth.py
```

**Your app now uses DynamoDB (LocalStack)!** 🎉

---

## ☁️ OPTION 2: Real AWS (Production)

### Step 1: Create AWS Account

1. Go to: https://aws.amazon.com
2. Click "Create an AWS Account"
3. Follow the signup process
4. Add payment method (required, but free tier available)

---

### Step 2: Create IAM User

1. Sign in to AWS Console: https://console.aws.amazon.com
2. Go to IAM service
3. Click "Users" → "Create user"
4. Username: `caption-app-user`
5. Enable "Provide user access to the AWS Management Console" (optional)
6. Click "Next"
7. Select "Attach policies directly"
8. Add these policies:
   - ✅ `AmazonDynamoDBFullAccess`
   - ✅ `AmazonS3FullAccess`
   - ✅ `CloudWatchLogsFullAccess`
9. Click "Create user"

---

### Step 3: Create Access Keys

1. Click on the user you just created
2. Go to "Security credentials" tab
3. Scroll to "Access keys"
4. Click "Create access key"
5. Select "Application running outside AWS"
6. Click "Next" → "Create access key"
7. **IMPORTANT:** Save these values:
   - Access Key ID: `AKIAXXXXXXXXXXXXXXXX`
   - Secret Access Key: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
8. Download the CSV file as backup

---

### Step 4: Configure AWS CLI

```powershell
# Install AWS CLI if not already installed
pip install awscli

# Configure AWS credentials
aws configure

# Enter when prompted:
AWS Access Key ID: [paste your access key]
AWS Secret Access Key: [paste your secret key]
Default region name: us-east-1
Default output format: json
```

**Verify:**
```powershell
aws sts get-caller-identity
# Should show your AWS account ID
```

---

### Step 5: Create DynamoDB Tables in AWS

```powershell
# Create Users table
aws dynamodb create-table \
    --table-name caption-users \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
        AttributeName=email,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
    --global-secondary-indexes \
        "IndexName=email-index,KeySchema=[{AttributeName=email,KeyType=HASH}],Projection={ProjectionType=ALL}" \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

# Create Sessions table
aws dynamodb create-table \
    --table-name caption-sessions \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
    --key-schema \
        AttributeName=session_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

# Create Captions table
aws dynamodb create-table \
    --table-name caption-metadata \
    --attribute-definitions \
        AttributeName=PK,AttributeType=S \
        AttributeName=SK,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=PK,KeyType=HASH \
        AttributeName=SK,KeyType=RANGE \
    --global-secondary-indexes \
        "IndexName=user-index,KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=SK,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

# Verify tables
aws dynamodb list-tables --region us-east-1
```

---

### Step 6: Create S3 Bucket

```powershell
# Choose a UNIQUE bucket name (must be globally unique)
$BUCKET_NAME = "your-name-caption-images-2025"

# Create bucket
aws s3 mb s3://$BUCKET_NAME --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket $BUCKET_NAME \
    --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block \
    --bucket $BUCKET_NAME \
    --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Verify
aws s3 ls
```

---

### Step 7: Update Environment for Real AWS

Edit `.env`:

```env
# AWS Configuration (REAL AWS)
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1
# AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY will be read from ~/.aws/credentials

# S3 Configuration
S3_BUCKET_NAME=your-name-caption-images-2025
S3_PRESIGNED_URL_EXPIRY=3600

# DynamoDB Configuration
DYNAMODB_TABLE_NAME=caption-metadata

# Caption Provider Settings
CAPTION_PROVIDER=huggingface
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Hugging Face
HF_API_TOKEN=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

# Rekognition
USE_REKOGNITION=false

# Environment
ENVIRONMENT=production

# App Configuration
APP_NAME=image-caption-generator
LOG_LEVEL=INFO
```

---

### Step 8: Run App with Real AWS

```powershell
cd d:\genaiproject
.\venv\Scripts\Activate.ps1
python -m streamlit run app\streamlit_app_auth.py
```

---

## 🔧 Troubleshooting

### Docker Issues

**Problem:** "Cannot connect to Docker daemon"
```powershell
# Solution: Make sure Docker Desktop is running
# Check system tray for whale icon
# If not running, launch Docker Desktop
```

**Problem:** "Port 4566 already in use"
```powershell
# Solution: Stop LocalStack and restart
docker-compose down
docker-compose up -d
```

---

### AWS Issues

**Problem:** "Unable to locate credentials"
```powershell
# Solution: Reconfigure AWS CLI
aws configure
# Enter your access key and secret key again
```

**Problem:** "AccessDenied" errors
```powershell
# Solution: Check IAM user has correct permissions
aws iam list-attached-user-policies --user-name caption-app-user
```

---

## 💰 Cost Estimates

### LocalStack (Option 1):
- **Cost:** FREE ✅
- Docker runs on your computer
- No AWS charges

### Real AWS (Option 2):
- **DynamoDB:** $0.25/GB/month (first 25 GB free)
- **S3:** $0.023/GB/month (first 5 GB free for 12 months)
- **Data Transfer:** $0.09/GB (first 100 GB/month free)
- **Estimated:** $1-5/month for small usage

---

## 📊 Verify Everything Works

### Check LocalStack Tables:
```powershell
awslocal dynamodb list-tables
awslocal dynamodb describe-table --table-name local-caption-metadata-users
```

### Check Real AWS Tables:
```powershell
aws dynamodb list-tables --region us-east-1
aws dynamodb describe-table --table-name caption-users --region us-east-1
```

### Check S3 Buckets:
```powershell
aws s3 ls
```

---

## 🎯 Next Steps

1. **Choose your option** (LocalStack or Real AWS)
2. **Follow the steps** above
3. **Run the app:** `python -m streamlit run app\streamlit_app_auth.py`
4. **Test signup/signin** - data now persists in DynamoDB!
5. **Upload images** - stored in S3 (if configured)

---

## 🆘 Need Help?

**LocalStack not working?**
- Check Docker is running: `docker ps`
- Check LocalStack logs: `docker-compose logs localstack`
- Restart: `docker-compose restart`

**AWS not working?**
- Verify credentials: `aws sts get-caller-identity`
- Check region: Make sure using `us-east-1`
- Check IAM permissions

---

## 📚 Resources

- Docker Desktop: https://www.docker.com/products/docker-desktop
- LocalStack Docs: https://docs.localstack.cloud
- AWS DynamoDB: https://docs.aws.amazon.com/dynamodb/
- AWS CLI: https://aws.amazon.com/cli/
- AWS Free Tier: https://aws.amazon.com/free/

---

**Ready to start? Choose Option 1 (LocalStack) for free testing!** 🚀
