"""Integration tests using moto for AWS service mocking."""
import pytest
import boto3
from moto import mock_s3, mock_dynamodb, mock_cognitoidp
from PIL import Image
import io
import os

from backend.s3_manager import S3Manager
from backend.db import DynamoDBManager
from backend.models import CaptionResult, CaptionProvider


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_REGION'] = 'us-east-1'


@mock_s3
class TestS3Integration:
    """Integration tests for S3 operations."""
    
    def test_upload_and_download(self, aws_credentials):
        """Test full upload and download cycle."""
        # Setup
        s3_client = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'test-bucket'
        s3_client.create_bucket(Bucket=bucket_name)
        
        os.environ['S3_BUCKET'] = bucket_name
        
        manager = S3Manager()
        
        # Create test image
        img = Image.new('RGB', (200, 200), color='green')
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        image_data = buf.getvalue()
        
        # Upload
        metadata = manager.upload_image(
            user_id='test_user',
            file_data=image_data,
            filename='test.jpg',
            content_type='image/jpeg'
        )
        
        # Verify
        assert metadata.user_id == 'test_user'
        assert metadata.image_id is not None
        
        # Check S3
        objects = s3_client.list_objects_v2(Bucket=bucket_name)
        assert objects['KeyCount'] >= 2  # Original + thumbnail


@mock_dynamodb
class TestDynamoDBIntegration:
    """Integration tests for DynamoDB operations."""
    
    def test_save_and_retrieve_caption(self, aws_credentials):
        """Test saving and retrieving caption."""
        # Setup
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table_name = 'test-captions'
        
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'GSI1',
                    'KeySchema': [
                        {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                        {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        os.environ['DYNAMODB_TABLE'] = table_name
        
        db = DynamoDBManager()
        
        # Create caption
        caption = CaptionResult(
            image_id='img123',
            user_id='user123',
            concise_caption='A dog',
            creative_caption='A happy dog playing in the park',
            labels=['dog', 'park', 'animal'],
            model='test-model',
            provider=CaptionProvider.BEDROCK,
            s3_url='s3://bucket/image',
            thumbnail_url='s3://bucket/thumb'
        )
        
        # Save
        result = db.save_caption(caption)
        assert result == True
        
        # Retrieve history
        history, next_key = db.get_user_history('user123')
        assert len(history) == 1
        assert history[0].concise_caption == 'A dog'
    
    def test_delete_user_data(self, aws_credentials):
        """Test deleting user data."""
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table_name = 'test-captions'
        
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        os.environ['DYNAMODB_TABLE'] = table_name
        
        db = DynamoDBManager()
        
        # Add some data
        caption = CaptionResult(
            image_id='img456',
            user_id='user456',
            concise_caption='A cat',
            creative_caption='A sleepy cat',
            labels=['cat'],
            model='test-model',
            provider=CaptionProvider.BEDROCK,
            s3_url='s3://bucket/image',
            thumbnail_url='s3://bucket/thumb'
        )
        db.save_caption(caption)
        
        # Delete
        deleted = db.delete_user_data('user456')
        assert deleted > 0
        
        # Verify deletion
        history, _ = db.get_user_history('user456')
        assert len(history) == 0
