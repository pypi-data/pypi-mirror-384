"""
Example usage of st_download_base64 component

This example demonstrates how to use the st_download_base64 component to trigger
automatic file downloads from base64 data with zero height footprint.
"""

import streamlit as st
import sys
import os
import json

# Ensure package import works when running example directly, regardless of CWD
_this_file = os.path.abspath(__file__)
_component_dir = os.path.dirname(_this_file)  # .../streamlit_rockyroad_tools/st_fetch_data
_package_dir = os.path.dirname(_component_dir)  # .../streamlit_rockyroad_tools
_repo_root = os.path.dirname(_package_dir)  # repo root containing streamlit_rockyroad_tools
if _repo_root not in sys.path:
    sys.path.append(_repo_root)

from streamlit_rockyroad_tools import st_download_base64

st.set_page_config(page_title="Download Base64 Example", layout="wide")

st.title("🔽 st_download_base64 Component Example")
st.markdown("This component allows you to trigger file downloads with **zero height footprint**.")

# Initialize the component (loads without triggering download)
if 'component_initialized' not in st.session_state:
    st.session_state.component_initialized = False

if not st.session_state.component_initialized:
    st.info("Initializing download component...")
    result = st_download_base64(initialize=True, key="init_component")
    if result is not None:
        st.session_state.component_initialized = True
        st.success("Component initialized!")
        st.rerun()

# Example 1: Download text file
st.header("📄 Example 1: Download Text File")
text_content = st.text_area(
    "Enter text content to download:",
    value="Hello, World!\nThis is a test file created with st_download_base64.",
    height=100
)

filename = st.text_input("Filename:", value="sample.txt")

if st.button("Download Text File", type="primary"):
    if text_content and filename:
        # Convert text to bytes
        file_bytes = text_content.encode('utf-8')
        
        # Trigger download
        result = st_download_base64(
            file_content=file_bytes,
            download_filename=filename,
            key=f"download_text_{hash(text_content)}"
        )
        
        if result:
            if result.get('download_triggered'):
                st.success(f"✅ Download triggered for '{result['filename']}' ({result['file_size']} bytes)")
            elif result.get('error'):
                st.error(f"❌ Download failed: {result['error']}")
    else:
        st.warning("Please enter both text content and filename.")

# Example 2: Download JSON file
st.header("📊 Example 2: Download JSON File")

sample_data = {
    "name": "John Doe",
    "age": 30,
    "city": "New York",
    "hobbies": ["reading", "swimming", "coding"],
    "metadata": {
        "created_at": "2024-01-01",
        "version": "1.0"
    }
}

st.json(sample_data)

if st.button("Download JSON File", type="primary"):
    # Convert dict to JSON bytes
    json_str = json.dumps(sample_data, indent=2)
    file_bytes = json_str.encode('utf-8')
    
    # Trigger download
    result = st_download_base64(
        file_content=file_bytes,
        download_filename="sample_data.json",
        key="download_json"
    )
    
    if result:
        if result.get('download_triggered'):
            st.success(f"✅ Download triggered for '{result['filename']}' ({result['file_size']} bytes)")
        elif result.get('error'):
            st.error(f"❌ Download failed: {result['error']}")

# Example 3: Download uploaded file (re-download)
st.header("🔄 Example 3: Re-download Uploaded File")
st.markdown("Upload a file and then download it back using the component.")

uploaded_file = st.file_uploader("Choose a file to re-download:", type=None)

if uploaded_file is not None:
    st.write(f"**File details:**")
    st.write(f"- Name: {uploaded_file.name}")
    st.write(f"- Size: {len(uploaded_file.getvalue())} bytes")
    st.write(f"- Type: {uploaded_file.type}")
    
    if st.button("Re-download File", type="primary"):
        # Get file content as bytes
        file_bytes = uploaded_file.getvalue()
        
        # Trigger download with original filename
        result = st_download_base64(
            file_content=file_bytes,
            download_filename=uploaded_file.name,
            key=f"redownload_{uploaded_file.name}"
        )
        
        if result:
            if result.get('download_triggered'):
                st.success(f"✅ Download triggered for '{result['filename']}' ({result['file_size']} bytes)")
            elif result.get('error'):
                st.error(f"❌ Download failed: {result['error']}")

# Component information
st.header("ℹ️ Component Information")
st.markdown("""
**Key Features:**
- ✅ **Zero height footprint** - Component sets its height to 0 pixels
- ✅ **Invisible operation** - No visual elements, just triggers downloads
- ✅ **Base64 encoding** - Handles binary data conversion automatically
- ✅ **Error handling** - Returns detailed status information
- ✅ **Initialization mode** - Can pre-load component without triggering downloads

**Comparison with `components.html`:**
- ❌ `components.html(height=0)` - May not reliably set height to 0
- ✅ `st_download_base64` - Guarantees 0 height through React component

**Return Value:**
The component returns a dictionary with:
- `download_triggered`: Boolean indicating if download was attempted
- `filename`: The filename used for download
- `file_size`: Size of the file in bytes
- `download_id`: Unique identifier for this download
- `error`: Error message if download failed (optional)
""")

# Usage code example
st.header("💻 Usage Code")
st.code("""
from streamlit_rockyroad_tools import st_download_base64

# Initialize component (optional)
st_download_base64(initialize=True, key="init")

# Trigger download
result = st_download_base64(
    file_content=file_bytes,
    download_filename="myfile.txt",
    key="download_key"
)

if result and result.get('download_triggered'):
    st.success(f"Downloaded {result['filename']}")
""", language="python")
