# 🎈 Streamlit Cloud Deployment Guide

## 🚀 Deploy Your App in 10 Minutes!

Streamlit Cloud is **FREE** and the **easiest** way to host your Streamlit app!

---

## ✨ Why Streamlit Cloud?

- ✅ **100% FREE** (Community plan)
- ✅ **No AWS setup needed**
- ✅ **Automatic HTTPS**
- ✅ **Custom subdomain** (yourapp.streamlit.app)
- ✅ **Auto-deploys from GitHub**
- ✅ **Built-in secrets management**

---

## 📋 Prerequisites

1. **GitHub Account** (free at [github.com](https://github.com))
2. **Streamlit Cloud Account** (free at [streamlit.io/cloud](https://streamlit.io/cloud))
3. **AWS Credentials** (for S3 and DynamoDB access)

---

## 🎯 Step-by-Step Deployment

### **Step 1: Push Your Code to GitHub** (5 minutes)

**Option A: Using GitHub Desktop (Easiest)**
1. Download [GitHub Desktop](https://desktop.github.com/)
2. Create new repository
3. Add your project folder
4. Commit and publish to GitHub

**Option B: Using Git Command Line**
```bash
cd "C:\Users\karth\Downloads\awsproject-main\awsproject-main"

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Streamlit Caption App"

# Create repository on GitHub, then:
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
git branch -M main
git push -u origin main
```

**Important Files to Include:**
- ✅ `app.py`
- ✅ `aws_utils.py`
- ✅ `requirements.txt`
- ✅ `.streamlit/config.toml` (optional)
- ❌ `.streamlit/secrets.toml` (DO NOT commit this!)

**Create `.gitignore` file:**
```
.streamlit/secrets.toml
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
.env
*.log
.DS_Store
```

---

### **Step 2: Sign Up for Streamlit Cloud** (2 minutes)

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Click **"Sign in with GitHub"**
3. Authorize Streamlit Cloud
4. Done! ✅

---

### **Step 3: Deploy Your App** (3 minutes)

1. **Click "New app"** in Streamlit Cloud dashboard

2. **Configure deployment:**
   - **Repository:** Select your GitHub repo
   - **Branch:** `main`
   - **Main file path:** `app.py`

3. **Click "Advanced settings"** ⚙️

4. **Add Secrets** (this is IMPORTANT!)
   - Click on **"Secrets"** tab
   - Copy the content below and paste it:

```toml
# Copy everything from here ↓

AWS_ACCESS_KEY_ID = "YOUR_AWS_ACCESS_KEY_HERE"
AWS_SECRET_ACCESS_KEY = "YOUR_AWS_SECRET_KEY_HERE"
AWS_DEFAULT_REGION = "eu-north-1"

S3_BUCKET_NAME = "image-caption-bucket-karthik"
DYNAMODB_TABLE_NAME = "image_captions"

hf_api_token = "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"

# Copy everything to here ↑
```

5. **Replace with your AWS credentials:**
   - Get from AWS Console → IAM → Security Credentials
   - Replace `YOUR_AWS_ACCESS_KEY_HERE`
   - Replace `YOUR_AWS_SECRET_KEY_HERE`

6. **Click "Save"**

7. **Click "Deploy!"** 🚀

---

### **Step 4: Wait for Deployment** (2-3 minutes)

- Streamlit will install dependencies
- You'll see build logs in real-time
- App will automatically open when ready

---

### **Step 5: Access Your App!** 🎉

Your app will be available at:
```
https://YOUR-APP-NAME.streamlit.app
```

**Share this URL with anyone!** 🌐

---

## 🔑 Getting AWS Credentials

### **Method 1: IAM User (Recommended)**

1. **Go to AWS Console** → IAM → Users
2. **Click "Add user"**
3. **User name:** `streamlit-app-user`
4. **Access type:** ✅ Programmatic access
5. **Next: Permissions**
6. **Attach policies:**
   - `AmazonS3FullAccess`
   - `AmazonDynamoDBFullAccess`
7. **Next → Create user**
8. **IMPORTANT:** Copy the credentials:
   - Access Key ID
   - Secret Access Key
   - You can only see these ONCE!

### **Method 2: Using Existing Credentials**

```bash
# If you already ran `aws configure`, get them from:
# Windows:
type %USERPROFILE%\.aws\credentials

# Mac/Linux:
cat ~/.aws/credentials
```

---

## 📝 Update Your Code for Streamlit Cloud

Your `app.py` already reads secrets correctly, but verify it uses:

```python
# At the top of app.py
import streamlit as st

# AWS Configuration - reads from Streamlit secrets
S3_BUCKET_NAME = st.secrets.get("S3_BUCKET_NAME", "image-caption-bucket-karthik")
DYNAMODB_TABLE_NAME = st.secrets.get("DYNAMODB_TABLE_NAME", "image_captions")

# HuggingFace API Token
try:
    HF_API_TOKEN = st.secrets["hf_api_token"]
except:
    HF_API_TOKEN = None
```

**Update `aws_utils.py` to use Streamlit secrets:**

```python
import boto3
import streamlit as st

# Read AWS credentials from Streamlit secrets
aws_access_key = st.secrets.get("AWS_ACCESS_KEY_ID")
aws_secret_key = st.secrets.get("AWS_SECRET_ACCESS_KEY")
aws_region = st.secrets.get("AWS_DEFAULT_REGION", "eu-north-1")

# Initialize AWS clients
s3_client = boto3.client(
    's3',
    region_name=aws_region,
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

dynamodb = boto3.resource(
    'dynamodb',
    region_name=aws_region,
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)
```

---

## 📦 Requirements.txt

Make sure your `requirements.txt` includes:

```txt
streamlit>=1.28.0
transformers>=4.30.0
torch>=2.0.0
pillow>=9.5.0
boto3>=1.28.0
accelerate>=0.20.0
```

---

## 🎨 Optional: Custom Configuration

Create `.streamlit/config.toml` (if not exists):

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

---

## 🔄 Auto-Deploy Updates

Once deployed, **every push to GitHub automatically redeploys!**

```bash
# Make changes to your code
git add .
git commit -m "Updated caption templates"
git push

# Streamlit Cloud automatically redeploys! 🎉
```

---

## 💰 Cost Breakdown

### **Streamlit Cloud:**
```
Community Plan:  FREE ✅
- 1 app deployment
- Automatic HTTPS
- Custom subdomain
- 1GB RAM
- 800 hours/month
```

### **AWS Services (You Pay):**
```
S3 Storage:      $0.023/GB/month
DynamoDB:        Free tier (25GB)
Data Transfer:   $0.09/GB

Example:
1000 images (~500MB): $0.01/month
1000 DB operations:   $0.001/month

Total: ~$0.01-0.05/month 💰
```

---

## 🐛 Troubleshooting

### **Issue: "Module not found"**

**Solution:** Update `requirements.txt`
```bash
# Test locally first:
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Updated requirements"
git push
```

### **Issue: "AWS credentials not found"**

**Solution:** 
1. Go to Streamlit Cloud → Your app → Settings
2. Click "Secrets"
3. Verify AWS credentials are correct
4. Click "Save"
5. App will automatically restart

### **Issue: "S3 Access Denied"**

**Solution:**
- Check IAM user has S3 permissions
- Verify bucket name is correct
- Check bucket exists in eu-north-1 region

### **Issue: "Out of memory"**

**Solution:**
- Upgrade to Streamlit Cloud paid plan ($20/month)
- Or optimize model loading with @st.cache_resource

---

## 🔒 Security Best Practices

### **1. Never Commit Secrets!**
```bash
# Always in .gitignore:
.streamlit/secrets.toml
.env
*.key
*.pem
```

### **2. Use Environment-Specific Secrets**
- Development: Local secrets.toml
- Production: Streamlit Cloud secrets

### **3. Rotate AWS Keys Regularly**
- Create new keys every 90 days
- Delete old keys from IAM

### **4. Use Least Privilege**
- IAM user only needs S3 and DynamoDB access
- Don't use root account credentials

---

## 📊 Monitoring Your App

### **View Logs:**
1. Go to Streamlit Cloud dashboard
2. Click on your app
3. Click "Manage app"
4. View logs in real-time

### **Check Usage:**
- Streamlit Cloud shows:
  - Active users
  - Resource usage
  - Error logs

---

## 🎯 Complete Deployment Checklist

**Before Deployment:**
- [ ] Code tested locally
- [ ] requirements.txt is complete
- [ ] .gitignore includes secrets.toml
- [ ] Code pushed to GitHub
- [ ] AWS credentials ready

**During Deployment:**
- [ ] Streamlit Cloud account created
- [ ] Repository connected
- [ ] Secrets configured correctly
- [ ] App deployed successfully

**After Deployment:**
- [ ] App loads without errors
- [ ] Can upload images
- [ ] S3 upload works
- [ ] DynamoDB saves work
- [ ] Share URL with others!

---

## 🚀 Advanced: Custom Domain

Want `yourapp.com` instead of `yourapp.streamlit.app`?

**Streamlit Cloud Team Plan ($250/month):**
- Custom domains
- SSO authentication
- Priority support

**Alternative (Free):**
Use Cloudflare Workers or Vercel to proxy:
```
yourapp.com → yourapp.streamlit.app
```

---

## 📞 Support & Resources

- **Streamlit Docs:** [docs.streamlit.io](https://docs.streamlit.io/)
- **Community Forum:** [discuss.streamlit.io](https://discuss.streamlit.io/)
- **Deployment Docs:** [docs.streamlit.io/streamlit-cloud](https://docs.streamlit.io/streamlit-cloud)
- **Status Page:** [status.streamlit.io](https://status.streamlit.io/)

---

## 🎉 Success!

Your app is now live on Streamlit Cloud! 🌟

**What you get:**
- ✅ Public URL (https://your-app.streamlit.app)
- ✅ Automatic HTTPS
- ✅ Auto-deploys from GitHub
- ✅ Free hosting
- ✅ Share with anyone!

**Next steps:**
1. Share your app URL
2. Monitor usage
3. Add new features
4. Push to GitHub (auto-deploys!)

---

## 📝 Quick Reference

**Your secrets format:**
```toml
AWS_ACCESS_KEY_ID = "AKIA..."
AWS_SECRET_ACCESS_KEY = "wJalr..."
AWS_DEFAULT_REGION = "eu-north-1"
S3_BUCKET_NAME = "image-caption-bucket-karthik"
DYNAMODB_TABLE_NAME = "image_captions"
hf_api_token = "hf_..."
```

**Deployment URL:**
```
https://share.streamlit.io/
```

**Your app URL:**
```
https://[your-username]-[repo-name]-[branch]-app.streamlit.app
```

---

**Ready to deploy? Go to [share.streamlit.io](https://share.streamlit.io/) now!** 🚀
