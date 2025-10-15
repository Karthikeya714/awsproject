"""Amazon Bedrock caption provider."""
import io
import json
import base64
from typing import Tuple, List, Optional
from PIL import Image
import boto3
from botocore.exceptions import ClientError
from backend.caption_base import CaptionProvider
from backend.config import config_manager


class BedrockProvider(CaptionProvider):
    """Amazon Bedrock caption generation provider."""
    
    def __init__(self):
        self.config = config_manager.config
        self.client = None
        
    def _get_client(self):
        """Lazy initialization of Bedrock client."""
        if not self.client:
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=self.config.aws_region
            )
        return self.client
    
    def is_available(self) -> bool:
        """Check if Bedrock is available."""
        try:
            client = self._get_client()
            # Simple check - in production you'd verify model access
            return bool(self.config.bedrock_model_id)
        except Exception as e:
            print(f"Bedrock not available: {e}")
            return False
    
    def generate_caption(
        self,
        image: Image.Image,
        labels: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """
        Generate captions using Amazon Bedrock.
        
        Args:
            image: PIL Image object
            labels: Optional list of labels from Rekognition
            
        Returns:
            Tuple of (concise_caption, creative_caption)
        """
        client = self._get_client()
        
        # Convert image to base64
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Build prompt
        prompt = self._build_prompt(labels)
        
        # Prepare request based on model type
        model_id = self.config.bedrock_model_id
        
        if 'claude' in model_id.lower():
            # Claude 3 format
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
        else:
            # Generic format
            body = {
                "prompt": prompt,
                "max_tokens": 300,
                "temperature": 0.7
            }
        
        try:
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            
            # Parse response based on model type
            if 'claude' in model_id.lower():
                response_text = response_body['content'][0]['text']
            else:
                response_text = response_body.get('completion', response_body.get('generated_text', ''))
            
            return self._parse_response(response_text)
            
        except ClientError as e:
            print(f"Error calling Bedrock: {e}")
            raise Exception(f"Bedrock API error: {str(e)}")
