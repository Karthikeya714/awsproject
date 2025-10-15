"""Caption service with provider management and fallback logic."""
import io
from typing import Tuple, List, Optional
from PIL import Image
import boto3
from botocore.exceptions import ClientError
from backend.config import config_manager
from backend.models import CaptionProvider as ProviderEnum
from backend.bedrock_provider import BedrockProvider
from backend.sagemaker_provider import SageMakerProvider
from backend.hf_provider import HuggingFaceProvider


class CaptionService:
    """Service for generating captions with provider fallback."""
    
    def __init__(self):
        self.config = config_manager.config
        self.rekognition_client = None
        
        # Initialize providers
        self.providers = {
            ProviderEnum.BEDROCK: BedrockProvider(),
            ProviderEnum.SAGEMAKER: SageMakerProvider(),
            ProviderEnum.HUGGINGFACE: HuggingFaceProvider()
        }
    
    def _get_rekognition_client(self):
        """Lazy initialization of Rekognition client."""
        if not self.rekognition_client:
            self.rekognition_client = boto3.client(
                'rekognition',
                region_name=self.config.aws_region
            )
        return self.rekognition_client
    
    def detect_labels(self, image_bytes: bytes) -> List[str]:
        """
        Detect labels in image using AWS Rekognition.
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            List of detected labels
        """
        if not self.config.use_rekognition:
            return []
        
        try:
            client = self._get_rekognition_client()
            response = client.detect_labels(
                Image={'Bytes': image_bytes},
                MaxLabels=10,
                MinConfidence=70
            )
            
            labels = [label['Name'] for label in response['Labels']]
            return labels
        except ClientError as e:
            print(f"Error detecting labels: {e}")
            return []
    
    def generate_caption(
        self,
        image: Image.Image,
        image_bytes: Optional[bytes] = None
    ) -> Tuple[str, str, Optional[List[str]], str]:
        """
        Generate captions for an image with provider fallback.
        
        Args:
            image: PIL Image object
            image_bytes: Optional image bytes for Rekognition
            
        Returns:
            Tuple of (concise_caption, creative_caption, labels, provider_used)
        """
        # Detect labels if enabled
        labels = []
        if image_bytes and self.config.use_rekognition:
            labels = self.detect_labels(image_bytes)
        
        # Try primary provider
        primary_provider = self.config.caption_provider
        
        # Define fallback order
        fallback_order = [
            primary_provider,
            ProviderEnum.BEDROCK,
            ProviderEnum.SAGEMAKER,
            ProviderEnum.HUGGINGFACE
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        fallback_order = [x for x in fallback_order if not (x in seen or seen.add(x))]
        
        last_error = None
        
        for provider_enum in fallback_order:
            provider = self.providers[provider_enum]
            
            if not provider.is_available():
                continue
            
            try:
                concise, creative = provider.generate_caption(image, labels)
                return concise, creative, labels, provider_enum.value
            except Exception as e:
                print(f"Provider {provider_enum.value} failed: {e}")
                last_error = e
                continue
        
        # All providers failed
        raise Exception(f"All caption providers failed. Last error: {last_error}")
    
    def preprocess_image(self, image: Image.Image, max_size: int = 2048) -> Image.Image:
        """
        Preprocess image for caption generation.
        
        Args:
            image: PIL Image object
            max_size: Maximum dimension size
            
        Returns:
            Preprocessed image
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too large
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        return image
