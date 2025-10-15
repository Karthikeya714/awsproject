"""View DynamoDB items in a readable format."""
import boto3
from datetime import datetime
import json

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
table = dynamodb.Table('image_captions')

# Scan all items
response = table.scan()
items = response.get('Items', [])

print("=" * 80)
print(f"📊 DynamoDB Table: image_captions")
print(f"🌍 Region: eu-north-1")
print(f"📝 Total Items: {len(items)}")
print("=" * 80)
print()

if len(items) == 0:
    print("⚠️  No items found in the table.")
    print()
    print("💡 To add items:")
    print("   1. Run the Streamlit app")
    print("   2. Upload an image")
    print("   3. Generate a caption")
    print("   4. Click 'Upload to S3'")
    print("   5. Click 'Save to DynamoDB'")
else:
    # Sort by timestamp (newest first)
    items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    for i, item in enumerate(items, 1):
        print(f"📄 Item #{i}")
        print("-" * 80)
        print(f"🆔 Image ID:    {item.get('image_id', 'N/A')}")
        print(f"📅 Timestamp:   {item.get('timestamp', 'N/A')}")
        print(f"💬 Caption:     {item.get('caption_text', 'N/A')}")
        print(f"🔗 Image URL:   {item.get('image_url', 'N/A')}")
        print()

print("=" * 80)
print()
print("🌐 View in AWS Console:")
print("   https://eu-north-1.console.aws.amazon.com/dynamodbv2/home?region=eu-north-1#item-explorer?table=image_captions")
print()
print("💻 View with AWS CLI:")
print('   aws dynamodb scan --table-name image_captions --region eu-north-1')
print()
