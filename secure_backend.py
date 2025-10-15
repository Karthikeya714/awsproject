"""
Secure Flask Backend with Google Identity Platform & Cloud Storage
Features:
- Firebase Authentication with ID token verification
- Signed URLs for secure Cloud Storage access
- AI-powered image captioning
- User-isolated file storage
- Comprehensive security middleware
"""

import os
import logging
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
import firebase_admin
from firebase_admin import credentials, auth
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import io
from dotenv import load_dotenv

# Import our custom modules
from auth_security import AuthMiddleware, SecurityConfig, StorageSecurityUtils, ERROR_RESPONSES
from storage_manager import CloudStorageManager, StorageQuotaManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-this-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Configure CORS
CORS(app, 
     origins=SecurityConfig.get_cors_origins(),
     methods=['GET', 'POST', 'PUT', 'DELETE'],
     allow_headers=['Content-Type', 'Authorization'])

# Initialize JWT
jwt = JWTManager(app)

# Global variables
storage_manager = None
quota_manager = None
processor = None
model = None
firebase_initialized = False

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    global firebase_initialized
    try:
        firebase_service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        if not firebase_service_account_path:
            raise ValueError("FIREBASE_SERVICE_ACCOUNT_PATH environment variable not set")
        
        SecurityConfig.validate_service_account_file(firebase_service_account_path)
        cred = credentials.Certificate(firebase_service_account_path)
        firebase_admin.initialize_app(cred)
        firebase_initialized = True
        logger.info("Firebase initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return False

def initialize_storage():
    """Initialize Cloud Storage manager"""
    global storage_manager, quota_manager
    try:
        service_account_path = os.getenv('GOOGLE_CLOUD_SERVICE_ACCOUNT_PATH')
        bucket_name = os.getenv('GOOGLE_CLOUD_STORAGE_BUCKET')
        
        if not service_account_path or not bucket_name:
            raise ValueError("Storage configuration missing")
        
        storage_manager = CloudStorageManager(service_account_path, bucket_name)
        quota_manager = StorageQuotaManager(storage_manager)
        logger.info("Storage manager initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize storage: {e}")
        return False

def initialize_ai_model():
    """Initialize BLIP model for image captioning"""
    global processor, model
    try:
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        logger.info("BLIP model loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to load BLIP model: {e}")
        return False

# Initialize all services
firebase_initialized = initialize_firebase()
storage_initialized = initialize_storage()
model_initialized = initialize_ai_model()

# Routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'services': {
            'firebase': firebase_initialized,
            'storage': storage_initialized,
            'ai_model': model_initialized
        },
        'version': '1.0.0'
    })

