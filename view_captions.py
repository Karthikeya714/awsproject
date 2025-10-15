"""Simple Streamlit app to view DynamoDB captions."""
import streamlit as st
import boto3
from datetime import datetime

st.set_page_config(page_title="Caption Gallery", page_icon="📊", layout="wide")

# Initialize DynamoDB
@st.cache_resource
def init_dynamodb():
    return boto3.resource('dynamodb', region_name='eu-north-1')

dynamodb = init_dynamodb()
table = dynamodb.Table('image_captions')

# Page header
st.title("📊 Image Caption Gallery")
st.markdown("View all captions stored in DynamoDB")
st.markdown("---")

# Get data
with st.spinner("Loading data from DynamoDB..."):
    response = table.scan()
    items = response.get('Items', [])

if len(items) == 0:
    st.warning("⚠️ No captions found in DynamoDB")
    st.info("💡 Upload images and save captions using the main app to see them here!")
else:
    st.success(f"✅ Found {len(items)} captions")
    
    # Sort by timestamp (newest first)
    items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Display in columns
    cols = st.columns(2)
    
    for i, item in enumerate(items):
        col = cols[i % 2]
        
        with col:
            st.markdown("### 🖼️ Image Caption")
            
            # Show image if URL exists
            image_url = item.get('image_url', '')
            if image_url:
                try:
                    st.image(image_url, use_container_width=True)
                except:
                    st.error("❌ Could not load image")
            
            # Show metadata
            st.markdown(f"**💬 Caption:**")
            st.info(item.get('caption_text', 'N/A'))
            
            with st.expander("📋 Details"):
                st.markdown(f"**🆔 Image ID:** `{item.get('image_id', 'N/A')}`")
                st.markdown(f"**📅 Timestamp:** {item.get('timestamp', 'N/A')}")
                st.markdown(f"**🔗 URL:** [{image_url}]({image_url})")
            
            st.markdown("---")

# Footer
st.markdown("---")
st.markdown("🌐 **View in AWS Console:** [DynamoDB Table](https://eu-north-1.console.aws.amazon.com/dynamodbv2/home?region=eu-north-1#item-explorer?table=image_captions)")

# Refresh button
if st.button("🔄 Refresh Data"):
    st.cache_resource.clear()
    st.rerun()
