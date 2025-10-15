# 🚀 Quick Start: AWS Setup for DynamoDB

## Choose Your Option:

### ✅ Option 1: LocalStack (FREE, Docker Required)
- **Cost:** FREE
- **Requires:** Docker Desktop
- **Good for:** Development and testing
- **Data:** Lost when Docker stops

### ✅ Option 2: Real AWS (Costs ~$1-5/month)
- **Cost:** ~$1-5/month
- **Requires:** AWS Account + Credit Card
- **Good for:** Production
- **Data:** Persistent forever

---

## 🐳 OPTION 1: LocalStack Setup (RECOMMENDED FOR TESTING)

### Step 1: Install Docker Desktop

1. **Download:** https://www.docker.com/products/docker-desktop
2. **Install** and restart computer
3. **Launch** Docker Desktop
4. **Wait** for Docker to start (green whale icon in system tray)

### Step 2: Verify Docker

```powershell
docker --version
# Should show: Docker version 24.x.x
```

### Step 3: Run Setup Script

```powershell
cd d:\genaiproject
.\setup_localstack.ps1
```

**This script will:**
- Start LocalStack
- Create DynamoDB tables
- Verify everything works

### Step 4: Run Your App

```powershell
python -m streamlit run app\streamlit_app_auth.py
```

**Done!** Your app now uses DynamoDB via LocalStack! 🎉

---

## ☁️ OPTION 2: Real AWS Setup

### Step 1: Create AWS Account

1. Go to: https://aws.amazon.com
2. Click "Create an AWS Account"
3. Follow signup (requires credit card)

### Step 2: Create IAM User

1. Sign in to AWS Console
2. Go to IAM → Users → Create user
3. Username: `caption-app-user`
4. Add permissions:
   - AmazonDynamoDBFullAccess
   - AmazonS3FullAccess
5. Create user

### Step 3: Create Access Keys

1. Click on user → Security credentials
2. Create access key
3. Choose "Application running outside AWS"
4. **SAVE THE KEYS!**
   - Access Key ID
   - Secret Access Key

### Step 4: Configure AWS CLI

```powershell
# Install AWS CLI
pip install awscli

# Configure with your keys
aws configure

# Enter when prompted:
# AWS Access Key ID: [your key]
# AWS Secret Access Key: [your secret]
# Default region: us-east-1
# Default output: json
```

### Step 5: Run Setup Script

```powershell
cd d:\genaiproject
.\setup_real_aws.ps1
```

**This script will:**
- Create DynamoDB tables
- Create S3 bucket
- Verify resources

### Step 6: Update .env File

```env
# Change these lines:
S3_BUCKET_NAME=your-bucket-name-from-script
DYNAMODB_TABLE_NAME=caption-metadata
ENVIRONMENT=production
```

### Step 7: Run Your App

```powershell
python -m streamlit run app\streamlit_app_auth.py
```

**Done!** Your app now uses real AWS! 🎉

---

## 🔍 Verify It Works

### Test Signup:
1. Go to http://localhost:8501
2. Create account
3. **Stop the app** (Ctrl+C)
4. **Run it again**
5. Try to login with same credentials
6. ✅ If you can login, DynamoDB is working!

### Check LocalStack:
```powershell
awslocal dynamodb scan --table-name local-caption-metadata-users
```

### Check Real AWS:
```powershell
aws dynamodb scan --table-name caption-users --region us-east-1
```

---

## 🆘 Troubleshooting

### "Docker not found"
- Install Docker Desktop
- Restart computer
- Launch Docker Desktop

### "Cannot connect to endpoint"
- LocalStack: Check Docker is running: `docker ps`
- Real AWS: Check credentials: `aws sts get-caller-identity`

### "Table already exists"
- LocalStack: `docker-compose down` then run setup again
- Real AWS: Tables already created, skip to Step 6

---

## 💰 Costs

### LocalStack:
- **DynamoDB:** FREE
- **S3:** FREE (simulated)
- **Total:** $0/month ✅

### Real AWS:
- **DynamoDB:** ~$0.25/GB/month
- **S3:** ~$0.023/GB/month
- **Estimated:** $1-5/month for small usage

---

## 📊 What Gets Stored in DynamoDB

### Users Table:
- Email
- Password (hashed)
- Full name
- Created date

### Sessions Table:
- Session ID
- User ID
- Login time
- Expiry time

### Captions Table:
- Image metadata
- Generated captions
- Timestamps

---

## ✅ Next Steps

1. **Choose** LocalStack or Real AWS
2. **Follow** the steps above
3. **Run** the setup script
4. **Test** signup/signin
5. **Verify** data persists after restart

---

## 📚 Files Created

- `AWS_SETUP_GUIDE.md` - Detailed guide
- `setup_localstack.ps1` - LocalStack setup script
- `setup_real_aws.ps1` - Real AWS setup script
- `AWS_SETUP_QUICK.md` - This quick guide

---

**Start with LocalStack for free testing!** 🚀

Need help? Check the detailed guide: `AWS_SETUP_GUIDE.md`
