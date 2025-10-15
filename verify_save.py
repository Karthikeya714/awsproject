"""
Quick verification script - Run this after saving in the app!
"""
import boto3
from datetime import datetime
from colorama import init, Fore, Style
import sys

# Initialize colorama for Windows
init()

def print_header(text):
    print("\n" + "=" * 70)
    print(f"{Fore.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}")
    print("=" * 70)

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.BLUE}ℹ️  {text}{Style.RESET_ALL}")

def print_warning(text):
    print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

try:
    print_header("🔍 CHECKING DYNAMODB STATUS")
    
    # Connect to DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
    table = dynamodb.Table('image_captions')
    
    print_info("Connecting to DynamoDB...")
    
    # Get all items
    response = table.scan()
    items = response.get('Items', [])
    
    if not items:
        print_warning("No items found in DynamoDB!")
        print_info("Steps to add items:")
        print("  1. Open the app: http://localhost:8501")
        print("  2. Upload an image")
        print("  3. Click: 'Upload to S3 & Save to DynamoDB'")
        print("  4. Run this script again!")
        sys.exit(0)
    
    # Sort by timestamp
    items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    print_success(f"Found {len(items)} item(s) in DynamoDB!")
    
    print_header("📊 YOUR SAVED CAPTIONS")
    
    for i, item in enumerate(items, 1):
        print(f"\n{Fore.MAGENTA}{'─' * 70}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📷 Item #{i}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'─' * 70}{Style.RESET_ALL}")
        
        # Extract data
        image_id = item.get('image_id', 'N/A')
        timestamp = item.get('timestamp', 'N/A')
        caption = item.get('caption_text', 'N/A')
        image_url = item.get('image_url', 'N/A')
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            time_str = timestamp
        
        print(f"🆔 ID:        {image_id[:30]}...")
        print(f"📅 Time:      {time_str}")
        print(f"💬 Caption:   {caption[:60]}...")
        print(f"🔗 S3 URL:    {image_url[:60]}...")
    
    # Find most recent
    print_header("⭐ MOST RECENT SAVE")
    latest = items[0]
    print(f"Saved: {Fore.GREEN}{latest.get('timestamp', 'Unknown')}{Style.RESET_ALL}")
    print(f"Caption: {Fore.CYAN}{latest.get('caption_text', '')[:80]}{Style.RESET_ALL}")
    
    print_header("✅ STATUS: ALL GOOD!")
    print_success("DynamoDB is working correctly!")
    print_info(f"Total items: {len(items)}")
    print_info("Ready to save more captions!")
    
    print("\n" + Fore.CYAN + "💡 TIP: To add more captions:" + Style.RESET_ALL)
    print("   1. Go to: http://localhost:8501")
    print("   2. Upload image → Generate caption")
    print("   3. Click: 'Upload to S3 & Save to DynamoDB'")
    print("   4. Look for 🎈 balloons!")
    print("\n")
    
except Exception as e:
    print_error(f"Error: {e}")
    print_info("Make sure:")
    print("  ✓ AWS credentials are configured (run: aws configure)")
    print("  ✓ DynamoDB table 'image_captions' exists")
    print("  ✓ You have internet connection")
    import traceback
    print(f"\n{Fore.RED}{traceback.format_exc()}{Style.RESET_ALL}")
