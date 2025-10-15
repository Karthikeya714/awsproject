# 🚀 Complete Beginner's Guide - Image Caption Generator

This guide assumes you have **zero experience** with AWS, Python, or Docker. Follow every step carefully.

---

## 📋 Table of Contents

1. [Prerequisites - Install Required Software](#step-1-prerequisites)
2. [Set Up AWS Account](#step-2-aws-account-setup)
3. [Install Python & Dependencies](#step-3-python-setup)
4. [Test Locally with Docker](#step-4-local-testing)
5. [Configure AWS CLI](#step-5-aws-cli-configuration)
6. [Set Up GitHub Repository](#step-6-github-setup)
7. [Deploy Infrastructure](#step-7-deploy-infrastructure)
8. [Verify Deployment](#step-8-verify-deployment)
9. [Troubleshooting](#step-9-troubleshooting)

---

## 🎯 STEP 1: Prerequisites

### What You Need to Install

#### 1.1 Install Python (Required)

**Download & Install:**
1. Go to https://www.python.org/downloads/
2. Download Python 3.11 (click the yellow "Download Python 3.11.x" button)
3. Run the installer
4. ✅ **IMPORTANT**: Check "Add Python to PATH" before clicking Install
5. Click "Install Now"

**Verify Installation:**
```powershell
# Open PowerShell and type:
python --version
# Should show: Python 3.11.x

pip --version
# Should show: pip 23.x.x
```

#### 1.2 Install Git (Required)

**Download & Install:**
1. Go to https://git-scm.com/download/win
2. Download the installer
3. Run installer with default options
4. Click "Next" through all screens

**Verify Installation:**
```powershell
git --version
# Should show: git version 2.x.x
```

#### 1.3 Install Docker Desktop (Required)

**Download & Install:**
1. Go to https://www.docker.com/products/docker-desktop
2. Click "Download for Windows"
3. Run the installer
4. Restart your computer when prompted
5. Launch Docker Desktop
6. Wait for Docker to start (icon in system tray should be green)

**Verify Installation:**
```powershell
docker --version
# Should show: Docker version 24.x.x

docker-compose --version
# Should show: Docker Compose version 2.x.x
```

#### 1.4 Install AWS CLI (Required)

**Download & Install:**
1. Go to https://aws.amazon.com/cli/
2. Download AWS CLI for Windows (MSI installer)
3. Run the installer
4. Click "Next" through all screens
5. Close and reopen PowerShell

**Verify Installation:**
```powershell
aws --version
# Should show: aws-cli/2.x.x
```

#### 1.5 Install Terraform (Required)

**Download & Install:**
1. Go to https://www.terraform.io/downloads
2. Download "Windows AMD64" zip file
3. Extract the zip file
4. Move `terraform.exe` to `C:\terraform\`
5. Add to PATH:
   - Press Windows Key + R
   - Type: `sysdm.cpl` and press Enter
   - Click "Advanced" tab
   - Click "Environment Variables"
   - Under "System variables", find "Path" and click "Edit"
   - Click "New"
   - Add: `C:\terraform`
   - Click "OK" on all windows
6. Close and reopen PowerShell

**Verify Installation:**
```powershell
terraform --version
# Should show: Terraform v1.5.x or higher
```

#### 1.6 Install VS Code (Recommended)

**Download & Install:**
1. Go to https://code.visualstudio.com/
2. Download installer
3. Run installer with default options

---

## 🏢 STEP 2: AWS Account Setup

### 2.1 Create AWS Account

1. Go to https://aws.amazon.com/
2. Click "Create an AWS Account"
3. Enter email address
4. Follow account creation wizard:
   - Enter contact information
   - Add credit card (required, but we'll use free tier)
   - Verify phone number
   - Select "Basic Support - Free"
5. Wait for account activation (may take a few minutes)

### 2.2 Enable Bedrock Model Access

**This is CRITICAL - without this, captions won't work!**

1. Sign in to AWS Console: https://console.aws.amazon.com/
2. In the top-right, select region: **US East (N. Virginia)** `us-east-1`
3. In search bar, type "Bedrock" and click on it
4. In left sidebar, click "Model access"
5. Click "Manage model access" button (orange)
6. Find "Anthropic" section
7. Check the box next to "Claude 3 Sonnet"
8. Click "Request model access" at bottom
9. Wait 2-5 minutes for approval (refresh page)
10. Status should change from "In progress" to "Access granted" ✅

### 2.3 Create IAM User for Deployment

**Why?** You need credentials to deploy from your computer.

1. In AWS Console, search for "IAM"
2. Click "Users" in left sidebar
3. Click "Create user" button
4. **User name**: `terraform-deploy`
5. Click "Next"
6. Select "Attach policies directly"
7. Search and check these policies:
   - ✅ `AdministratorAccess` (for initial setup - we'll restrict this later)
8. Click "Next", then "Create user"

**Create Access Keys:**
1. Click on the user you just created (`terraform-deploy`)
2. Click "Security credentials" tab
3. Scroll to "Access keys"
4. Click "Create access key"
5. Select "Command Line Interface (CLI)"
6. Check "I understand..." and click "Next"
7. Click "Create access key"
8. **IMPORTANT**: Copy both values:
   - Access key ID: `AKIAXXXXXXXXXXXXXXXX`
   - Secret access key: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
9. Save these somewhere safe (password manager)
10. Click "Done"

---

## 🐍 STEP 3: Python Setup

### 3.1 Navigate to Project Folder

```powershell
# Open PowerShell
cd d:\genaiproject
```

### 3.2 Create Python Virtual Environment

**Why?** Keeps project dependencies isolated.

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# If you get an error about execution policy, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activate again
.\venv\Scripts\Activate.ps1

# Your prompt should now show (venv) at the start
```

### 3.3 Install Python Dependencies

```powershell
# Make sure you're in d:\genaiproject with venv activated
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# This will take 2-5 minutes
# You should see lots of "Successfully installed..." messages
```

### 3.4 Verify Installation

```powershell
# Test imports
python -c "import streamlit; print('Streamlit OK')"
python -c "import boto3; print('Boto3 OK')"
python -c "import pytest; print('Pytest OK')"

# All should print "OK"
```

---

## 🐳 STEP 4: Local Testing

### 4.1 Create Environment File

```powershell
# Copy the example file
copy .env.example .env

# Open .env in notepad
notepad .env
```

**Edit the .env file** with these values:

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1

# S3 Configuration (use fake values for local testing)
S3_BUCKET_NAME=local-test-bucket
S3_PRESIGNED_URL_EXPIRY=3600

# DynamoDB Configuration
DYNAMODB_TABLE_NAME=local-caption-metadata

# Caption Provider Settings
CAPTION_PROVIDER=bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# SageMaker (optional - leave empty for local)
SAGEMAKER_ENDPOINT_NAME=

# Hugging Face (optional - leave empty for local)
HF_API_TOKEN=

# Rekognition
USE_REKOGNITION=false

# Cognito (leave empty for local testing)
COGNITO_USER_POOL_ID=
COGNITO_CLIENT_ID=
COGNITO_DOMAIN=

# Rate Limiting
RATE_LIMIT_MAX_REQUESTS=60
RATE_LIMIT_TIME_WINDOW=3600

# Environment
ENVIRONMENT=local

# Secrets Manager (leave empty for local)
SECRET_NAME=

# App Configuration
APP_NAME=image-caption-generator
LOG_LEVEL=INFO
```

Save and close the file.

### 4.2 Start LocalStack (Mock AWS)

**What is this?** LocalStack simulates AWS services on your computer for testing.

```powershell
# Make sure Docker Desktop is running (check system tray)

# Start LocalStack
docker-compose up -d

# Check it's running
docker-compose ps

# You should see localstack running on port 4566
```

**Wait 30 seconds** for LocalStack to fully start.

### 4.3 Run Streamlit App Locally

```powershell
# Make sure venv is activated (you should see (venv) in prompt)
# If not: .\venv\Scripts\Activate.ps1

# Run the app
streamlit run app/streamlit_app.py
```

**What should happen:**
1. Browser opens automatically
2. You see the login page
3. URL is: http://localhost:8501

**Expected behavior in local mode:**
- Login is bypassed (no Cognito in local mode)
- You can upload images
- Captions will show "Mock caption" (no real Bedrock locally)
- This is normal for local testing!

**Stop the app:** Press `Ctrl+C` in PowerShell

### 4.4 Run Tests

```powershell
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=backend --cov-report=html

# Open coverage report
start htmlcov/index.html
```

**Expected:** All tests should pass ✅

---

## ☁️ STEP 5: AWS CLI Configuration

### 5.1 Configure AWS Credentials

```powershell
# Run configuration wizard
aws configure

# You'll be prompted for:
AWS Access Key ID [None]: AKIAXXXXXXXXXXXXXXXX
# Paste the Access Key ID from Step 2.3

AWS Secret Access Key [None]: xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# Paste the Secret Access Key from Step 2.3

Default region name [None]: us-east-1
# Type: us-east-1

Default output format [None]: json
# Type: json
```

### 5.2 Verify AWS Access

```powershell
# Test connection
aws sts get-caller-identity

# Should show:
# {
#     "UserId": "AIDAXXXXXXXXXXXXXXXX",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/terraform-deploy"
# }
```

### 5.3 Create S3 Bucket for Terraform State

**Why?** Terraform needs a place to store its state file.

```powershell
# Choose a UNIQUE bucket name (must be globally unique)
# Format: your-name-terraform-state-uniqueid
# Example: john-smith-terraform-state-2025

$BUCKET_NAME = "your-unique-name-terraform-state-2025"

# Create bucket
aws s3 mb s3://$BUCKET_NAME --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning --bucket $BUCKET_NAME --versioning-configuration Status=Enabled

# Verify
aws s3 ls
# Should show your bucket
```

### 5.4 Create DynamoDB Table for Terraform Lock

**Why?** Prevents multiple people from running Terraform at the same time.

```powershell
# Create table
aws dynamodb create-table `
    --table-name terraform-lock `
    --attribute-definitions AttributeName=LockID,AttributeType=S `
    --key-schema AttributeName=LockID,KeyType=HASH `
    --billing-mode PAY_PER_REQUEST `
    --region us-east-1

# Wait 10 seconds for creation
Start-Sleep -Seconds 10

# Verify
aws dynamodb describe-table --table-name terraform-lock --region us-east-1
```

---

## 🐙 STEP 6: GitHub Setup

### 6.1 Create GitHub Account

1. Go to https://github.com/
2. Click "Sign up"
3. Follow the wizard to create account
4. Verify your email

### 6.2 Create New Repository

1. Click "+" icon (top-right)
2. Click "New repository"
3. **Repository name**: `image-caption-generator`
4. Select "Private"
5. Don't check any boxes (no README, no .gitignore)
6. Click "Create repository"

### 6.3 Push Code to GitHub

```powershell
# In d:\genaiproject folder
cd d:\genaiproject

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: Complete implementation"

# Add GitHub as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/image-caption-generator.git

# Push to GitHub
git push -u origin main

# If asked for credentials:
# Username: your_github_username
# Password: use a Personal Access Token (see below)
```

**Create Personal Access Token** (if needed):
1. GitHub → Settings (click your profile picture)
2. Developer settings (bottom of left sidebar)
3. Personal access tokens → Tokens (classic)
4. Generate new token → Generate new token (classic)
5. Note: "Git access"
6. Select scopes: ✅ repo (all)
7. Generate token
8. Copy the token and use it as password

### 6.4 Configure GitHub Secrets

**Why?** CI/CD needs AWS credentials to deploy.

1. Go to your repository on GitHub
2. Click "Settings" tab
3. Click "Secrets and variables" → "Actions"
4. Click "New repository secret" for each:

**Add these secrets:**

| Name | Value | How to Get |
|------|-------|------------|
| `AWS_ACCOUNT_ID` | 123456789012 | Run: `aws sts get-caller-identity` |
| `AWS_REGION` | us-east-1 | Your AWS region |
| `TF_STATE_BUCKET` | your-unique-name-terraform-state-2025 | Your S3 bucket from Step 5.3 |
| `TF_STATE_KEY` | terraform.tfstate | Use this exact value |
| `TF_STATE_REGION` | us-east-1 | Your AWS region |
| `S3_BUCKET_NAME` | your-name-caption-images-2025 | Choose unique name |
| `DYNAMODB_TABLE_NAME` | caption-metadata | Use this value |
| `COGNITO_DOMAIN` | your-app-auth-uniqueid | Choose unique name (letters/numbers only) |
| `ALARM_EMAIL` | your.email@example.com | Your email for alerts |

**For AWS credentials** (we'll use OIDC instead of keys - more secure):

Actually, let's configure OIDC for GitHub Actions (more secure):

### 6.5 Set Up GitHub OIDC Provider

```powershell
# Create trust policy file
@"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/image-caption-generator:*"
        }
      }
    }
  ]
}
"@ | Out-File -FilePath trust-policy.json -Encoding utf8

# Get your account ID
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)

# Replace YOUR_ACCOUNT_ID in trust-policy.json
(Get-Content trust-policy.json) -replace 'YOUR_ACCOUNT_ID', $ACCOUNT_ID | Set-Content trust-policy.json

# Replace YOUR_GITHUB_USERNAME (do this manually)
notepad trust-policy.json
# Replace YOUR_GITHUB_USERNAME with your actual GitHub username
# Save and close

# Create OIDC provider
aws iam create-open-id-connect-provider `
    --url https://token.actions.githubusercontent.com `
    --client-id-list sts.amazonaws.com `
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# Create IAM role for GitHub Actions
aws iam create-role `
    --role-name GitHubActionsDeployRole `
    --assume-role-policy-document file://trust-policy.json

# Attach admin policy (we'll restrict later)
aws iam attach-role-policy `
    --role-name GitHubActionsDeployRole `
    --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Get role ARN
aws iam get-role --role-name GitHubActionsDeployRole --query 'Role.Arn' --output text
# Copy this ARN
```

**Add GitHub Secret:**
- Name: `AWS_DEPLOY_ROLE_ARN`
- Value: `arn:aws:iam::123456789012:role/GitHubActionsDeployRole` (use your actual ARN)

---

## 🏗️ STEP 7: Deploy Infrastructure

### 7.1 Update Terraform Backend Configuration

```powershell
cd d:\genaiproject\infra\terraform

# Open main.tf
notepad main.tf
```

Find this section:
```hcl
backend "s3" {
  bucket         = "my-terraform-state-bucket"  # ← Change this
  key            = "terraform.tfstate"
  region         = "us-east-1"
  dynamodb_table = "terraform-lock"
  encrypt        = true
}
```

**Change to your bucket name:**
```hcl
backend "s3" {
  bucket         = "your-unique-name-terraform-state-2025"  # ← Your bucket from Step 5.3
  key            = "terraform.tfstate"
  region         = "us-east-1"
  dynamodb_table = "terraform-lock"
  encrypt        = true
}
```

Save and close.

### 7.2 Create Terraform Variables File

```powershell
# Create terraform.tfvars file
notepad terraform.tfvars
```

**Add this content** (update with your values):

```hcl
# AWS Configuration
aws_region     = "us-east-1"
aws_account_id = "123456789012"  # Your account ID from: aws sts get-caller-identity

# Environment
environment = "prod"
project_name = "caption-gen"

# S3 Configuration
s3_bucket_name = "your-name-caption-images-2025"  # Choose unique name

# DynamoDB Configuration
dynamodb_table_name = "caption-metadata"

# Cognito Configuration
cognito_domain = "your-app-auth-uniqueid"  # Choose unique (letters/numbers only, no dashes)

# ECS Configuration
ecs_task_cpu    = 512
ecs_task_memory = 1024
ecs_desired_count = 2
ecs_min_capacity = 2
ecs_max_capacity = 10

# Docker Image (we'll update this after first build)
docker_image = "123456789012.dkr.ecr.us-east-1.amazonaws.com/caption-generator:latest"

# Monitoring
alarm_email = "your.email@example.com"  # Your email for alerts

# Optional Features
enable_cloudfront = false  # Set to true after initial setup
enable_waf = false         # Set to true for production security

# Tags
tags = {
  Project     = "ImageCaptionGenerator"
  Environment = "Production"
  ManagedBy   = "Terraform"
}
```

Save and close.

### 7.3 Initialize Terraform

```powershell
# Make sure you're in infra/terraform folder
cd d:\genaiproject\infra\terraform

# Initialize Terraform
terraform init

# This will:
# - Download AWS provider
# - Configure S3 backend
# - Set up state locking
# Takes 1-2 minutes
```

**Expected output:**
```
Terraform has been successfully initialized!
```

### 7.4 Validate Terraform Configuration

```powershell
# Check for syntax errors
terraform validate

# Expected output:
# Success! The configuration is valid.
```

### 7.5 Plan Infrastructure

```powershell
# See what will be created
terraform plan -out=tfplan

# This will show ~50+ resources to be created:
# - S3 bucket
# - DynamoDB table
# - Cognito user pool
# - ECS cluster
# - And many more...
```

**Review the plan carefully!** Look for:
- ✅ Green "+" means resource will be created
- ❌ No red "-" (nothing should be destroyed on first run)

### 7.6 Apply Infrastructure (First Deployment)

**⚠️ WARNING: This will create AWS resources that cost money!**

**Estimated cost:** $30-60/month for low usage

```powershell
# Apply the plan
terraform apply tfplan

# Type: yes

# This will take 10-15 minutes
# Grab a coffee ☕
```

**What's happening:**
1. Creating S3 bucket (30 seconds)
2. Creating DynamoDB table (1 minute)
3. Creating Cognito user pool (2 minutes)
4. Creating VPC and networking (3 minutes)
5. Creating ECS cluster (2 minutes)
6. Creating monitoring (2 minutes)
7. Creating IAM roles (1 minute)

**Expected at end:**
```
Apply complete! Resources: 54 added, 0 changed, 0 destroyed.

Outputs:
alb_dns_name = "caption-gen-alb-1234567890.us-east-1.elb.amazonaws.com"
cognito_user_pool_id = "us-east-1_ABC123DEF"
ecr_repository_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/caption-generator"
...
```

**Save these outputs!** You'll need them.

---

## 🐳 STEP 8: Build and Deploy Application

### 8.1 Build Docker Image

```powershell
# Go back to project root
cd d:\genaiproject

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
# Replace 123456789012 with your account ID

# Build image
docker build -t caption-generator:latest .

# This takes 5-10 minutes first time
```

### 8.2 Tag and Push Image

```powershell
# Get ECR URL from Terraform output
cd infra\terraform
terraform output ecr_repository_url
# Copy this URL

# Go back to root
cd ..\..

# Tag image (replace with your ECR URL)
docker tag caption-generator:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/caption-generator:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/caption-generator:latest

# Takes 2-5 minutes
```

### 8.3 Update ECS Service

```powershell
# Force ECS to pull new image
aws ecs update-service `
    --cluster caption-gen-cluster `
    --service caption-gen-service `
    --force-new-deployment `
    --region us-east-1

# Wait for deployment (5-10 minutes)
aws ecs wait services-stable `
    --cluster caption-gen-cluster `
    --services caption-gen-service `
    --region us-east-1

# Check status
aws ecs describe-services `
    --cluster caption-gen-cluster `
    --services caption-gen-service `
    --region us-east-1 `
    --query 'services[0].deployments[0]'
```

### 8.4 Create Cognito Test User

```powershell
# Get user pool ID from Terraform
cd infra\terraform
$USER_POOL_ID = terraform output -raw cognito_user_pool_id
cd ..\..

# Create test user
aws cognito-idp admin-create-user `
    --user-pool-id $USER_POOL_ID `
    --username testuser `
    --user-attributes Name=email,Value=test@example.com Name=email_verified,Value=true `
    --temporary-password TempPass123! `
    --region us-east-1

# Set permanent password
aws cognito-idp admin-set-user-password `
    --user-pool-id $USER_POOL_ID `
    --username testuser `
    --password MySecurePass123! `
    --permanent `
    --region us-east-1
```

---

## ✅ STEP 9: Verify Deployment

### 9.1 Get Application URL

```powershell
cd infra\terraform

# Get ALB DNS name
terraform output alb_dns_name

# Example output: caption-gen-alb-1234567890.us-east-1.elb.amazonaws.com
```

### 9.2 Test Application

1. **Open browser** and go to the ALB DNS name:
   ```
   http://caption-gen-alb-1234567890.us-east-1.elb.amazonaws.com
   ```

2. **You should see:** Streamlit login page

3. **Login with:**
   - Username: `testuser`
   - Password: `MySecurePass123!`

4. **Test upload:**
   - Click "Upload Image" tab
   - Upload a JPEG/PNG image (max 10MB)
   - Click "Generate Captions"
   - Wait 2-5 seconds
   - You should see concise and creative captions!

5. **Test history:**
   - Click "History" tab
   - You should see your uploaded image

6. **Test deletion:**
   - Click "Delete My Data" tab
   - Click "Delete All My Data"
   - Confirm
   - Go back to History - should be empty

### 9.3 Check CloudWatch Logs

```powershell
# View application logs
aws logs tail /ecs/caption-generator --follow --region us-east-1

# Press Ctrl+C to stop
```

### 9.4 Check Monitoring Dashboard

1. Go to AWS Console: https://console.aws.amazon.com/cloudwatch/
2. Click "Dashboards" in left sidebar
3. Click "caption-gen-dashboard"
4. You should see graphs for:
   - ECS CPU/Memory
   - ALB response times
   - Error rates
   - DynamoDB metrics

### 9.5 Run Smoke Tests

```powershell
cd d:\genaiproject

# Set environment variables for testing
$env:ALB_URL = "http://caption-gen-alb-1234567890.us-east-1.elb.amazonaws.com"
$env:AWS_REGION = "us-east-1"

# Run smoke tests
pytest tests/e2e_smoke.py -v
```

---

## 🎉 SUCCESS!

If you've made it here, **congratulations!** You have:

✅ Installed all required tools  
✅ Set up AWS account with Bedrock access  
✅ Configured AWS CLI and Terraform  
✅ Deployed complete infrastructure  
✅ Built and pushed Docker image  
✅ Deployed application to ECS  
✅ Created test user  
✅ Verified everything works  

---

## 🔧 STEP 10: Troubleshooting

### Problem: "terraform init" fails

**Error:** "Error configuring S3 Backend"

**Solution:**
```powershell
# Check bucket exists
aws s3 ls s3://your-bucket-name

# If not found, create it:
aws s3 mb s3://your-bucket-name --region us-east-1
```

### Problem: "terraform apply" fails with permission errors

**Error:** "AccessDenied" or "UnauthorizedOperation"

**Solution:**
```powershell
# Verify AWS credentials
aws sts get-caller-identity

# Check IAM user has AdministratorAccess
aws iam list-attached-user-policies --user-name terraform-deploy
```

### Problem: Docker build fails

**Error:** "Cannot connect to Docker daemon"

**Solution:**
1. Open Docker Desktop
2. Wait for it to fully start (icon should be green)
3. Try again

### Problem: ECS tasks fail to start

**Error:** Tasks keep stopping

**Solution:**
```powershell
# Check ECS logs
aws logs tail /ecs/caption-generator --follow

# Common issues:
# - Missing environment variables
# - Docker image not found
# - Insufficient memory/CPU
```

### Problem: Cannot access application URL

**Error:** Site can't be reached

**Solution:**
```powershell
# Check ECS service status
aws ecs describe-services `
    --cluster caption-gen-cluster `
    --services caption-gen-service `
    --region us-east-1

# Check if tasks are running
aws ecs list-tasks --cluster caption-gen-cluster --region us-east-1

# Check ALB target health
aws elbv2 describe-target-health `
    --target-group-arn $(terraform output -raw target_group_arn) `
    --region us-east-1
```

### Problem: Bedrock "Access Denied"

**Error:** "Could not access bedrock runtime"

**Solution:**
1. Go to AWS Console → Bedrock
2. Click "Model access" in left sidebar
3. Make sure "Claude 3 Sonnet" shows "Access granted" ✅
4. If not, request access and wait 5 minutes

### Problem: High AWS costs

**Solution:**
```powershell
# Stop ECS service to save costs
aws ecs update-service `
    --cluster caption-gen-cluster `
    --service caption-gen-service `
    --desired-count 0 `
    --region us-east-1

# Destroy everything when done testing
cd infra\terraform
terraform destroy
# Type: yes
```

---

## 📚 Next Steps

### 1. Set Up Custom Domain (Optional)

1. Buy domain in Route 53
2. Create ACM certificate
3. Update ALB with HTTPS listener
4. Update Terraform with domain

### 2. Enable CloudFront CDN

```powershell
cd infra\terraform
notepad terraform.tfvars

# Change:
enable_cloudfront = true

# Apply
terraform apply
```

### 3. Set Up CI/CD

Your GitHub Actions are already configured! Every push to `main` will:
1. Run tests
2. Build Docker image
3. Push to ECR
4. Update ECS service

Test it:
```powershell
# Make a small change
echo "# Test" >> README.md

# Commit and push
git add .
git commit -m "Test CI/CD"
git push

# Go to GitHub → Actions tab to watch deployment
```

### 4. Monitor Costs

1. Go to AWS Console → Billing Dashboard
2. Set up billing alerts
3. Recommended: Set alert at $50/month

### 5. Learn More

- **Streamlit docs**: https://docs.streamlit.io/
- **AWS Bedrock docs**: https://docs.aws.amazon.com/bedrock/
- **Terraform docs**: https://www.terraform.io/docs/
- **ECS docs**: https://docs.aws.amazon.com/ecs/

---

## 🆘 Getting Help

**If you're stuck:**

1. **Check logs:**
   ```powershell
   aws logs tail /ecs/caption-generator --follow
   ```

2. **Check GitHub Issues:**
   - Search existing issues in your repo

3. **AWS Support:**
   - Basic support is included (forums)
   - Developer support: $29/month

4. **Common commands:**
   ```powershell
   # Check everything is healthy
   terraform output
   aws ecs describe-services --cluster caption-gen-cluster --services caption-gen-service
   aws s3 ls s3://your-bucket-name
   aws dynamodb describe-table --table-name caption-metadata
   ```

---

## 💰 Cost Management

### Monthly Cost Estimate

**Low usage (1K requests/month):** $30-60
- ECS Fargate: $20-30
- S3: $1-2
- DynamoDB: $1-2
- Bedrock: $5-10
- Other: $3-5

**Medium usage (10K requests/month):** $175-335

### How to Minimize Costs

1. **Stop when not using:**
   ```powershell
   aws ecs update-service --cluster caption-gen-cluster --service caption-gen-service --desired-count 0
   ```

2. **Use spot pricing** (advanced)
3. **Enable S3 lifecycle** (already configured)
4. **Use Graviton instances** (ARM) for ECS

### How to Destroy Everything

**⚠️ WARNING: This deletes everything!**

```powershell
cd d:\genaiproject\infra\terraform

# Destroy all infrastructure
terraform destroy

# Type: yes

# Delete S3 buckets (Terraform can't delete non-empty buckets)
aws s3 rb s3://your-terraform-state-bucket --force
aws s3 rb s3://your-caption-images-bucket --force

# Delete ECR images
aws ecr delete-repository --repository-name caption-generator --force
```

---

## ✅ Quick Reference

### Essential Commands

```powershell
# Activate Python environment
cd d:\genaiproject
.\venv\Scripts\Activate.ps1

# Run locally
streamlit run app/streamlit_app.py

# Run tests
pytest tests/ -v

# Deploy infrastructure
cd infra\terraform
terraform plan
terraform apply

# Build and deploy Docker
cd d:\genaiproject
docker build -t caption-generator:latest .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker tag caption-generator:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/caption-generator:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/caption-generator:latest

# Update ECS
aws ecs update-service --cluster caption-gen-cluster --service caption-gen-service --force-new-deployment

# Check logs
aws logs tail /ecs/caption-generator --follow

# Check status
aws ecs describe-services --cluster caption-gen-cluster --services caption-gen-service
```

---

## 🎓 What You Learned

By completing this guide, you now know:

✅ How to set up AWS account and services  
✅ How to use AWS CLI and configure credentials  
✅ How to create and use Python virtual environments  
✅ How to use Docker for containerization  
✅ How to write and deploy infrastructure as code (Terraform)  
✅ How to deploy applications to ECS Fargate  
✅ How to set up CI/CD with GitHub Actions  
✅ How to monitor applications with CloudWatch  
✅ How to troubleshoot cloud applications  

**You're now a cloud developer!** 🚀

---

## 📝 Checklist

Print this and check off as you go:

- [ ] Installed Python 3.11
- [ ] Installed Git
- [ ] Installed Docker Desktop
- [ ] Installed AWS CLI
- [ ] Installed Terraform
- [ ] Created AWS account
- [ ] Enabled Bedrock model access
- [ ] Created IAM user with access keys
- [ ] Configured AWS CLI credentials
- [ ] Created S3 bucket for Terraform state
- [ ] Created DynamoDB table for Terraform lock
- [ ] Created GitHub repository
- [ ] Pushed code to GitHub
- [ ] Configured GitHub secrets
- [ ] Set up GitHub OIDC for deployments
- [ ] Created Python virtual environment
- [ ] Installed Python dependencies
- [ ] Tested application locally
- [ ] Updated Terraform backend configuration
- [ ] Created terraform.tfvars file
- [ ] Ran terraform init
- [ ] Ran terraform plan
- [ ] Ran terraform apply
- [ ] Built Docker image
- [ ] Pushed image to ECR
- [ ] Updated ECS service
- [ ] Created Cognito test user
- [ ] Tested application in browser
- [ ] Verified monitoring dashboard
- [ ] Ran smoke tests
- [ ] Celebrated success! 🎉

---

**Need help?** Re-read the relevant section carefully, check the troubleshooting section, and verify each command output matches the expected result.

**Good luck!** 🍀
