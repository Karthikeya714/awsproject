import os
import json
from functools import wraps
from flask import request, jsonify
import firebase_admin
from firebase_admin import auth
import logging

class SecurityConfig:
    """Security configuration and utilities"""
    
    @staticmethod
    def validate_service_account_file(file_path):
        """Validate service account JSON file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Service account file not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                service_account = json.load(f)
                
            required_fields = [
                'type', 'project_id', 'private_key_id', 'private_key',
                'client_email', 'client_id', 'auth_uri', 'token_uri'
            ]
            
            for field in required_fields:
                if field not in service_account:
                    raise ValueError(f"Missing required field in service account: {field}")
            
            return service_account
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in service account file")
    
    @staticmethod
    def get_cors_origins():
        """Get CORS origins from environment"""
        origins_str = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
        return [origin.strip() for origin in origins_str.split(',')]
    
    @staticmethod
    def validate_upload_file_type(filename):
        """Validate uploaded file type"""
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        _, ext = os.path.splitext(filename.lower())
        return ext in allowed_extensions
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename for safe storage"""
        import re
        # Remove any path separators and dangerous characters
        filename = os.path.basename(filename)
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Limit length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext
        return filename

class AuthMiddleware:
    """Authentication middleware for Firebase ID tokens"""
    
    @staticmethod
    def verify_firebase_token(require_email_verified=False):
        """Decorator to verify Firebase ID token"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                auth_header = request.headers.get('Authorization')
                if not auth_header or not auth_header.startswith('Bearer '):
                    return jsonify({
                        'error': 'Authorization token required',
                        'code': 'AUTH_TOKEN_MISSING'
                    }), 401
                
                token = auth_header.split(' ')[1]
                
                try:
                    # Verify the ID token
                    decoded_token = auth.verify_id_token(token)
                    
                    # Check email verification if required
                    if require_email_verified and not decoded_token.get('email_verified', False):
                        return jsonify({
                            'error': 'Email verification required',
                            'code': 'EMAIL_NOT_VERIFIED'
                        }), 401
                    
                    # Add user info to request object
                    request.user = {
                        'uid': decoded_token['uid'],
                        'email': decoded_token.get('email'),
                        'email_verified': decoded_token.get('email_verified', False),
                        'name': decoded_token.get('name'),
                        'picture': decoded_token.get('picture'),
                        'firebase_claims': decoded_token
                    }
                    
                    return f(*args, **kwargs)
                    
                except auth.InvalidIdTokenError:
                    return jsonify({
                        'error': 'Invalid ID token',
                        'code': 'INVALID_TOKEN'
                    }), 401
                except auth.ExpiredIdTokenError:
                    return jsonify({
                        'error': 'Token has expired',
                        'code': 'TOKEN_EXPIRED'
                    }), 401
                except Exception as e:
                    logging.error(f"Token verification error: {e}")
                    return jsonify({
                        'error': 'Token verification failed',
                        'code': 'TOKEN_VERIFICATION_FAILED'
                    }), 401
            
            return decorated_function
        return decorator
    
    @staticmethod
    def check_user_permissions(required_permissions=None):
        """Check if user has required custom claims/permissions"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not hasattr(request, 'user'):
                    return jsonify({
                        'error': 'Authentication required',
                        'code': 'AUTH_REQUIRED'
                    }), 401
                
                if required_permissions:
                    user_claims = request.user.get('firebase_claims', {})
                    for permission in required_permissions:
                        if not user_claims.get(permission, False):
                            return jsonify({
                                'error': f'Permission required: {permission}',
                                'code': 'INSUFFICIENT_PERMISSIONS'
                            }), 403
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator

class StorageSecurityUtils:
    """Security utilities for Cloud Storage operations"""
    
    @staticmethod
    def validate_user_access(blob_name, user_id):
        """Validate that user has access to the blob"""
        # Users can only access files in their own directory
        allowed_prefix = f"uploads/{user_id}/"
        return blob_name.startswith(allowed_prefix)
    
    @staticmethod
    def generate_secure_blob_name(user_id, original_filename):
        """Generate a secure blob name with user isolation"""
        from datetime import datetime
        import uuid
        
        # Sanitize the filename
        safe_filename = SecurityConfig.sanitize_filename(original_filename)
        
        # Add timestamp and random component for uniqueness
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        # Create the secure path
        return f"uploads/{user_id}/{timestamp}_{unique_id}_{safe_filename}"
    
    @staticmethod
    def validate_content_type(content_type):
        """Validate content type for uploads"""
        allowed_types = {
            'image/jpeg',
            'image/jpg', 
            'image/png',
            'image/gif',
            'image/webp'
        }
        return content_type.lower() in allowed_types

class RateLimitConfig:
    """Rate limiting configuration"""
    
    # Rate limits per endpoint (requests per minute)
    RATE_LIMITS = {
        'upload_url': 10,      # 10 upload URLs per minute
        'generate_caption': 5,  # 5 caption generations per minute
        'download_url': 20,    # 20 download URLs per minute
        'auth_login': 5        # 5 login attempts per minute
    }
    
    @staticmethod
    def get_rate_limit(endpoint):
        """Get rate limit for specific endpoint"""
        return RateLimitConfig.RATE_LIMITS.get(endpoint, 60)  # Default 60/min

# Error response templates
ERROR_RESPONSES = {
    'AUTH_TOKEN_MISSING': {
        'error': 'Authorization token is required',
        'code': 'AUTH_TOKEN_MISSING',
        'details': 'Include "Authorization: Bearer <token>" header'
    },
    'INVALID_TOKEN': {
        'error': 'Invalid authentication token',
        'code': 'INVALID_TOKEN',
        'details': 'Token may be malformed or expired'
    },
    'ACCESS_DENIED': {
        'error': 'Access denied to requested resource',
        'code': 'ACCESS_DENIED', 
        'details': 'User does not have permission to access this resource'
    },
    'INVALID_FILE_TYPE': {
        'error': 'Invalid file type',
        'code': 'INVALID_FILE_TYPE',
        'details': 'Only image files are allowed (JPG, PNG, GIF, WebP)'
    },
    'RATE_LIMIT_EXCEEDED': {
        'error': 'Rate limit exceeded',
        'code': 'RATE_LIMIT_EXCEEDED',
        'details': 'Too many requests. Please try again later.'
    }
}