@app.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user with Firebase ID token"""
    if not firebase_initialized:
        return jsonify({'error': 'Authentication service unavailable'}), 503
    
    try:
        data = request.get_json()
        if not data or 'idToken' not in data:
            return jsonify({'error': 'ID token required'}), 400
        
        id_token = data['idToken']
        
        # Verify Firebase ID token
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        email = decoded_token.get('email')
        
        # Create JWT for our backend
        access_token = create_access_token(
            identity=user_id,
            additional_claims={
                'email': email,
                'email_verified': decoded_token.get('email_verified', False)
            }
        )
        
        # Get user quota info
        quota_info = None
        if storage_initialized:
            try:
                quota_info = quota_manager.check_user_quota(user_id)
            except Exception as e:
                logger.warning(f"Could not get quota info for user {user_id}: {e}")
        
        return jsonify({
            'success': True,
            'access_token': access_token,
            'user': {
                'uid': user_id,
                'email': email,
                'name': decoded_token.get('name', ''),
                'picture': decoded_token.get('picture', ''),
                'email_verified': decoded_token.get('email_verified', False)
            },
            'quota': quota_info
        })
    
    except auth.InvalidIdTokenError:
        return jsonify(ERROR_RESPONSES['INVALID_TOKEN']), 401
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/storage/upload-url', methods=['POST'])
@AuthMiddleware.verify_firebase_token()
def get_upload_url():
    """Generate signed URL for file upload"""
    if not storage_initialized:
        return jsonify({'error': 'Storage service unavailable'}), 503
    
    try:
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({'error': 'Filename required'}), 400
        
        filename = data['filename']
        content_type = data.get('contentType', 'image/jpeg')
        file_size = data.get('fileSize', 0)
        
        # Validate file type
        if not SecurityConfig.validate_upload_file_type(filename):
            return jsonify(ERROR_RESPONSES['INVALID_FILE_TYPE']), 400
        
        user_id = request.user['uid']
        
        # Check user quota
        quota_info = quota_manager.check_user_quota(user_id, file_size)
        if not quota_info['can_upload']:
            return jsonify({
                'error': 'Storage quota exceeded',
                'code': 'QUOTA_EXCEEDED',
                'quota_info': quota_info
            }), 413
        
        # Generate signed upload URL
        upload_info = storage_manager.generate_upload_url(
            user_id=user_id,
            original_filename=filename,
            content_type=content_type,
            expiration_minutes=30
        )
        
        return jsonify({
            'success': True,
            'upload_url': upload_info['url'],
            'blob_name': upload_info['blob_name'],
            'method': upload_info['method'],
            'expires_at': upload_info['expires_at'],
            'content_type': content_type
        })
    
    except Exception as e:
        logger.error(f"Error generating upload URL: {e}")
        return jsonify({'error': 'Failed to generate upload URL'}), 500

@app.route('/storage/download-url', methods=['POST'])
@AuthMiddleware.verify_firebase_token()
def get_download_url():
    """Generate signed URL for file download"""
    if not storage_initialized:
        return jsonify({'error': 'Storage service unavailable'}), 503
    
    try:
        data = request.get_json()
        if not data or 'blobName' not in data:
            return jsonify({'error': 'Blob name required'}), 400
        
        blob_name = data['blobName']
        user_id = request.user['uid']
        
        # Generate signed download URL (validates user access internally)
        download_info = storage_manager.generate_download_url(
            blob_name=blob_name,
            user_id=user_id,
            expiration_minutes=15
        )
        
        return jsonify({
            'success': True,
            'download_url': download_info['url'],
            'expires_at': download_info['expires_at']
        })
    
    except PermissionError:
        return jsonify(ERROR_RESPONSES['ACCESS_DENIED']), 403
    except Exception as e:
        logger.error(f"Error generating download URL: {e}")
        return jsonify({'error': 'Failed to generate download URL'}), 500

@app.route('/ai/generate-caption', methods=['POST'])
@AuthMiddleware.verify_firebase_token()
def generate_caption():
    """Generate AI caption for uploaded image"""
    if not model_initialized:
        return jsonify({'error': 'AI service unavailable'}), 503
    
    if not storage_initialized:
        return jsonify({'error': 'Storage service unavailable'}), 503
    
    try:
        data = request.get_json()
        if not data or 'blobName' not in data:
            return jsonify({'error': 'Blob name required'}), 400
        
        blob_name = data['blobName']
        style = data.get('style', 'Instagram')
        user_id = request.user['uid']
        
        # Download and process image
        image = storage_manager.download_file_as_image(blob_name, user_id)
        
        # Generate caption using BLIP
        inputs = processor(image, return_tensors="pt")
        with torch.no_grad():
            out = model.generate(**inputs, max_length=50, num_beams=4)
        basic_caption = processor.decode(out[0], skip_special_tokens=True)
        
        # Style the caption
        styled_caption = create_advanced_caption(basic_caption, style)
        
        return jsonify({
            'success': True,
            'basic_caption': basic_caption,
            'styled_caption': styled_caption,
            'style': style,
            'image_info': {
                'width': image.width,
                'height': image.height,
                'mode': image.mode
            }
        })
    
    except PermissionError:
        return jsonify(ERROR_RESPONSES['ACCESS_DENIED']), 403
    except Exception as e:
        logger.error(f"Error generating caption: {e}")
        return jsonify({'error': 'Failed to generate caption'}), 500

@app.route('/user/files', methods=['GET'])
@AuthMiddleware.verify_firebase_token()
def list_user_files():
    """List user's uploaded files"""
    if not storage_initialized:
        return jsonify({'error': 'Storage service unavailable'}), 503
    
    try:
        user_id = request.user['uid']
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 files
        
        files = storage_manager.list_user_files(user_id, limit=limit)
        quota_info = quota_manager.check_user_quota(user_id)
        
        return jsonify({
            'success': True,
            'files': files,
            'total_files': len(files),
            'quota': quota_info
        })
    
    except Exception as e:
        logger.error(f"Error listing user files: {e}")
        return jsonify({'error': 'Failed to list files'}), 500

