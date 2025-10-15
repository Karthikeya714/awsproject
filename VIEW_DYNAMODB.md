# How to View Your DynamoDB Storage

You have **3 ways** to view your DynamoDB captions:

---

## ✅ **Current Status**

📊 **DynamoDB Table:** `image_captions`  
🌍 **Region:** `eu-north-1`  
📝 **Items Stored:** 2 captions

---

## **Method 1: Python Script (Quick Check)** 💻

Run this command to see all stored data:

```powershell
C:/Python313/python.exe check_dynamodb.py
```

**Output shows:**
- Image ID
- Timestamp
- Caption text
- S3 image URL

---

## **Method 2: Streamlit Gallery App** 🖼️

View your captions in a beautiful gallery interface:

```powershell
C:/Python313/python.exe -m streamlit run view_captions.py
```

**Features:**
- ✅ See images and captions together
- ✅ View all metadata
- ✅ Refresh to see new uploads
- ✅ Click URLs to open images

---

## **Method 3: AWS Console (Web)** 🌐

View in your browser:

**Direct Link:**
https://eu-north-1.console.aws.amazon.com/dynamodbv2/home?region=eu-north-1#item-explorer?table=image_captions

**Steps:**
1. Click the link above (or go to AWS Console)
2. Navigate to: DynamoDB → Tables → image_captions
3. Click "Explore table items"
4. See all your stored captions

---

## **Method 4: AWS CLI** 📟

If you want to use command line:

```powershell
# View all items (with proper encoding)
& "C:\Program Files\Amazon\AWSCLIV2\aws.exe" dynamodb scan --table-name image_captions --region eu-north-1 --output json > captions.json

# Then view the file
notepad captions.json
```

---

## **Your Current Data** 📊

You have **2 captions** stored:

### Item #1
- **Image ID:** d87fbfda-c1a3-47a1-a098-041a0c1ffda0
- **Timestamp:** 2025-10-15T15:48:17.864896
- **Caption:** Current mood: a table with different types of font and numbers and loving it! 😍 #Mood #InstaDaily #Life #Happy #Blessed
- **Image URL:** https://image-caption-bucket-karthik.s3.eu-north-1.amazonaws.com/uploads/23e4d69a-f12e-403c-aff9-187c80841720.png

### Item #2
- **Image ID:** d87fbfda-c1a3-47a1-a098-041a0c1ffda0
- **Timestamp:** 2025-10-15T15:45:52.306298
- **Caption:** Current mood: a table with different types of font and numbers and loving it! 😍 #Mood #InstaDaily #Life #Happy #Blessed
- **Image URL:** https://image-caption-bucket-karthik.s3.eu-north-1.amazonaws.com/uploads/23e4d69a-f12e-403c-aff9-187c80841720.png

---

## **Quick Commands** 🚀

```powershell
# Check DynamoDB in terminal
C:/Python313/python.exe check_dynamodb.py

# View gallery app
C:/Python313/python.exe -m streamlit run view_captions.py

# Run main app
C:/Python313/python.exe -m streamlit run app.py

# List all S3 images
& "C:\Program Files\Amazon\AWSCLIV2\aws.exe" s3 ls s3://image-caption-bucket-karthik/uploads/
```

---

## **Files Created** 📁

| File | Purpose |
|------|---------|
| `check_dynamodb.py` | Terminal viewer for DynamoDB |
| `view_captions.py` | Streamlit gallery app |
| `app.py` | Main caption generator app |

---

**Recommended: Use the Streamlit gallery app** (`view_captions.py`) for the best viewing experience! 🎨
