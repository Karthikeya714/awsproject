"""AWS utilities configured for LocalStack (local AWS simulation)."""
import boto3
import uuid
from datetime import datetime
from botocore.exceptions import ClientError


# Configure for LocalStack (local AWS simulation)
LOCALSTACK_ENDPOINT = "http://localhost:4566"

# Initialize AWS clients for LocalStack
s3_client = boto3.client(
    's3',
    endpoint_url=LOCALSTACK_ENDPOINT,
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='eu-north-1'
)

dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url=LOCALSTACK_ENDPOINT,
    aws_access_key_id='test',
    aws_secret_access_key='test',
    region_name='eu-north-1'
)


def upload_image_to_s3(file_obj, bucket_name, folder="uploads"):
    """
    Upload file to S3 (LocalStack) and make it publicly readable.
    
    Args:
        file_obj: File object from Streamlit uploader
        bucket_name: Name of S3 bucket
        folder: Folder prefix in S3 (default: "uploads")
    
    Returns:
        str: Public S3 URL of uploaded image
    """
    try:
        # Ensure bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except ClientError:
            # Create bucket if it doesn't exist
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': 'eu-north-1'}
            )
            print(f"✅ Created bucket: {bucket_name}")
        
        # Generate unique filename
        file_extension = file_obj.name.split('.')[-1]
        unique_filename = f"{folder}/{uuid.uuid4()}.{file_extension}"
        
        # Upload to S3
        s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            unique_filename,
            ExtraArgs={
                'ContentType': file_obj.type
            }
        )
        
        # Generate public URL (LocalStack format)
        s3_url = f"{LOCALSTACK_ENDPOINT}/{bucket_name}/{unique_filename}"
        
        return s3_url
    
    except ClientError as e:
        raise Exception(f"Failed to upload to S3: {str(e)}")


def save_caption_to_dynamodb(image_id, caption, image_url, table_name='image_captions'):
    """
    Save image caption metadata to DynamoDB (LocalStack).
    
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
    Create DynamoDB table if it doesn't exist (LocalStack).
    
    Args:
        table_name: Name of the table to create
    """
    try:
        dynamodb_client = boto3.client(
            'dynamodb',
            endpoint_url=LOCALSTACK_ENDPOINT,
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='eu-north-1'
        )
        
        # Check if table exists
        try:
            dynamodb_client.describe_table(TableName=table_name)
            print(f"✅ Table '{table_name}' already exists")
            return
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
        
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
            BillingMode='PAY_PER_REQUEST'
        )
        
        print(f"✅ Created DynamoDB table '{table_name}'")
        
    except ClientError as e:
        if 'ResourceInUseException' in str(e):
            print(f"✅ Table '{table_name}' already exists")
        else:
            raise Exception(f"Failed to create table: {str(e)}")
