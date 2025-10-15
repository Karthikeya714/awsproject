# 🎈 STREAMLIT CLOUD - COPY & PASTE GUIDE

## 🚀 Deploy to Streamlit Cloud in 3 Steps!

---

## ⚡ STEP 1: Copy Your Secrets

### **Copy this to Streamlit Cloud Secrets:**

```toml
AWS_ACCESS_KEY_ID = "YOUR_AWS_ACCESS_KEY_HERE"
AWS_SECRET_ACCESS_KEY = "YOUR_AWS_SECRET_KEY_HERE"
AWS_DEFAULT_REGION = "eu-north-1"
S3_BUCKET_NAME = "image-caption-bucket-karthik"
DYNAMODB_TABLE_NAME = "image_captions"
hf_api_token = "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"
```

**⚠️ IMPORTANT:** Replace these with YOUR actual AWS credentials:
- `YOUR_AWS_ACCESS_KEY_HERE` → Your AWS Access Key ID
- `YOUR_AWS_SECRET_KEY_HERE` → Your AWS Secret Access Key

---

## 🔑 STEP 2: Get Your AWS Credentials

### **Method 1: Create New IAM User (Recommended)**

1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Click **"Users"** → **"Add user"**
3. **Username:** `streamlit-cloud-user`
4. **Access type:** ✅ **Programmatic access**
5. Click **"Next: Permissions"**
6. **Attach policies:**
   - Search and select: `AmazonS3FullAccess`
   - Search and select: `AmazonDynamoDBFullAccess`
7. Click **"Next"** → **"Next"** → **"Create user"**
8. **COPY THESE NOW** (you can't see them again!):
   - ✅ **Access Key ID** (starts with `AKIA...`)
   - ✅ **Secret Access Key** (long random string)
9. Click **"Download .csv"** (backup)

### **Method 2: Use Existing Credentials**

**Windows PowerShell:**
```powershell
type $env:USERPROFILE\.aws\credentials
```

**Mac/Linux:**
```bash
cat ~/.aws/credentials
```

---

## 🌐 STEP 3: Deploy to Streamlit Cloud

### **3a. Push Code to GitHub**

```powershell
# In PowerShell, navigate to your project
cd "C:\Users\karth\Downloads\awsproject-main\awsproject-main"

# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Streamlit Cloud deployment"

# Push to GitHub (create repo first on github.com)
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```

### **3b. Deploy on Streamlit Cloud**

1. **Go to:** [share.streamlit.io](https://share.streamlit.io/)
2. **Sign in** with GitHub
3. Click **"New app"**
4. **Select:**
   - Repository: Your repo
   - Branch: main
   - Main file: `app.py`
5. Click **"Advanced settings"** ⚙️
6. **Paste secrets** (from Step 1) into the "Secrets" box
7. Click **"Deploy"**
8. **Wait 2-3 minutes** ⏱️
9. **Done!** 🎉

---

## 📋 Your Complete Secrets (Ready to Copy)

```toml
# ============================================
# COPY EVERYTHING BELOW THIS LINE
# ============================================

AWS_ACCESS_KEY_ID = "REPLACE_WITH_YOUR_ACCESS_KEY"
AWS_SECRET_ACCESS_KEY = "REPLACE_WITH_YOUR_SECRET_KEY"
AWS_DEFAULT_REGION = "eu-north-1"
S3_BUCKET_NAME = "image-caption-bucket-karthik"
DYNAMODB_TABLE_NAME = "image_captions"
hf_api_token = "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"

# ============================================
# COPY EVERYTHING ABOVE THIS LINE
# ============================================
```

---

## ✅ Checklist

**Before Deployment:**
- [ ] AWS IAM user created with S3 + DynamoDB permissions
- [ ] Access Key ID copied
- [ ] Secret Access Key copied
- [ ] Code pushed to GitHub
- [ ] Streamlit Cloud account created

**During Deployment:**
- [ ] Repository connected
- [ ] Secrets pasted correctly
- [ ] AWS credentials replaced
- [ ] Deploy button clicked

**After Deployment:**
- [ ] App loads successfully
- [ ] Can upload images
- [ ] S3 upload works
- [ ] DynamoDB saves work

---

## 💰 Cost

**Streamlit Cloud:** FREE ✅
**AWS Services:**
- S3: ~$0.01/month for 1000 images
- DynamoDB: FREE (25GB free tier)
- **Total: ~$0.01-0.05/month**

---

## 🎯 Quick Links

- **Deploy Now:** [share.streamlit.io](https://share.streamlit.io/)
- **AWS IAM:** [console.aws.amazon.com/iam/](https://console.aws.amazon.com/iam/)
- **Full Guide:** See `STREAMLIT_CLOUD_DEPLOY.md`

---

## ⚠️ Important Notes

1. **NEVER commit secrets to GitHub!**
   - Keep `.streamlit/secrets.toml` in `.gitignore`

2. **Replace placeholder credentials**
   - `YOUR_AWS_ACCESS_KEY_HERE` → Your actual key
   - `YOUR_AWS_SECRET_KEY_HERE` → Your actual secret

3. **Test locally first**
   - Make sure app works on your computer
   - Then deploy to Streamlit Cloud

---

## 🐛 Common Issues

### **Issue: "AWS credentials not found"**
**Fix:** 
- Go to Streamlit Cloud → Your app → Settings
- Check secrets are pasted correctly
- Make sure no extra spaces or quotes

### **Issue: "S3 Access Denied"**
**Fix:**
- Check IAM user has `AmazonS3FullAccess`
- Verify bucket name is correct
- Check bucket exists in `eu-north-1` region

### **Issue: "Module not found"**
**Fix:**
- Check `requirements.txt` exists
- Verify all packages are listed
- Redeploy app

---

## 🎉 Success!

Your app will be live at:
```
https://[username]-[repo]-[branch]-app.streamlit.app
```

**Share this URL with anyone!** 🌐

---

## 📞 Need More Help?

- **Full deployment guide:** `STREAMLIT_CLOUD_DEPLOY.md`
- **Streamlit docs:** [docs.streamlit.io](https://docs.streamlit.io/)
- **Community forum:** [discuss.streamlit.io](https://discuss.streamlit.io/)

---

**Ready? Go to [share.streamlit.io](https://share.streamlit.io/) and deploy!** 🚀
