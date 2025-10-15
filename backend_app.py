import os
from datetime import timedelta, datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from google.cloud import storage
from google.oauth2 import service_account
import firebase_admin
from firebase_admin import credentials, auth
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
import requests
import json
import logging
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Enable CORS
CORS(app, origins=["http://localhost:3000", "https://yourdomain.com"])

# Initialize JWT
jwt = JWTManager(app)

# Initialize Firebase Admin SDK
def initialize_firebase():
    try:
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        if not service_account_path:
            raise ValueError("FIREBASE_SERVICE_ACCOUNT_PATH environment variable not set")
        
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        return True
    except Exception as e:
        logging.error(f"Failed to initialize Firebase: {e}")
        return False

# Initialize Google Cloud Storage
def initialize_storage_client():
    try:
        service_account_path = os.getenv('GOOGLE_CLOUD_SERVICE_ACCOUNT_PATH')
        if not service_account_path:
            raise ValueError("GOOGLE_CLOUD_SERVICE_ACCOUNT_PATH environment variable not set")
        
        credentials_obj = service_account.Credentials.from_service_account_file(
            service_account_path
        )
        return storage.Client(credentials=credentials_obj)
    except Exception as e:
        logging.error(f"Failed to initialize Storage client: {e}")
        return None

# Global variables
firebase_initialized = initialize_firebase()
storage_client = initialize_storage_client()
BUCKET_NAME = os.getenv('GOOGLE_CLOUD_STORAGE_BUCKET', 'your-bucket-name')

# Load BLIP model for image captioning
processor = None
model = None

def load_blip_model():
    global processor, model
    try:
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        logging.info("BLIP model loaded successfully")
    except Exception as e:
        logging.error(f"Error loading BLIP model: {e}")

# Authentication decorator
def verify_firebase_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not firebase_initialized:
            return jsonify({'error': 'Firebase not initialized'}), 500
        
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            decoded_token = auth.verify_id_token(token)
            request.user = decoded_token
            return f(*args, **kwargs)
        except Exception as e:
            logging.error(f"Token verification failed: {e}")
            return jsonify({'error': 'Invalid token'}), 401
    
    return decorated_function

# Helper function to generate signed URLs
def generate_signed_url(blob_name, method='GET', expiration_minutes=15):
    """Generate a signed URL for Cloud Storage"""
    if not storage_client:
        raise Exception("Storage client not initialized")
    
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method=method,
            headers={'Content-Type': 'image/jpeg'} if method == 'PUT' else None
        )
        
        return url
    except Exception as e:
        logging.error(f"Error generating signed URL: {e}")
        raise

# Routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'firebase_initialized': firebase_initialized,
        'storage_initialized': storage_client is not None,
        'model_loaded': processor is not None and model is not None
    })

@app.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user with Firebase ID token and return JWT"""
    if not firebase_initialized:
        return jsonify({'error': 'Firebase not initialized'}), 500
    
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        
        if not id_token:
            return jsonify({'error': 'ID token required'}), 400
        
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        email = decoded_token.get('email')
        
        # Create JWT token for our backend
        access_token = create_access_token(
            identity=user_id,
            additional_claims={'email': email}
        )
        
        return jsonify({
            'success': True,
            'access_token': access_token,
            'user': {
                'uid': user_id,
                'email': email,
                'name': decoded_token.get('name', ''),
                'picture': decoded_token.get('picture', '')
            }
        })
    
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({'error': 'Authentication failed'}), 401

@app.route('/storage/upload-url', methods=['POST'])
@verify_firebase_token
def get_upload_url():
    """Generate signed URL for uploading images"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        content_type = data.get('contentType', 'image/jpeg')
        
        if not filename:
            return jsonify({'error': 'Filename required'}), 400
        
        # Create unique blob name with user ID
        user_id = request.user['uid']
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        blob_name = f"uploads/{user_id}/{timestamp}_{filename}"
        
        # Generate signed URL for upload
        upload_url = generate_signed_url(blob_name, method='PUT', expiration_minutes=30)
        
        return jsonify({
            'success': True,
            'uploadUrl': upload_url,
            'blobName': blob_name,
            'expiresIn': 30 * 60  # 30 minutes in seconds
        })
    
    except Exception as e:
        logging.error(f"Error generating upload URL: {e}")
        return jsonify({'error': 'Failed to generate upload URL'}), 500

@app.route('/storage/download-url', methods=['POST'])
@verify_firebase_token
def get_download_url():
    """Generate signed URL for downloading images"""
    try:
        data = request.get_json()
        blob_name = data.get('blobName')
        
        if not blob_name:
            return jsonify({'error': 'Blob name required'}), 400
        
        # Verify user owns this file
        user_id = request.user['uid']
        if not blob_name.startswith(f"uploads/{user_id}/"):
            return jsonify({'error': 'Access denied'}), 403
        
        # Generate signed URL for download
        download_url = generate_signed_url(blob_name, method='GET', expiration_minutes=15)
        
        return jsonify({
            'success': True,
            'downloadUrl': download_url,
            'expiresIn': 15 * 60  # 15 minutes in seconds
        })
    
    except Exception as e:
        logging.error(f"Error generating download URL: {e}")
        return jsonify({'error': 'Failed to generate download URL'}), 500

