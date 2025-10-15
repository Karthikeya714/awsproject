"""Data models for the application."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class CaptionProvider(str, Enum):
    """Supported caption providers."""
    BEDROCK = "bedrock"
    SAGEMAKER = "sagemaker"
    HUGGINGFACE = "hf"


class CaptionVariant(BaseModel):
    """A single caption variant."""
    text: str
    variant_type: str  # "concise" or "creative"
    confidence: Optional[float] = None


class ImageMetadata(BaseModel):
    """Metadata for an uploaded image."""
    user_id: str
    image_id: str
    s3_url: str
    thumbnail_url: str
    original_filename: str
    file_size: int
    content_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    

class CaptionResult(BaseModel):
    """Result of caption generation."""
    image_id: str
    user_id: str
    concise_caption: str
    creative_caption: str
    labels: Optional[List[str]] = None
    model: str
    provider: CaptionProvider
    confidence: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    s3_url: str
    thumbnail_url: str


class UserHistory(BaseModel):
    """User's caption history item."""
    image_id: str
    user_id: str
    concise_caption: str
    creative_caption: str
    thumbnail_url: str
    timestamp: datetime
    labels: Optional[List[str]] = None


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    requests_per_hour: int = 60
    bucket_size: int = 60
    refill_rate: float = 1.0  # tokens per second


class AppConfig(BaseModel):
    """Application configuration."""
    aws_region: str
    s3_bucket: str
    dynamodb_table: str
    cognito_user_pool_id: str
    cognito_client_id: str
    caption_provider: CaptionProvider = CaptionProvider.BEDROCK
    bedrock_model_id: Optional[str] = "anthropic.claude-3-sonnet-20240229-v1:0"
    sagemaker_endpoint: Optional[str] = None
    hf_api_key: Optional[str] = None
    secrets_manager_arn: Optional[str] = None
    use_rekognition: bool = True
    max_image_size_mb: int = 10
    thumbnail_size: int = 300
    presigned_url_expiry: int = 3600  # seconds
    retention_days: int = 90
    
    @validator("caption_provider", pre=True)
    def validate_provider(cls, v):
        """Validate caption provider."""
        if isinstance(v, str):
            return CaptionProvider(v.lower())
        return v


class UsageMetrics(BaseModel):
    """Usage metrics for admin dashboard."""
    total_uploads: int
    total_users: int
    captions_generated: int
    avg_processing_time: float
    error_rate: float
    storage_used_gb: float
