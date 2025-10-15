"""Unit tests for backend modules."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io

from backend.models import AppConfig, CaptionProvider, CaptionResult
from backend.s3_manager import S3Manager
from backend.db import DynamoDBManager
from backend.caption_service import CaptionService
from backend.rate_limiter import RateLimiter, RateLimitConfig


class TestS3Manager:
    """Test S3Manager functionality."""
    
    @patch('backend.s3_manager.boto3.client')
    def test_upload_image(self, mock_boto):
        """Test image upload to S3."""
        # Setup
        mock_s3 = Mock()
        mock_boto.return_value = mock_s3
        
        manager = S3Manager()
        
        # Create test image
        img = Image.new('RGB', (100, 100), color='red')
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        image_data = buf.getvalue()
        
        # Test
        result = manager.upload_image(
            user_id='test_user',
            file_data=image_data,
            filename='test.jpg',
            content_type='image/jpeg'
        )
        
        # Assert
        assert result.user_id == 'test_user'
        assert result.original_filename == 'test.jpg'
        assert 's3://' in result.s3_url
        assert mock_s3.put_object.called
    
    @patch('backend.s3_manager.boto3.client')
    def test_get_presigned_url(self, mock_boto):
        """Test presigned URL generation."""
        mock_s3 = Mock()
        mock_s3.generate_presigned_url.return_value = 'https://test-url.com'
        mock_boto.return_value = mock_s3
        
        manager = S3Manager()
        
        url = manager.get_presigned_url('s3://bucket/key')
        
        assert url == 'https://test-url.com'
        assert mock_s3.generate_presigned_url.called


class TestDynamoDBManager:
    """Test DynamoDB operations."""
    
    @patch('backend.db.boto3.resource')
    def test_save_caption(self, mock_boto):
        """Test saving caption to DynamoDB."""
        mock_table = Mock()
        mock_dynamodb = Mock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto.return_value = mock_dynamodb
        
        db = DynamoDBManager()
        
        caption_result = CaptionResult(
            image_id='img123',
            user_id='user123',
            concise_caption='A cat',
            creative_caption='A cute cat sitting on a mat',
            labels=['cat', 'animal'],
            model='test-model',
            provider=CaptionProvider.BEDROCK,
            s3_url='s3://bucket/image',
            thumbnail_url='s3://bucket/thumb'
        )
        
        result = db.save_caption(caption_result)
        
        assert result == True
        assert mock_table.put_item.called


class TestRateLimiter:
    """Test rate limiter."""
    
    def test_rate_limit_allowed(self):
        """Test rate limiting allows requests."""
        config = RateLimitConfig(requests_per_hour=60, bucket_size=60)
        limiter = RateLimiter(config)
        
        # First request should be allowed
        assert limiter.is_allowed('user1') == True
        
        # Multiple requests should be allowed
        for _ in range(10):
            assert limiter.is_allowed('user1') == True
    
    def test_rate_limit_exceeded(self):
        """Test rate limiting blocks excess requests."""
        config = RateLimitConfig(requests_per_hour=5, bucket_size=5)
        limiter = RateLimiter(config)
        
        # Use up all tokens
        for _ in range(5):
            assert limiter.is_allowed('user1') == True
        
        # Next request should be blocked
        assert limiter.is_allowed('user1') == False


class TestCaptionService:
    """Test caption service."""
    
    @patch('backend.caption_service.boto3.client')
    def test_detect_labels(self, mock_boto):
        """Test Rekognition label detection."""
        mock_rekognition = Mock()
        mock_rekognition.detect_labels.return_value = {
            'Labels': [
                {'Name': 'Cat', 'Confidence': 99.5},
                {'Name': 'Animal', 'Confidence': 99.0}
            ]
        }
        mock_boto.return_value = mock_rekognition
        
        service = CaptionService()
        
        labels = service.detect_labels(b'image_data')
        
        assert 'Cat' in labels
        assert 'Animal' in labels
    
    def test_preprocess_image(self):
        """Test image preprocessing."""
        service = CaptionService()
        
        # Create large image
        img = Image.new('RGB', (3000, 3000), color='blue')
        
        processed = service.preprocess_image(img, max_size=2048)
        
        assert max(processed.size) <= 2048
        assert processed.mode == 'RGB'


@pytest.fixture
def mock_config():
    """Mock configuration."""
    return AppConfig(
        aws_region='us-east-1',
        s3_bucket='test-bucket',
        dynamodb_table='test-table',
        cognito_user_pool_id='test-pool',
        cognito_client_id='test-client',
        caption_provider=CaptionProvider.BEDROCK
    )
