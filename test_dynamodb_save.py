"""Test script to verify DynamoDB saving works"""
import boto3
import uuid
from datetime import datetime
from aws_utils import save_caption_to_dynamodb

# Test 1: Check current items
print("=" * 60)
print("TEST 1: Checking current DynamoDB items")
print("=" * 60)

dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
table = dynamodb.Table('image_captions')
response = table.scan()
items = response.get('Items', [])

print(f"✅ Found {len(items)} items in DynamoDB")
for i, item in enumerate(items, 1):
    print(f"\nItem {i}:")
    print(f"  ID: {item.get('image_id')}")
    print(f"  Time: {item.get('timestamp')}")
    print(f"  Caption: {item.get('caption_text', '')[:50]}...")

# Test 2: Try saving a new item
print("\n" + "=" * 60)
print("TEST 2: Attempting to save a test item")
print("=" * 60)

test_id = str(uuid.uuid4())
test_caption = "Test caption for verification"
test_url = "https://test-bucket.s3.amazonaws.com/test.jpg"

try:
    save_caption_to_dynamodb(
        image_id=test_id,
        caption=test_caption,
        image_url=test_url,
        table_name='image_captions'
    )
    print("✅ Successfully saved test item to DynamoDB!")
    print(f"   Test ID: {test_id}")
    
    # Verify it was saved
    response = table.get_item(Key={'image_id': test_id})
    if 'Item' in response:
        print("✅ Verified: Item exists in DynamoDB!")
        print(f"   Caption: {response['Item']['caption_text']}")
    else:
        print("❌ ERROR: Item not found after saving!")
        
except Exception as e:
    print(f"❌ ERROR saving to DynamoDB: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check total items again
print("\n" + "=" * 60)
print("TEST 3: Final count")
print("=" * 60)
response = table.scan()
items = response.get('Items', [])
print(f"✅ Total items now: {len(items)}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
