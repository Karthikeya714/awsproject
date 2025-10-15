"""Simplified Streamlit app for local testing (no AWS required)."""
import os
import sys
from datetime import datetime
from typing import Optional
import streamlit as st
from PIL import Image
import requests
import io

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.auth_security import SimpleUserAuth

# Page config
st.set_page_config(
    page_title="Image Caption Generator",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize auth service
@st.cache_resource
def init_auth():
    """Initialize authentication service."""
    return SimpleUserAuth()

auth_service = init_auth()

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'page' not in st.session_state:
    st.session_state.page = 'signin'
if 'caption_history' not in st.session_state:
    st.session_state.caption_history = []

# Get HF API token from environment
HF_API_TOKEN = os.getenv('HF_API_TOKEN', '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')

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


def generate_caption_hf(image: Image.Image) -> tuple[str, str]:
    """Generate caption using Hugging Face API."""
    try:
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        
        # Call Hugging Face API
        API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        response = requests.post(API_URL, headers=headers, data=img_bytes)
        
        if response.status_code == 200:
            result = response.json()
            base_caption = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', 'A captioned image')
            
            # Create concise and creative versions
            concise = base_caption[:50] + "..." if len(base_caption) > 50 else base_caption
            creative = f"{base_caption}. This image captures a moment worth remembering."
            
            return concise, creative
        else:
            return "Unable to generate caption", "Please try again with a different image"
            
    except Exception as e:
        return f"Error: {str(e)}", "Caption generation failed"


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
            if not full_name or not email or not password:
                st.markdown('<div class="error-message">❌ All fields are required</div>', unsafe_allow_html=True)
            elif password != confirm_password:
                st.markdown('<div class="error-message">❌ Passwords do not match</div>', unsafe_allow_html=True)
            else:
                success, message, user_id = auth_service.signup(email, password, full_name)
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
                    success, message, user_data = auth_service.signin(email, password)
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
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<div class="main-header"><h1>🖼️ Image Caption Generator</h1><p>Upload images and get AI-powered captions</p></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="user-info">', unsafe_allow_html=True)
        st.write(f"👤 **{st.session_state.user_data['full_name']}**")
        st.write(f"📧 {st.session_state.user_data['email']}")
        if st.button("🚪 Logout"):
            auth_service.logout(st.session_state.user_data['session_id'])
            st.session_state.authenticated = False
            st.session_state.user_data = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📤 Upload Image", "📜 History"])
    
    with tab1:
        upload_tab()
    
    with tab2:
        history_tab()


def upload_tab():
    """Upload and caption generation tab."""
    st.markdown("### Upload an Image")
    st.markdown("Supported formats: JPEG, PNG (Max 10 MB)")
    
    uploaded_file = st.file_uploader("Choose an image...", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(image, caption="Uploaded Image", use_container_width=True)
        
        with col2:
            st.markdown("#### Image Details")
            st.write(f"**Filename:** {uploaded_file.name}")
            st.write(f"**Size:** {uploaded_file.size / 1024:.2f} KB")
            st.write(f"**Dimensions:** {image.size[0]} x {image.size[1]}")
        
        if st.button("🎨 Generate Captions", type="primary", use_container_width=True):
            with st.spinner("🤖 Generating captions... This may take 5-10 seconds..."):
                concise, creative = generate_caption_hf(image)
                
                st.success("✅ Captions generated successfully!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 📝 Concise Caption")
                    st.info(concise)
                
                with col2:
                    st.markdown("#### 🎭 Creative Caption")
                    st.info(creative)
                
                # Save to history
                st.session_state.caption_history.append({
                    'filename': uploaded_file.name,
                    'concise': concise,
                    'creative': creative,
                    'timestamp': datetime.now().isoformat()
                })
                
                st.balloons()


def history_tab():
    """User history tab."""
    st.markdown("### Your Caption History")
    
    if not st.session_state.caption_history:
        st.info("📭 No captions yet. Upload an image to get started!")
        return
    
    st.success(f"✅ Found {len(st.session_state.caption_history)} caption(s)")
    
    for idx, item in enumerate(reversed(st.session_state.caption_history)):
        with st.expander(f"📷 {item['filename']} - {item['timestamp'][:10]}"):
            st.markdown("**Concise Caption:**")
            st.write(item['concise'])
            st.markdown("**Creative Caption:**")
            st.write(item['creative'])


def main():
    """Main application entry point."""
    if not st.session_state.authenticated:
        if st.session_state.page == 'signup':
            signup_page()
        else:
            signin_page()
    else:
        main_app()


if __name__ == "__main__":
    main()
