"""Configuration management using environment variables and AWS Secrets Manager."""
import os
import json
import boto3
from typing import Optional, Dict, Any
from backend.models import AppConfig, CaptionProvider


class ConfigManager:
    """Manages application configuration from environment and Secrets Manager."""
    
    def __init__(self):
        self.secrets_client = None
        self._config: Optional[AppConfig] = None
        
    def load_config(self) -> AppConfig:
        """Load configuration from environment variables and Secrets Manager."""
        if self._config:
            return self._config
            
        # Load from environment first
        config_dict = {
            "aws_region": os.getenv("AWS_REGION", "us-east-1"),
            "s3_bucket": os.getenv("S3_BUCKET", ""),
            "dynamodb_table": os.getenv("DYNAMODB_TABLE", "image_captions"),
            "cognito_user_pool_id": os.getenv("COGNITO_USER_POOL_ID", ""),
            "cognito_client_id": os.getenv("COGNITO_CLIENT_ID", ""),
            "caption_provider": os.getenv("CAPTION_PROVIDER", "bedrock"),
            "bedrock_model_id": os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"),
            "sagemaker_endpoint": os.getenv("SAGEMAKER_ENDPOINT"),
            "hf_api_key": os.getenv("HF_API_KEY"),
            "secrets_manager_arn": os.getenv("SECRETS_MANAGER_ARN"),
            "use_rekognition": os.getenv("USE_REKOGNITION", "true").lower() == "true",
            "max_image_size_mb": int(os.getenv("MAX_IMAGE_SIZE_MB", "10")),
            "thumbnail_size": int(os.getenv("THUMBNAIL_SIZE", "300")),
            "presigned_url_expiry": int(os.getenv("PRESIGNED_URL_EXPIRY", "3600")),
            "retention_days": int(os.getenv("RETENTION_DAYS", "90")),
        }
        
        # Load secrets from AWS Secrets Manager if ARN is provided
        if config_dict["secrets_manager_arn"]:
            secrets = self._load_secrets(
                config_dict["secrets_manager_arn"],
                config_dict["aws_region"]
            )
            # Override with secrets
            config_dict.update(secrets)
        
        self._config = AppConfig(**config_dict)
        return self._config
    
    def _load_secrets(self, secret_arn: str, region: str) -> Dict[str, Any]:
        """Load secrets from AWS Secrets Manager."""
        if not self.secrets_client:
            self.secrets_client = boto3.client('secretsmanager', region_name=region)
        
        try:
            response = self.secrets_client.get_secret_value(SecretId=secret_arn)
            secret_string = response.get('SecretString')
            if secret_string:
                return json.loads(secret_string)
            return {}
        except Exception as e:
            print(f"Warning: Could not load secrets from Secrets Manager: {e}")
            return {}
    
    @property
    def config(self) -> AppConfig:
        """Get current configuration."""
        if not self._config:
            return self.load_config()
        return self._config


# Global config manager instance
config_manager = ConfigManager()
