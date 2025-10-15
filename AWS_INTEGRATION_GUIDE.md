# AWS Integration Guide

This guide shows you how to use the AWS S3 and DynamoDB integration in your Image Caption Generator.

## 🎯 What This Does

- **S3**: Stores uploaded images in the cloud
- **DynamoDB**: Stores image metadata (caption, S3 URL, timestamp)

---

## ⚡ Quick Start (3 Steps)

### Step 1: Configure AWS CLI

Run this command and enter your AWS credentials:

```powershell
aws configure
```

You'll need:
- **AWS Access Key ID**: (from IAM user `image-caption-app`)
- **AWS Secret Access Key**: (from IAM user)
- **Default region**: `eu-north-1`
- **Default output format**: `json`

### Step 2: Run Setup Script

This will create your S3 bucket and DynamoDB table:

```powershell
.\setup_aws_integration.ps1
```

### Step 3: Update Bucket Name (if different)

Edit `app.py` and change this line if needed:

```python
S3_BUCKET_NAME = "image-caption-bucket-karthik"  # Replace with your bucket name
```

### Step 4: Run the App

```powershell
streamlit run app.py
```

---

## 🚀 How to Use

1. **Upload an Image** - Click "Upload your image"
2. **Generate Caption** - AI will analyze and create a caption
3. **Upload to S3** - Click "📤 Upload to S3" to store in cloud
4. **Save to DynamoDB** - Click "💾 Save to DynamoDB" to save metadata

---

## 📂 What Gets Created

### S3 Bucket
- **Name**: `image-caption-bucket-karthik`
- **Region**: `eu-north-1`
- **Purpose**: Stores uploaded images
- **Access**: Public read for uploaded images

### DynamoDB Table
- **Name**: `image_captions`
- **Primary Key**: `image_id` (String)
- **Attributes**:
  - `image_id`: Unique identifier
  - `timestamp`: When the caption was created
  - `caption_text`: The generated caption
  - `image_url`: Public S3 URL of the image

---

## 🔧 Files Created

| File | Purpose |
|------|---------|
| `aws_utils.py` | AWS S3 and DynamoDB helper functions |
| `setup_aws_integration.ps1` | Automated AWS resource setup |
| `app.py` (updated) | Main Streamlit app with AWS integration |

---

## 🛠️ Manual Setup (Alternative)

If the script fails, you can create resources manually:

### Create S3 Bucket

```powershell
aws s3api create-bucket --bucket image-caption-bucket-karthik --region eu-north-1 --create-bucket-configuration LocationConstraint=eu-north-1
```

### Create DynamoDB Table

```powershell
aws dynamodb create-table --table-name image_captions --attribute-definitions AttributeName=image_id,AttributeType=S --key-schema AttributeName=image_id,KeyType=HASH --billing-mode PAY_PER_REQUEST --region eu-north-1
```

---

## 🔍 Verify Your Setup

### Check S3 Bucket

```powershell
aws s3 ls s3://image-caption-bucket-karthik/
```

### Check DynamoDB Table

```powershell
aws dynamodb describe-table --table-name image_captions --region eu-north-1
```

### List All Items in DynamoDB

```powershell
aws dynamodb scan --table-name image_captions --region eu-north-1
```

---

## 💰 Cost Estimation

### Free Tier (First 12 months)
- **S3**: First 5 GB storage free
- **DynamoDB**: 25 GB storage + 25 read/write units free
- **Data Transfer**: 15 GB out free

### After Free Tier
- **S3**: ~$0.023 per GB/month
- **DynamoDB**: Pay-per-request (very cheap for small usage)
- **Example**: 100 images (~50 MB) + 100 captions = ~$0.01/month

---

## ⚠️ Troubleshooting

### Error: "NoCredentialsError"
**Solution**: Run `aws configure` and enter your AWS credentials

### Error: "BucketAlreadyExists"
**Solution**: Change the bucket name in `app.py` to something unique

### Error: "AccessDenied"
**Solution**: Make sure your IAM user has S3 and DynamoDB permissions

### Error: "Could not connect to endpoint"
**Solution**: Check your internet connection and AWS region

---

## 🗑️ Cleanup (Delete Resources)

If you want to delete everything:

```powershell
# Delete all objects in bucket
aws s3 rm s3://image-caption-bucket-karthik/ --recursive

# Delete bucket
aws s3api delete-bucket --bucket image-caption-bucket-karthik --region eu-north-1

# Delete DynamoDB table
aws dynamodb delete-table --table-name image_captions --region eu-north-1
```

---

## 📚 Additional Resources

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [AWS CLI Reference](https://docs.aws.amazon.com/cli/)

---

## 🎉 Next Steps

Once everything is working:

1. Try uploading multiple images
2. Check the DynamoDB table to see stored data
3. Visit the S3 URLs to see your uploaded images
4. Consider adding more features like image gallery or caption history

---

Need help? Check the main project documentation or open an issue!
