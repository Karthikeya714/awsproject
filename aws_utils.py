"""Simple AWS utilities for S3 and DynamoDB integration."""
import boto3
import uuid
from datetime import datetime
from botocore.exceptions import ClientError

# Try to use Streamlit secrets if available (for Streamlit Cloud deployment)
try:
    import streamlit as st
    
    # Check if running on Streamlit Cloud with secrets
    if hasattr(st, 'secrets') and len(st.secrets) > 0:
        aws_config = {
            'region_name': st.secrets.get('AWS_DEFAULT_REGION', 'eu-north-1'),
            'aws_access_key_id': st.secrets.get('AWS_ACCESS_KEY_ID'),
            'aws_secret_access_key': st.secrets.get('AWS_SECRET_ACCESS_KEY')
        }
        # Remove None values
        aws_config = {k: v for k, v in aws_config.items() if v is not None}
        
        s3_client = boto3.client('s3', **aws_config)
        dynamodb = boto3.resource('dynamodb', **aws_config)
    else:
        # Use default credentials (from aws configure)
        s3_client = boto3.client('s3', region_name='eu-north-1')
        dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
except (ImportError, Exception):
    # Fallback to default credentials (from aws configure)
    s3_client = boto3.client('s3', region_name='eu-north-1')
    dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')


def upload_image_to_s3(file_obj, bucket_name, folder="uploads"):
    """
    Upload file to S3 and make it publicly readable.
    
    Args:
        file_obj: File object from Streamlit uploader
        bucket_name: Name of S3 bucket
        folder: Folder prefix in S3 (default: "uploads")
    
    Returns:
        str: Public S3 URL of uploaded image
    """
    try:
        # Generate unique filename
        file_extension = file_obj.name.split('.')[-1]
        unique_filename = f"{folder}/{uuid.uuid4()}.{file_extension}"
        
        # Upload to S3 (without ACL - bucket policy handles public access)
        s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            unique_filename,
            ExtraArgs={
                'ContentType': file_obj.type
            }
        )
        
        # Generate public URL
        s3_url = f"https://{bucket_name}.s3.eu-north-1.amazonaws.com/{unique_filename}"
        
        return s3_url
    
    except ClientError as e:
        raise Exception(f"Failed to upload to S3: {str(e)}")


def save_caption_to_dynamodb(image_id, caption, image_url, table_name='image_captions'):
    """
    Save image caption metadata to DynamoDB.
    
    Args:
        image_id: Unique identifier for the image
        caption: Generated caption text
        image_url: S3 URL of the image
        table_name: DynamoDB table name (default: 'image_captions')
    """
    try:
        table = dynamodb.Table(table_name)
        
        # Create item
        item = {
            'image_id': image_id,
            'timestamp': datetime.utcnow().isoformat(),
            'caption_text': caption,
            'image_url': image_url
        }
        
        # Put item to DynamoDB
        table.put_item(Item=item)
        
        return True
    
    except ClientError as e:
        raise Exception(f"Failed to save to DynamoDB: {str(e)}")


def get_all_captions(table_name='image_captions', limit=50):
    """
    Retrieve all captions from DynamoDB.
    
    Args:
        table_name: DynamoDB table name
        limit: Maximum number of items to retrieve
    
    Returns:
        list: List of caption items
    """
    try:
        table = dynamodb.Table(table_name)
        response = table.scan(Limit=limit)
        
        # Sort by timestamp (newest first)
        items = response.get('Items', [])
        items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return items
    
    except ClientError as e:
        raise Exception(f"Failed to retrieve from DynamoDB: {str(e)}")


def create_dynamodb_table_if_not_exists(table_name='image_captions'):
    """
    Create DynamoDB table if it doesn't exist.
    
    Args:
        table_name: Name of the table to create
    """
    try:
        dynamodb_client = boto3.client('dynamodb', region_name='eu-north-1')
        
        # Check if table exists
        existing_tables = dynamodb_client.list_tables()['TableNames']
        
        if table_name in existing_tables:
            print(f"✅ Table '{table_name}' already exists")
            return
        
        # Create table
        dynamodb_client.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'image_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'image_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand pricing
        )
        
        print(f"✅ Created DynamoDB table '{table_name}'")
        
        # Wait for table to be created
        waiter = dynamodb_client.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"✅ Table '{table_name}' already exists")
        else:
            raise Exception(f"Failed to create table: {str(e)}")
