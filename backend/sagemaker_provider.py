"""Amazon SageMaker caption provider."""
import io
import json
from typing import Tuple, List, Optional
from PIL import Image
import boto3
from botocore.exceptions import ClientError
from backend.caption_base import CaptionProvider
from backend.config import config_manager


class SageMakerProvider(CaptionProvider):
    """Amazon SageMaker caption generation provider."""
    
    def __init__(self):
        self.config = config_manager.config
        self.client = None
        
    def _get_client(self):
        """Lazy initialization of SageMaker Runtime client."""
        if not self.client:
            self.client = boto3.client(
                'sagemaker-runtime',
                region_name=self.config.aws_region
            )
        return self.client
    
    def is_available(self) -> bool:
        """Check if SageMaker endpoint is available."""
        return bool(self.config.sagemaker_endpoint)
    
    def generate_caption(
        self,
        image: Image.Image,
        labels: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """
        Generate captions using Amazon SageMaker endpoint.
        
        Args:
            image: PIL Image object
            labels: Optional list of labels from Rekognition
            
        Returns:
            Tuple of (concise_caption, creative_caption)
        """
        client = self._get_client()
        
        # Convert image to bytes
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        # Build prompt
        prompt = self._build_prompt(labels)
        
        # Prepare payload for BLIP/ViT-GPT2 model
        payload = {
            "image": image_bytes.hex(),  # Send as hex string
            "prompt": prompt,
            "max_length": 150,
            "num_return_sequences": 2
        }
        
        try:
            response = client.invoke_endpoint(
                EndpointName=self.config.sagemaker_endpoint,
                ContentType='application/json',
                Body=json.dumps(payload)
            )
            
            result = json.loads(response['Body'].read().decode())
            
            # Parse results
            if isinstance(result, list) and len(result) >= 2:
                concise = result[0][:80]  # Limit to ~10 words
                creative = result[1][:200]
            elif isinstance(result, dict):
                generated_text = result.get('generated_text', result.get('caption', ''))
                concise, creative = self._parse_response(generated_text)
            else:
                generated_text = str(result)
                concise, creative = self._parse_response(generated_text)
            
            return concise, creative
            
        except ClientError as e:
            print(f"Error calling SageMaker: {e}")
            raise Exception(f"SageMaker API error: {str(e)}")
