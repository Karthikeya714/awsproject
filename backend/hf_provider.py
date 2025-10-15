"""Hugging Face Inference API caption provider."""
import io
import base64
import requests
from typing import Tuple, List, Optional
from PIL import Image
from backend.caption_base import CaptionProvider
from backend.config import config_manager


class HuggingFaceProvider(CaptionProvider):
    """Hugging Face Inference API caption generation provider."""
    
    def __init__(self):
        self.config = config_manager.config
        self.api_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
        self.headers = {}
        if self.config.hf_api_key:
            self.headers["Authorization"] = f"Bearer {self.config.hf_api_key}"
    
    def is_available(self) -> bool:
        """Check if HF API is available."""
        return bool(self.config.hf_api_key)
    
    def generate_caption(
        self,
        image: Image.Image,
        labels: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """
        Generate captions using Hugging Face Inference API.
        
        Args:
            image: PIL Image object
            labels: Optional list of labels from Rekognition
            
        Returns:
            Tuple of (concise_caption, creative_caption)
        """
        # Convert image to bytes
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        
        try:
            # Call BLIP model for base caption
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=image_bytes,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                base_caption = result[0].get('generated_text', '')
            elif isinstance(result, dict):
                base_caption = result.get('generated_text', result.get('caption', ''))
            else:
                base_caption = str(result)
            
            # Generate creative variant
            concise = self._make_concise(base_caption)
            creative = self._make_creative(base_caption, labels)
            
            return concise, creative
            
        except requests.RequestException as e:
            print(f"Error calling Hugging Face API: {e}")
            raise Exception(f"Hugging Face API error: {str(e)}")
    
    def _make_concise(self, caption: str) -> str:
        """Make caption concise (max 10 words)."""
        words = caption.split()
        if len(words) <= 10:
            return caption
        return ' '.join(words[:10])
    
    def _make_creative(self, base_caption: str, labels: Optional[List[str]] = None) -> str:
        """Create a creative caption from base caption and labels."""
        creative = base_caption
        
        if labels and len(labels) > 0:
            # Enhance with labels
            label_context = ", ".join(labels[:3])
            creative = f"{base_caption}. The scene includes {label_context}."
        
        return creative[:200]
