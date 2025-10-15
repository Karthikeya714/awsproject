# Troubleshooting Guide

## Issue: Images storing in S3 but not in DynamoDB

### Understanding the Workflow

The app requires a **two-step process** to save your data:

1. **Step 1: Upload to S3** - Stores the actual image file
2. **Step 2: Save to DynamoDB** - Stores the metadata (caption, URL, timestamp)

### Why This Design?

- **S3** is for storing large files (images)
- **DynamoDB** is for storing metadata and enables fast queries
- They work together: DynamoDB stores the S3 URL reference

### Common Issues & Solutions

#### ✅ **Issue: "Please upload to S3 first!" warning**
**Solution:** Click the "📤 Upload to S3" button BEFORE clicking "💾 Save to DynamoDB"

#### ✅ **Issue: Buttons are disabled/greyed out**
**Causes:**
- S3 button disabled = Already uploaded
- DynamoDB button disabled = Either not uploaded to S3 yet, or already saved

**Solution:** Check the "📊 Current Status" section to see what's been done

#### ✅ **Issue: Data not appearing in DynamoDB**
**Verification Steps:**
1. Check the status indicators show "✅ Uploaded" and "✅ Saved"
2. Look at "📚 Previously Saved Captions" section at the bottom
3. Click "🔄 Refresh Saved Captions" to reload
4. Run `python check_dynamodb.py` in terminal to verify

#### ✅ **Issue: New image not saving**
**Solution:** Upload a new image - this will reset the workflow states automatically

### Checking Your Data

#### Method 1: Using the App
Scroll down to the "📚 Previously Saved Captions" section at the bottom of the page

#### Method 2: Using Python Script
```bash
python check_dynamodb.py
```

#### Method 3: AWS Console
Visit: https://eu-north-1.console.aws.amazon.com/dynamodbv2/home?region=eu-north-1#item-explorer?table=image_captions

#### Method 4: AWS CLI
```bash
aws dynamodb scan --table-name image_captions --region eu-north-1
```

### Workflow Status Indicators

The app now shows clear status:

- **⏸️ Not uploaded** - Action needed
- **✅ Uploaded** - Completed successfully
- **Disabled button** - Already done or prerequisite not met

### Expected Data in DynamoDB

Each saved item should have:
- `image_id`: Unique identifier (UUID)
- `timestamp`: When it was saved (ISO format)
- `caption_text`: Your generated caption
- `image_url`: S3 URL of the image

### Testing the Complete Flow

1. Upload an image
2. Generate a caption
3. Click "📤 Upload to S3" → Wait for "✅ Uploaded to S3!"
4. Click "💾 Save to DynamoDB" → Wait for "✅ Saved to DynamoDB!"
5. Check status shows both "✅ Uploaded" and "✅ Saved"
6. Scroll down to see your saved caption in the list

### Improvements Made

✅ Added status indicators for S3 and DynamoDB
✅ Buttons disable after successful completion
✅ Clear warning if trying to save without S3 upload
✅ Added "Previously Saved Captions" viewer
✅ Session state management prevents duplicate saves
✅ Visual feedback at every step

### Still Having Issues?

1. Check AWS credentials: `aws configure list`
2. Verify region is `eu-north-1`
3. Confirm S3 bucket exists: `image-caption-bucket-karthik`
4. Check DynamoDB table exists: `image_captions`
5. Look for error messages in the Streamlit app (red boxes)

### Quick Verification

Run this to see if DynamoDB is working:
```python
python check_dynamodb.py
```

If you see items listed, DynamoDB is working correctly! 🎉
