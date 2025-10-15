"""S3 storage management for images and thumbnails."""
import io
import uuid
from typing import Tuple, Optional
from datetime import timedelta
import boto3
from botocore.exceptions import ClientError
from PIL import Image, ExifTags
from backend.config import config_manager
from backend.models import ImageMetadata


class S3Manager:
    """Manages S3 operations for image storage."""
    
    def __init__(self):
        self.config = config_manager.config
        self.s3_client = boto3.client('s3', region_name=self.config.aws_region)
        
    def upload_image(
        self,
        user_id: str,
        file_data: bytes,
        filename: str,
        content_type: str,
        strip_exif: bool = True
    ) -> ImageMetadata:
        """
        Upload image to S3 and create thumbnail.
        
        Args:
            user_id: User ID
            file_data: Image file bytes
            filename: Original filename
            content_type: MIME type
            strip_exif: Whether to strip EXIF metadata
            
        Returns:
            ImageMetadata with S3 URLs
        """
        image_id = str(uuid.uuid4())
        
        # Load image
        image = Image.open(io.BytesIO(file_data))
        
        # Strip EXIF if requested
        if strip_exif:
            image = self._strip_exif(image)
        
        # Upload original image
        original_key = f"images/{user_id}/{image_id}/original.{self._get_extension(filename)}"
        original_buffer = io.BytesIO()
        image.save(original_buffer, format=image.format or 'JPEG')
        original_buffer.seek(0)
        
        self.s3_client.put_object(
            Bucket=self.config.s3_bucket,
            Key=original_key,
            Body=original_buffer.getvalue(),
            ContentType=content_type,
            ServerSideEncryption='AES256',
            Metadata={
                'user_id': user_id,
                'image_id': image_id,
                'original_filename': filename
            }
        )
        
        # Create and upload thumbnail
        thumbnail_key = f"images/{user_id}/{image_id}/thumbnail.jpg"
        thumbnail = self._create_thumbnail(image, self.config.thumbnail_size)
        thumbnail_buffer = io.BytesIO()
        thumbnail.save(thumbnail_buffer, format='JPEG', quality=85)
        thumbnail_buffer.seek(0)
        
        self.s3_client.put_object(
            Bucket=self.config.s3_bucket,
            Key=thumbnail_key,
            Body=thumbnail_buffer.getvalue(),
            ContentType='image/jpeg',
            ServerSideEncryption='AES256'
        )
        
        return ImageMetadata(
            user_id=user_id,
            image_id=image_id,
            s3_url=f"s3://{self.config.s3_bucket}/{original_key}",
            thumbnail_url=f"s3://{self.config.s3_bucket}/{thumbnail_key}",
            original_filename=filename,
            file_size=len(file_data),
            content_type=content_type
        )
    
    def get_presigned_url(self, s3_url: str, expiry: Optional[int] = None) -> str:
        """
        Generate presigned URL for S3 object.
        
        Args:
            s3_url: S3 URL (s3://bucket/key format)
            expiry: URL expiry in seconds (default from config)
            
        Returns:
            Presigned URL
        """
        if not s3_url.startswith('s3://'):
            return s3_url
            
        # Parse S3 URL
        parts = s3_url[5:].split('/', 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ''
        
        expiry_seconds = expiry or self.config.presigned_url_expiry
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiry_seconds
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return ""
    
    def delete_user_images(self, user_id: str) -> int:
        """
        Delete all images for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of objects deleted
        """
        prefix = f"images/{user_id}/"
        
        # List all objects for user
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.config.s3_bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return 0
            
            # Delete objects
            objects = [{'Key': obj['Key']} for obj in response['Contents']]
            
            if objects:
                self.s3_client.delete_objects(
                    Bucket=self.config.s3_bucket,
                    Delete={'Objects': objects}
                )
                
            return len(objects)
        except ClientError as e:
            print(f"Error deleting user images: {e}")
            return 0
    
    def _strip_exif(self, image: Image.Image) -> Image.Image:
        """Remove EXIF metadata from image."""
        # Create new image without EXIF
        data = list(image.getdata())
        image_without_exif = Image.new(image.mode, image.size)
        image_without_exif.putdata(data)
        return image_without_exif
    
    def _create_thumbnail(self, image: Image.Image, size: int) -> Image.Image:
        """Create thumbnail of specified size."""
        image.thumbnail((size, size), Image.Resampling.LANCZOS)
        return image
    
    def _get_extension(self, filename: str) -> str:
        """Extract file extension."""
        return filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