@app.route('/ai/generate-caption', methods=['POST'])
@verify_firebase_token
def generate_caption():
    """Generate AI caption for uploaded image"""
    if not processor or not model:
        return jsonify({'error': 'AI model not loaded'}), 500
    
    try:
        data = request.get_json()
        blob_name = data.get('blobName')
        style = data.get('style', 'Instagram')
        
        if not blob_name:
            return jsonify({'error': 'Blob name required'}), 400
        
        # Verify user owns this file
        user_id = request.user['uid']
        if not blob_name.startswith(f"uploads/{user_id}/"):
            return jsonify({'error': 'Access denied'}), 403
        
        # Download image from Cloud Storage
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)
        
        # Download image as bytes and convert to PIL Image
        image_bytes = blob.download_as_bytes()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Generate basic caption using BLIP
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs, max_length=50, num_beams=4)
        basic_caption = processor.decode(out[0], skip_special_tokens=True)
        
        # Style the caption
        styled_caption = create_advanced_caption(basic_caption, style)
        
        return jsonify({
            'success': True,
            'basicCaption': basic_caption,
            'styledCaption': styled_caption,
            'style': style
        })
    
    except Exception as e:
        logging.error(f"Error generating caption: {e}")
        return jsonify({'error': 'Failed to generate caption'}), 500

@app.route('/user/files', methods=['GET'])
@verify_firebase_token
def list_user_files():
    """List user's uploaded files"""
    try:
        user_id = request.user['uid']
        prefix = f"uploads/{user_id}/"
        
        bucket = storage_client.bucket(BUCKET_NAME)
        blobs = bucket.list_blobs(prefix=prefix)
        
        files = []
        for blob in blobs:
            files.append({
                'name': blob.name,
                'size': blob.size,
                'timeCreated': blob.time_created.isoformat() if blob.time_created else None,
                'updated': blob.updated.isoformat() if blob.updated else None,
                'contentType': blob.content_type
            })
        
        return jsonify({
            'success': True,
            'files': files
        })
    
    except Exception as e:
        logging.error(f"Error listing files: {e}")
        return jsonify({'error': 'Failed to list files'}), 500

# Caption styling functions (same as original app.py)
import random
import io

def create_advanced_caption(blip_caption, style):
    """Advanced caption generation with multiple variations"""
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
    funny_templates = [
        f"When you're trying to be photogenic but end up with {caption} 😂 #PhotoFail #Relatable #Mood #Life",
        f"POV: You thought you looked good but the camera said '{caption}' 🤣 #Reality #Funny #Candid",
        f"That moment when {caption} and you can't even... 😅 #Awkward #Funny #Real #Moments",
        f"Me trying to be aesthetic: *gets {caption}* 🙃 #ExpectationVsReality #Funny #Relatable",
        f"When life gives you {caption}, make memes 🤪 #Funny #Life #Humor #Mood"
    ]
    return random.choice(funny_templates)

def generate_poetic_caption(caption, words):
    poetic_templates = [
        f"In whispered moments of grace, {caption} tells a story untold ✨ #Poetry #Beauty #Soul #Moment",
        f"Where light meets shadow, {caption} blooms eternal 🌸 #Poetic #Art #Beauty #Inspiration",
        f"Through the lens of wonder, {caption} speaks to hearts that listen 💫 #Poetry #Deep #Meaning #Art",
        f"Silent symphonies play where {caption} dances with time ⏰ #Poetic #Timeless #Beauty #Soul",
        f"In the cathedral of moments, {caption} becomes prayer 🙏 #Poetry #Spiritual #Beauty #Peace"
    ]
    return random.choice(poetic_templates)

def generate_aesthetic_caption(caption, words):
    aesthetic_templates = [
        f"soft mornings ☁️ {caption} #Aesthetic #Minimalist #Calm #Vibe #Clean",
        f"golden hour feelings when {caption} meets serenity ✨ #Aesthetic #Golden #Dreamy #Soft",
        f"finding beauty in {caption} 🤎 #Aesthetic #Simple #Pure #Minimalist #Vibe",
        f"quiet moments • {caption} • pure bliss ☁️ #Aesthetic #Quiet #Peace #Minimalist",
        f"captured: {caption} in all its gentle glory 🕊️ #Aesthetic #Gentle #Pure #Soft #Clean"
    ]
    return random.choice(aesthetic_templates)

def generate_instagram_caption(caption, words):
    instagram_templates = [
        f"Living for moments like this! {caption} 💕 #InstaGood #Life #Happy #PhotoOfTheDay #Blessed",
        f"Caught in the perfect moment: {caption} 📸 #Instagram #Life #Moments #Memories #Good",
        f"This is what happiness looks like ➜ {caption} ✨ #InstaLife #Happiness #Vibes #Daily #Love",
        f"Making memories one photo at a time • {caption} 💫 #Memories #InstaGood #Life #Moments",
        f"Current mood: {caption} and loving it! 😍 #Mood #InstaDaily #Life #Happy #Blessed"
    ]
    return random.choice(instagram_templates)

if __name__ == '__main__':
    # Load BLIP model on startup
    load_blip_model()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )