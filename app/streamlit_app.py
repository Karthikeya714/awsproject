"""Main Streamlit application for Image Caption Generator."""
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
from backend.auth import AuthManager
from backend.rate_limiter import RateLimiter
from backend.models import RateLimitConfig, CaptionResult


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
        'auth': AuthManager(),
        'rate_limiter': RateLimiter(RateLimitConfig())
    }

services = init_services()

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
    .caption-box {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 2px solid #e0e0e0;
    }
    .concise-caption {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .creative-caption {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .privacy-notice {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #ff9800;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def check_authentication():
    """Check if user is authenticated."""
    # For development, use session state
    # In production, integrate with Cognito Hosted UI
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    return st.session_state.authenticated


def login_page():
    """Display login page."""
    st.markdown('<div class="main-header"><h1>🖼️ Image Caption Generator</h1></div>', unsafe_allow_html=True)
    
    st.info("👋 Please sign in to continue")
    
    # Privacy notice
    st.markdown("""
    <div class="privacy-notice">
        <h4>🔒 Privacy Notice</h4>
        <p>
        • Your images are stored encrypted in AWS S3<br>
        • Images are retained for 90 days unless you delete them<br>
        • We don't store any personally identifiable information<br>
        • You can delete your images and captions at any time
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Development login (replace with Cognito in production)
        with st.form("login_form"):
            username = st.text_input("Username", help="For demo: any username")
            password = st.text_input("Password", type="password", help="For demo: any password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                login_btn = st.form_submit_button("🔐 Sign In", use_container_width=True)
            with col_b:
                signup_btn = st.form_submit_button("📝 Sign Up", use_container_width=True)
        
        if login_btn or signup_btn:
            if username:
                st.session_state.authenticated = True
                st.session_state.user_id = username
                st.success("✅ Signed in successfully!")
                st.rerun()
            else:
                st.error("Please enter a username")
    
    st.markdown("---")
    st.caption("🔒 Secured by AWS Cognito | 📊 Powered by AWS Bedrock & SageMaker")


def upload_page():
    """Main upload and caption generation page."""
    st.markdown('<div class="main-header"><h1>🖼️ Image Caption Generator</h1></div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 Welcome, {st.session_state.user_id}!")
        
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.rerun()
        
        st.markdown("---")
        
        # Rate limit info
        remaining = services['rate_limiter'].get_remaining(st.session_state.user_id)
        st.metric("⏱️ Requests Remaining", remaining)
        
        st.markdown("---")
        st.markdown("### ⚙️ Settings")
        
        use_rekognition = st.checkbox(
            "Use Rekognition labels",
            value=services['config'].use_rekognition,
            help="Enhance captions with AWS Rekognition object detection"
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.caption(f"""
        **Provider:** {services['config'].caption_provider.value}  
        **Region:** {services['config'].aws_region}  
        **Version:** 1.0.0
        """)
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload", "📜 History", "❌ Delete Data"])
    
    with tab1:
        upload_tab()
    
    with tab2:
        history_tab()
    
    with tab3:
        delete_tab()


def upload_tab():
    """Upload and caption generation tab."""
    st.markdown("### Upload an Image")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose an image (JPEG/PNG, max 10 MB)",
            type=['jpg', 'jpeg', 'png'],
            help="Upload an image to generate captions"
        )
        
        if uploaded_file:
            # Validate file size
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            if file_size_mb > services['config'].max_image_size_mb:
                st.error(f"⚠️ Image too large ({file_size_mb:.1f} MB). Maximum size is {services['config'].max_image_size_mb} MB.")
                return
            
            # Display image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)
            
            # Generate caption button
            if st.button("✨ Generate Captions", type="primary", use_container_width=True):
                generate_captions(uploaded_file, image)
    
    with col2:
        if 'current_result' in st.session_state and st.session_state.current_result:
            display_captions(st.session_state.current_result)


def generate_captions(uploaded_file, image: Image.Image):
    """Generate captions for uploaded image."""
    # Check rate limit
    if not services['rate_limiter'].is_allowed(st.session_state.user_id):
        st.error("⚠️ Rate limit exceeded. Please try again later.")
        return
    
    with st.spinner("🔄 Processing image..."):
        try:
            # Upload to S3
            file_bytes = uploaded_file.getvalue()
            metadata = services['s3'].upload_image(
                user_id=st.session_state.user_id,
                file_data=file_bytes,
                filename=uploaded_file.name,
                content_type=uploaded_file.type
            )
            
            # Preprocess image
            processed_image = services['caption'].preprocess_image(image)
            
            # Generate captions
            concise, creative, labels, provider = services['caption'].generate_caption(
                processed_image,
                file_bytes
            )
            
            # Save to database
            result = CaptionResult(
                image_id=metadata.image_id,
                user_id=st.session_state.user_id,
                concise_caption=concise,
                creative_caption=creative,
                labels=labels,
                model=services['config'].bedrock_model_id or "default",
                provider=provider,
                s3_url=metadata.s3_url,
                thumbnail_url=metadata.thumbnail_url
            )
            
            services['db'].save_caption(result)
            
            # Store in session
            st.session_state.current_result = result
            
            st.success("✅ Captions generated successfully!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def display_captions(result: CaptionResult):
    """Display generated captions."""
    st.markdown("### Generated Captions")
    
    # Concise caption
    st.markdown(f"""
    <div class="caption-box concise-caption">
        <h4>📝 Concise Caption</h4>
        <p style="font-size: 1.1em;">{result.concise_caption}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Creative caption
    st.markdown(f"""
    <div class="caption-box creative-caption">
        <h4>🎨 Creative Caption</h4>
        <p style="font-size: 1.1em;">{result.creative_caption}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Labels
    if result.labels:
        st.markdown("**🏷️ Detected Labels:**")
        st.write(", ".join(result.labels[:5]))
    
    # Metadata
    with st.expander("ℹ️ Metadata"):
        st.json({
            "Image ID": result.image_id,
            "Provider": result.provider.value,
            "Model": result.model,
            "Timestamp": result.timestamp.isoformat()
        })


def history_tab():
    """Display user's caption history."""
    st.markdown("### Your Caption History")
    
    try:
        history, next_key = services['db'].get_user_history(
            st.session_state.user_id,
            limit=20
        )
        
        if not history:
            st.info("No captions yet. Upload an image to get started!")
            return
        
        for item in history:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                # Get presigned URL for thumbnail
                thumbnail_url = services['s3'].get_presigned_url(item.thumbnail_url)
                if thumbnail_url:
                    st.image(thumbnail_url, use_container_width=True)
            
            with col2:
                st.markdown(f"**📝 Concise:** {item.concise_caption}")
                st.markdown(f"**🎨 Creative:** {item.creative_caption}")
                st.caption(f"🕒 {item.timestamp.strftime('%Y-%m-%d %H:%M')}")
                if item.labels:
                    st.caption(f"🏷️ {', '.join(item.labels[:3])}")
            
            st.markdown("---")
        
        if next_key:
            st.info("More items available. Pagination coming soon!")
            
    except Exception as e:
        st.error(f"Error loading history: {str(e)}")


def delete_tab():
    """Delete user data tab."""
    st.markdown("### Delete Your Data")
    
    st.warning("""
    ⚠️ **Warning**: This action cannot be undone!
    
    This will permanently delete:
    - All your uploaded images
    - All generated captions
    - All associated metadata
    """)
    
    confirm = st.text_input(
        "Type 'DELETE' to confirm:",
        help="Type DELETE in capital letters"
    )
    
    if st.button("🗑️ Delete All My Data", type="primary", disabled=(confirm != "DELETE")):
        with st.spinner("Deleting your data..."):
            try:
                # Delete from S3
                s3_count = services['s3'].delete_user_images(st.session_state.user_id)
                
                # Delete from DynamoDB
                db_count = services['db'].delete_user_data(st.session_state.user_id)
                
                st.success(f"✅ Deleted {s3_count} images and {db_count} database records.")
                
                # Clear session
                if 'current_result' in st.session_state:
                    del st.session_state.current_result
                
            except Exception as e:
                st.error(f"Error deleting data: {str(e)}")


def main():
    """Main application entry point."""
    if not check_authentication():
        login_page()
    else:
        upload_page()


if __name__ == "__main__":
    main()