@app.route('/user/files/<path:blob_name>', methods=['DELETE'])
@AuthMiddleware.verify_firebase_token()
def delete_user_file(blob_name):
    """Delete a user's file"""
    if not storage_initialized:
        return jsonify({'error': 'Storage service unavailable'}), 503
    
    try:
        user_id = request.user['uid']
        
        # Delete file (validates user access internally)
        success = storage_manager.delete_file(blob_name, user_id)
        
        if success:
            return jsonify({'success': True, 'message': 'File deleted successfully'})
        else:
            return jsonify({'error': 'File not found'}), 404
    
    except PermissionError:
        return jsonify(ERROR_RESPONSES['ACCESS_DENIED']), 403
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({'error': 'Failed to delete file'}), 500

@app.route('/user/quota', methods=['GET'])
@AuthMiddleware.verify_firebase_token()
def get_user_quota():
    """Get user's storage quota information"""
    if not storage_initialized:
        return jsonify({'error': 'Storage service unavailable'}), 503
    
    try:
        user_id = request.user['uid']
        quota_info = quota_manager.check_user_quota(user_id)
        
        return jsonify({
            'success': True,
            'quota': quota_info
        })
    
    except Exception as e:
        logger.error(f"Error getting quota info: {e}")
        return jsonify({'error': 'Failed to get quota information'}), 500

# Caption styling functions (from original app)
import random

def create_advanced_caption(blip_caption, style):
    """Create styled caption based on basic caption"""
    caption = blip_caption.lower().strip()
    words = caption.split()
    
    style_generators = {
        "Funny": generate_funny_caption,
        "Poetic": generate_poetic_caption,
        "Aesthetic": generate_aesthetic_caption,
        "Instagram": generate_instagram_caption
    }
    
    generator = style_generators.get(style, generate_instagram_caption)
    return generator(caption, words)

def generate_funny_caption(caption, words):
    templates = [
        f"When you're trying to be photogenic but end up with {caption} 😂 #PhotoFail #Relatable",
        f"POV: You thought you looked good but the camera said '{caption}' 🤣 #Reality #Funny",
        f"That moment when {caption} and you can't even... 😅 #Awkward #Real #Moments",
        f"Me trying to be aesthetic: *gets {caption}* 🙃 #ExpectationVsReality #Funny"
    ]
    return random.choice(templates)

def generate_poetic_caption(caption, words):
    templates = [
        f"In whispered moments of grace, {caption} tells a story untold ✨ #Poetry #Beauty",
        f"Where light meets shadow, {caption} blooms eternal 🌸 #Poetic #Art #Beauty",
        f"Through the lens of wonder, {caption} speaks to hearts that listen 💫 #Poetry #Deep",
        f"Silent symphonies play where {caption} dances with time ⏰ #Poetic #Timeless"
    ]
    return random.choice(templates)

def generate_aesthetic_caption(caption, words):
    templates = [
        f"soft mornings ☁️ {caption} #Aesthetic #Minimalist #Calm #Vibe",
        f"golden hour feelings when {caption} meets serenity ✨ #Aesthetic #Golden #Dreamy",
        f"finding beauty in {caption} 🤎 #Aesthetic #Simple #Pure #Minimalist",
        f"quiet moments • {caption} • pure bliss ☁️ #Aesthetic #Quiet #Peace"
    ]
    return random.choice(templates)

def generate_instagram_caption(caption, words):
    templates = [
        f"Living for moments like this! {caption} 💕 #InstaGood #Life #Happy #PhotoOfTheDay",
        f"Caught in the perfect moment: {caption} 📸 #Instagram #Life #Moments #Memories",
        f"This is what happiness looks like ➜ {caption} ✨ #InstaLife #Happiness #Vibes",
        f"Making memories one photo at a time • {caption} 💫 #Memories #InstaGood #Life"
    ]
    return random.choice(templates)

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'code': 'BAD_REQUEST'}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify(ERROR_RESPONSES['AUTH_TOKEN_MISSING']), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify(ERROR_RESPONSES['ACCESS_DENIED']), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found', 'code': 'NOT_FOUND'}), 404

@app.errorhandler(413)
def payload_too_large(error):
    return jsonify({'error': 'File too large', 'code': 'FILE_TOO_LARGE'}), 413

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'code': 'INTERNAL_ERROR'}), 500

if __name__ == '__main__':
    import torch
    
    # Run the application
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Flask app on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Services initialized - Firebase: {firebase_initialized}, Storage: {storage_initialized}, AI: {model_initialized}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )