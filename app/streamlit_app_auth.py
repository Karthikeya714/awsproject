"""Main Streamlit application with authentication for Image Caption Generator."""
import os
import sys
import io
from datetime import datetime
from typing import Optional
import streamlit as st
from PIL import Image

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.config import config_manager
from backend.s3_manager import S3Manager
from backend.db import DynamoDBManager
from backend.caption_service import CaptionService
from backend.rate_limiter import RateLimiter
from backend.models import RateLimitConfig, CaptionResult
from backend.auth_security import SimpleUserAuth


# Page config
st.set_page_config(
    page_title="Image Caption Generator",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
@st.cache_resource
def init_services():
    """Initialize backend services."""
    return {
        'config': config_manager.config,
        's3': S3Manager(),
        'db': DynamoDBManager(),
        'caption': CaptionService(),
        'user_auth': SimpleUserAuth(),
        'rate_limiter': RateLimiter(RateLimitConfig())
    }

services = init_services()

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'page' not in st.session_state:
    st.session_state.page = 'signin'

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .auth-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 3rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    .auth-header {
        text-align: center;
        margin-bottom: 2rem;
        color: #667eea;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-message {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-message {
        padding: 1rem;
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        font-size: 1.1rem;
        border-radius: 8px;
        font-weight: 600;
    }
    .user-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def signup_page():
    """Display signup page."""
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="auth-header">🖼️ Create Account</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Join us to start generating amazing image captions!</p>', unsafe_allow_html=True)
    
    with st.form("signup_form"):
        full_name = st.text_input("Full Name", placeholder="John Doe")
        email = st.text_input("Email Address", placeholder="john@example.com")
        password = st.text_input("Password", type="password", placeholder="Min. 8 characters")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("Create Account")
        
        if submit:
            # Validation
            if not full_name or not email or not password:
                st.markdown('<div class="error-message">❌ All fields are required</div>', unsafe_allow_html=True)
            elif password != confirm_password:
                st.markdown('<div class="error-message">❌ Passwords do not match</div>', unsafe_allow_html=True)
            else:
                # Attempt signup
                with st.spinner("Creating your account..."):
                    success, message, user_id = services['user_auth'].signup(email, password, full_name)
                    
                    if success:
                        st.markdown(f'<div class="success-message">✅ {message}</div>', unsafe_allow_html=True)
                        st.markdown('<div class="info-message">🎉 Account created! Please sign in to continue.</div>', unsafe_allow_html=True)
                        st.session_state.page = 'signin'
                        st.balloons()
                        st.rerun()
                    else:
                        st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p style="text-align: center;">Already have an account?</p>', unsafe_allow_html=True)
    if st.button("Sign In"):
        st.session_state.page = 'signin'
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


def signin_page():
    """Display signin page."""
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="auth-header">🖼️ Welcome Back</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Sign in to continue generating captions</p>', unsafe_allow_html=True)
    
    with st.form("signin_form"):
        email = st.text_input("Email Address", placeholder="john@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("Sign In")
        
        if submit:
            if not email or not password:
                st.markdown('<div class="error-message">❌ Email and password are required</div>', unsafe_allow_html=True)
            else:
                with st.spinner("Signing in..."):
                    success, message, user_data = services['user_auth'].signin(email, password)
                    
                    if success:
                        st.markdown(f'<div class="success-message">✅ {message}</div>', unsafe_allow_html=True)
                        st.session_state.authenticated = True
                        st.session_state.user_data = user_data
                        st.balloons()
                        st.rerun()
                    else:
                        st.markdown(f'<div class="error-message">❌ {message}</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p style="text-align: center;">Don\'t have an account?</p>', unsafe_allow_html=True)
    if st.button("Create Account"):
        st.session_state.page = 'signup'
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


def main_app():
    """Main application after authentication."""
    # Header with user info
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<div class="main-header"><h1>🖼️ Image Caption Generator</h1><p>Upload images and get AI-powered captions</p></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="user-info">', unsafe_allow_html=True)
        st.write(f"👤 **{st.session_state.user_data['full_name']}**")
        st.write(f"📧 {st.session_state.user_data['email']}")
        if st.button("🚪 Logout"):
            services['user_auth'].logout(st.session_state.user_data['session_id'])
            st.session_state.authenticated = False
            st.session_state.user_data = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload Image", "📜 History", "🗑️ Delete Data"])
    
    with tab1:
        upload_tab()
    
    with tab2:
        history_tab()
    
    with tab3:
        delete_tab()


def upload_tab():
    """Upload and caption generation tab."""
    st.markdown("### Upload an Image")
    st.markdown("Supported formats: JPEG, PNG (Max 10 MB)")
    
    uploaded_file = st.file_uploader(
        "Choose an image...",
        type=['jpg', 'jpeg', 'png'],
        help="Upload an image to generate captions"
    )
    
    if uploaded_file is not None:
        # Display image
        image = Image.open(uploaded_file)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(image, caption="Uploaded Image", use_container_width=True)
        
        with col2:
            st.markdown("#### Image Details")
            st.write(f"**Filename:** {uploaded_file.name}")
            st.write(f"**Size:** {uploaded_file.size / 1024:.2f} KB")
            st.write(f"**Dimensions:** {image.size[0]} x {image.size[1]}")
            st.write(f"**Format:** {image.format}")
        
        # Generate captions button
        if st.button("🎨 Generate Captions", type="primary", use_container_width=True):
            user_id = st.session_state.user_data['user_id']
            
            # Check rate limit
            if not services['rate_limiter'].is_allowed(user_id):
                st.error("⏱️ Rate limit exceeded. Please try again later.")
                remaining = services['rate_limiter'].get_remaining(user_id)
                st.info(f"Requests remaining: {remaining}")
                return
            
            with st.spinner("🤖 Generating captions... This may take a few seconds..."):
                try:
                    # Convert image to bytes
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format=image.format or 'PNG')
                    img_bytes = img_byte_arr.getvalue()
                    
                    # Generate caption
                    concise, creative, labels, provider = services['caption'].generate_caption(
                        image=image,
                        image_bytes=img_bytes
                    )
                    
                    # Display results
                    st.success("✅ Captions generated successfully!")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📝 Concise Caption")
                        st.info(concise)
                    
                    with col2:
                        st.markdown("#### 🎭 Creative Caption")
                        st.info(creative)
                    
                    # Show metadata
                    with st.expander("📊 View Details"):
                        st.write(f"**Provider:** {provider}")
                        st.write(f"**Filename:** {uploaded_file.name}")
                        st.write(f"**User ID:** {user_id}")
                        if labels:
                            st.write(f"**Detected labels:** {', '.join(labels[:5])}")
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Error generating caption: {str(e)}")


def history_tab():
    """User history tab."""
    st.markdown("### Your Caption History")
    
    user_id = st.session_state.user_data['user_id']
    
    try:
        history = services['db'].get_user_history(user_id, limit=20)
        
        if not history:
            st.info("📭 No captions yet. Upload an image to get started!")
            return
        
        st.success(f"✅ Found {len(history)} caption(s)")
        
        for idx, item in enumerate(history):
            with st.expander(f"📷 {item.get('filename', 'Unknown')} - {item.get('generated_at', 'N/A')[:10]}"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Try to load thumbnail
                    if item.get('s3_key'):
                        try:
                            presigned_url = services['s3'].get_presigned_url(item['s3_key'])
                            st.image(presigned_url, use_container_width=True)
                        except:
                            st.write("🖼️ Image not available")
                
                with col2:
                    st.markdown("**Concise Caption:**")
                    st.write(item.get('concise_caption', 'N/A'))
                    
                    st.markdown("**Creative Caption:**")
                    st.write(item.get('creative_caption', 'N/A'))
                    
                    st.markdown("**Provider:**")
                    st.write(item.get('provider', 'N/A'))
                    
                    if item.get('detected_labels'):
                        st.markdown("**Detected Labels:**")
                        st.write(", ".join(item['detected_labels'][:5]))
    
    except Exception as e:
        st.error(f"❌ Error loading history: {str(e)}")


def delete_tab():
    """Data deletion tab."""
    st.markdown("### Delete Your Data")
    
    st.warning("""
    ⚠️ **Data Privacy Notice**
    
    You can request deletion of your data at any time. This will:
    - Delete all your uploaded images from storage
    - Remove all caption history from the database
    - This action cannot be undone
    """)
    
    user_id = st.session_state.user_data['user_id']
    
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("#### Delete All My Caption Data")
        st.markdown("This will delete all your images and captions, but keep your account active.")
    
    with col2:
        if st.button("🗑️ Delete Caption Data", type="secondary"):
            with st.spinner("Deleting your data..."):
                try:
                    # Delete from S3
                    services['s3'].delete_user_images(user_id)
                    
                    # Delete from DynamoDB
                    services['db'].delete_user_data(user_id)
                    
                    st.success("✅ All your caption data has been deleted successfully!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Error deleting data: {str(e)}")
    
    st.markdown("---")
    st.markdown("#### Need help?")
    st.markdown(f"Contact us at: **{st.session_state.user_data['email']}**")


def main():
    """Main application entry point."""
    # Check if user is authenticated
    if not st.session_state.authenticated:
        # Check if there's an active session
        if 'session_id' in st.session_state and st.session_state.get('session_id'):
            is_valid, user_data = services['user_auth'].validate_session(st.session_state['session_id'])
            if is_valid:
                st.session_state.authenticated = True
                st.session_state.user_data = user_data
                st.rerun()
        
        # Show auth pages
        if st.session_state.page == 'signup':
            signup_page()
        else:
            signin_page()
    else:
        # Show main app
        main_app()


if __name__ == "__main__":
    main()
