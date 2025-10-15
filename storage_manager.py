import os
import io
import logging
from datetime import timedelta, datetime
from google.cloud import storage
from google.oauth2 import service_account
from PIL import Image
import uuid

class CloudStorageManager:
    """Secure Cloud Storage operations manager"""
    
    def __init__(self, service_account_path, bucket_name):
        self.bucket_name = bucket_name
        self.client = None
        self._initialize_client(service_account_path)
    
    def _initialize_client(self, service_account_path):
        """Initialize the Cloud Storage client with service account"""
        try:
            if not os.path.exists(service_account_path):
                raise FileNotFoundError(f"Service account file not found: {service_account_path}")
            
            credentials = service_account.Credentials.from_service_account_file(
                service_account_path,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            
            self.client = storage.Client(credentials=credentials)
            logging.info("Cloud Storage client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Cloud Storage client: {e}")
            raise
    
    def generate_signed_url(self, blob_name, method='GET', expiration_minutes=15, content_type=None):
        """Generate a signed URL for secure access to Cloud Storage objects"""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)
            
            # Set headers for upload URLs
            headers = {}
            if method == 'PUT' and content_type:
                headers['Content-Type'] = content_type
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method=method,
                headers=headers if headers else None
            )
            
            return {
                'url': url,
                'method': method,
                'expires_at': (datetime.utcnow() + timedelta(minutes=expiration_minutes)).isoformat(),
                'blob_name': blob_name
            }
        
        except Exception as e:
            logging.error(f"Error generating signed URL for {blob_name}: {e}")
            raise
    
    def generate_upload_url(self, user_id, original_filename, content_type='image/jpeg', expiration_minutes=30):
        """Generate signed URL for secure file upload"""
        # Create secure blob name
        blob_name = self._generate_secure_blob_name(user_id, original_filename)
        
        # Validate content type
        if not self._validate_content_type(content_type):
            raise ValueError(f"Invalid content type: {content_type}")
        
        return self.generate_signed_url(
            blob_name=blob_name,
            method='PUT',
            expiration_minutes=expiration_minutes,
            content_type=content_type
        )
    
    def generate_download_url(self, blob_name, user_id, expiration_minutes=15):
        """Generate signed URL for secure file download"""
        # Validate user access
        if not self._validate_user_access(blob_name, user_id):
            raise PermissionError(f"User {user_id} does not have access to {blob_name}")
        
        return self.generate_signed_url(
            blob_name=blob_name,
            method='GET',
            expiration_minutes=expiration_minutes
        )
    
    def list_user_files(self, user_id, limit=100):
        """List files belonging to a specific user"""
        try:
            bucket = self.client.bucket(self.bucket_name)
            prefix = f"uploads/{user_id}/"
            
            blobs = bucket.list_blobs(prefix=prefix, max_results=limit)
            
            files = []
            for blob in blobs:
                file_info = {
                    'name': blob.name,
                    'size': blob.size,
                    'content_type': blob.content_type,
                    'time_created': blob.time_created.isoformat() if blob.time_created else None,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'etag': blob.etag,
                    'md5_hash': blob.md5_hash,
                    'public_url': None,  # Never expose public URLs
                    'metadata': blob.metadata or {}
                }
                files.append(file_info)
            
            return files
        
        except Exception as e:
            logging.error(f"Error listing files for user {user_id}: {e}")
            raise
    
    def delete_file(self, blob_name, user_id):
        """Securely delete a file"""
        try:
            # Validate user access
            if not self._validate_user_access(blob_name, user_id):
                raise PermissionError(f"User {user_id} does not have access to {blob_name}")
            
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)
            
            if blob.exists():
                blob.delete()
                logging.info(f"File {blob_name} deleted successfully")
                return True
            else:
                logging.warning(f"File {blob_name} not found")
                return False
        
        except Exception as e:
            logging.error(f"Error deleting file {blob_name}: {e}")
            raise
    
    def get_file_metadata(self, blob_name, user_id):
        """Get metadata for a specific file"""
        try:
            # Validate user access
            if not self._validate_user_access(blob_name, user_id):
                raise PermissionError(f"User {user_id} does not have access to {blob_name}")
            
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)
            
            if blob.exists():
                blob.reload()
                return {
                    'name': blob.name,
                    'size': blob.size,
                    'content_type': blob.content_type,
                    'time_created': blob.time_created.isoformat() if blob.time_created else None,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'etag': blob.etag,
                    'md5_hash': blob.md5_hash,
                    'metadata': blob.metadata or {}
                }
            else:
                return None
        
        except Exception as e:
            logging.error(f"Error getting metadata for {blob_name}: {e}")
            raise
    
    def download_file_as_image(self, blob_name, user_id):
        """Download file as PIL Image for processing"""
        try:
            # Validate user access
            if not self._validate_user_access(blob_name, user_id):
                raise PermissionError(f"User {user_id} does not have access to {blob_name}")
            
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)
            
            if not blob.exists():
                raise FileNotFoundError(f"File {blob_name} not found")
            
            # Download file as bytes
            image_bytes = blob.download_as_bytes()
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            return image.convert("RGB")
        
        except Exception as e:
            logging.error(f"Error downloading file {blob_name} as image: {e}")
            raise
    
    def _generate_secure_blob_name(self, user_id, original_filename):
        """Generate a secure blob name with user isolation"""
        # Sanitize filename
        safe_filename = self._sanitize_filename(original_filename)
        
        # Add timestamp and UUID for uniqueness
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        return f"uploads/{user_id}/{timestamp}_{unique_id}_{safe_filename}"
    
    def _validate_user_access(self, blob_name, user_id):
        """Validate that user has access to the blob"""
        return blob_name.startswith(f"uploads/{user_id}/")
    
    def _validate_content_type(self, content_type):
        """Validate content type for uploads"""
        allowed_types = {
            'image/jpeg',
            'image/jpg',
            'image/png',
            'image/gif',
            'image/webp'
        }
        return content_type.lower() in allowed_types
    
    def _sanitize_filename(self, filename):
        """Sanitize filename for safe storage"""
        import re
        
        # Get just the filename without path
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
        
        # Limit length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext
        
        # Ensure we have a filename
        if not filename:
            filename = f"file_{uuid.uuid4().hex[:8]}.jpg"
        
        return filename
    
    def cleanup_expired_files(self, days_old=30):
        """Clean up files older than specified days (admin function)"""
        try:
            bucket = self.client.bucket(self.bucket_name)
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            blobs = bucket.list_blobs(prefix="uploads/")
            deleted_count = 0
            
            for blob in blobs:
                if blob.time_created and blob.time_created < cutoff_date:
                    blob.delete()
                    deleted_count += 1
                    logging.info(f"Deleted expired file: {blob.name}")
            
            logging.info(f"Cleanup completed. Deleted {deleted_count} expired files.")
            return deleted_count
        
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
            raise

class StorageQuotaManager:
    """Manage user storage quotas"""
    
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self.default_quota_mb = 100  # 100MB default quota per user
    
    def check_user_quota(self, user_id, file_size_bytes=0):
        """Check if user has enough quota for upload"""
        try:
            user_files = self.storage_manager.list_user_files(user_id)
            current_usage = sum(file['size'] or 0 for file in user_files)
            quota_bytes = self.default_quota_mb * 1024 * 1024
            
            return {
                'current_usage_bytes': current_usage,
                'quota_bytes': quota_bytes,
                'available_bytes': quota_bytes - current_usage,
                'can_upload': (current_usage + file_size_bytes) <= quota_bytes,
                'usage_percentage': (current_usage / quota_bytes) * 100
            }
        
        except Exception as e:
            logging.error(f"Error checking quota for user {user_id}: {e}")
            raise
    
    def set_user_quota(self, user_id, quota_mb):
        """Set custom quota for a user (admin function)"""
        # This would typically be stored in a database
        # For now, we'll just log it
        logging.info(f"Setting quota for user {user_id} to {quota_mb}MB")
        return True