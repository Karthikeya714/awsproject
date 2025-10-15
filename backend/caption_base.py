"""Abstract base class for caption providers."""
from abc import ABC, abstractmethod
from typing import Tuple, List, Optional
from PIL import Image


class CaptionProvider(ABC):
    """Abstract base class for caption generation providers."""
    
    @abstractmethod
    def generate_caption(
        self,
        image: Image.Image,
        labels: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """
        Generate captions for an image.
        
        Args:
            image: PIL Image object
            labels: Optional list of labels from Rekognition
            
        Returns:
            Tuple of (concise_caption, creative_caption)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured."""
        pass
    
    def _build_prompt(self, labels: Optional[List[str]] = None) -> str:
        """
        Build prompt for caption generation.
        
        Args:
            labels: Optional list of detected labels
            
        Returns:
            Prompt string
        """
        base_prompt = """Generate two image captions:
1. A concise caption (maximum 10 words) that describes the main subject
2. A creative caption (1-2 sentences) that tells a story or adds context

"""
        if labels:
            base_prompt += f"Detected objects/scenes: {', '.join(labels[:5])}\n\n"
        
        base_prompt += """Format your response as:
CONCISE: [your concise caption here]
CREATIVE: [your creative caption here]"""
        
        return base_prompt
    
    def _parse_response(self, response_text: str) -> Tuple[str, str]:
        """
        Parse response into concise and creative captions.
        
        Args:
            response_text: Raw response from model
            
        Returns:
            Tuple of (concise_caption, creative_caption)
        """
        concise = ""
        creative = ""
        
        lines = response_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.upper().startswith('CONCISE:'):
                concise = line.split(':', 1)[1].strip()
            elif line.upper().startswith('CREATIVE:'):
                creative = line.split(':', 1)[1].strip()
        
        # Fallback if parsing failed
        if not concise or not creative:
            parts = response_text.strip().split('\n', 1)
            concise = parts[0][:80] if parts else "An image"
            creative = parts[1][:200] if len(parts) > 1 else response_text[:200]
        
        return concise, creative
