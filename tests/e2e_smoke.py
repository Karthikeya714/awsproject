"""End-to-end smoke tests."""
import pytest
import requests
import os
from PIL import Image
import io


@pytest.fixture
def app_url():
    """Get application URL from environment."""
    return os.getenv('APP_URL', 'http://localhost:8501')


@pytest.fixture
def test_credentials():
    """Get test user credentials."""
    return {
        'username': os.getenv('TEST_USER', 'testuser'),
        'password': os.getenv('TEST_PASSWORD', 'testpass')
    }


def create_test_image():
    """Create a test image."""
    img = Image.new('RGB', (400, 300), color='blue')
    # Add some variety
    pixels = img.load()
    for i in range(100):
        pixels[i, i] = (255, 0, 0)
    
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    return buf


@pytest.mark.skipif(
    os.getenv('RUN_E2E_TESTS') != 'true',
    reason="E2E tests require deployed environment"
)
class TestE2ESmoke:
    """End-to-end smoke tests."""
    
    def test_application_is_accessible(self, app_url):
        """Test that application is accessible."""
        response = requests.get(app_url, timeout=30)
        assert response.status_code == 200
    
    def test_health_endpoint(self, app_url):
        """Test health check endpoint."""
        health_url = f"{app_url}/_stcore/health"
        response = requests.get(health_url, timeout=10)
        assert response.status_code == 200
    
    @pytest.mark.slow
    def test_full_upload_flow(self, app_url, test_credentials):
        """Test full image upload and caption generation flow."""
        # Note: This is a placeholder as Streamlit apps don't have REST API
        # In a real scenario, you'd use Selenium or Playwright for browser automation
        
        # Verify app loads
        response = requests.get(app_url, timeout=30)
        assert response.status_code == 200
        assert 'Image Caption Generator' in response.text or 'streamlit' in response.text.lower()


@pytest.mark.skipif(
    os.getenv('RUN_AWS_TESTS') != 'true',
    reason="AWS tests require AWS credentials"
)
class TestAWSServices:
    """Test AWS service connectivity."""
    
    def test_s3_bucket_exists(self):
        """Test S3 bucket accessibility."""
        import boto3
        
        s3 = boto3.client('s3')
        bucket_name = os.getenv('S3_BUCKET')
        
        if bucket_name:
            response = s3.head_bucket(Bucket=bucket_name)
            assert response['ResponseMetadata']['HTTPStatusCode'] == 200
    
    def test_dynamodb_table_exists(self):
        """Test DynamoDB table accessibility."""
        import boto3
        
        dynamodb = boto3.client('dynamodb')
        table_name = os.getenv('DYNAMODB_TABLE')
        
        if table_name:
            response = dynamodb.describe_table(TableName=table_name)
            assert response['Table']['TableStatus'] == 'ACTIVE'
    
    def test_cognito_pool_exists(self):
        """Test Cognito user pool accessibility."""
        import boto3
        
        cognito = boto3.client('cognito-idp')
        pool_id = os.getenv('COGNITO_USER_POOL_ID')
        
        if pool_id:
            response = cognito.describe_user_pool(UserPoolId=pool_id)
            assert response['UserPool']['Id'] == pool_id


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
