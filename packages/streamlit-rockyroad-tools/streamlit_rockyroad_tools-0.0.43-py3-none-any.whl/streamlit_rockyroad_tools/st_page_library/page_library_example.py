import streamlit as st
import sys
import os

# Add the repository root to path to import the package
# This goes up two levels: st_page_library -> streamlit_rockyroad_tools -> repo root
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, repo_root)
from streamlit_rockyroad_tools import st_page_library

st.set_page_config(page_title="Page Library Example", layout="wide")

st.title("Page Library Component Examples")

st.markdown("---")

# Example 1: With API Fetch
st.header("Example 1: Page Library with API Fetch")
st.markdown("This example shows a page library that fetches links from an API based on category filters.")

config_with_fetch = {
    "level_1_heading": "Widget Systems Manuals",
    "expand": True,
    "fetch": {
        "url": "https://api.example.com/page-library",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        },
        "body": ""
    },
    "collapsible_content": [
        {
            "level_2_heading": "2025 Widget Systems Manuals",
            "expand": False,
            "page_category_1": "Acme",
            "page_category_2": "Systems",
            "page_category_3": "2025 Widget Manuals",
            "display_style": "collapsible-list",
            "url": "",
            "url_label": ""
        },
        {
            "level_2_heading": "2024 Widget Systems Manuals",
            "expand": False,
            "page_category_1": "Acme",
            "page_category_2": "Systems",
            "page_category_3": "2024 Widget Manuals",
            "display_style": "collapsible-list",
            "url": "",
            "url_label": ""
        },
        {
            "level_2_heading": "2023 Widget Systems Manuals",
            "expand": False,
            "page_category_1": "Acme",
            "page_category_2": "Systems",
            "page_category_3": "2023 Widget Manuals",
            "display_style": "collapsible-list",
            "url": "",
            "url_label": ""
        }
    ]
}

result1 = st_page_library(config_with_fetch, key="page_library_fetch")

if result1:
    st.success(f"Clicked: {result1.get('clicked_title')} - {result1.get('clicked_url')}")

st.markdown("---")

# Example 2: With Direct URLs
st.header("Example 2: Page Library with Direct URLs")
st.markdown("This example shows a page library with direct URL links instead of fetching from an API.")

config_with_urls = {
    "level_1_heading": "Product Documentation",
    "expand": False,
    "collapsible_content": [
        {
            "level_2_heading": "User Guides",
            "expand": False,
            "page_category_1": "",
            "page_category_2": "",
            "page_category_3": "",
            "display_style": "collapsible-list",
            "url": "https://example.com/user-guide.pdf",
            "url_label": "Complete User Guide (PDF)"
        },
        {
            "level_2_heading": "Installation Manuals",
            "expand": False,
            "page_category_1": "",
            "page_category_2": "",
            "page_category_3": "",
            "display_style": "collapsible-list",
            "url": "https://example.com/installation.pdf",
            "url_label": "Installation Manual (PDF)"
        },
        {
            "level_2_heading": "Technical Specifications",
            "expand": False,
            "page_category_1": "",
            "page_category_2": "",
            "page_category_3": "",
            "display_style": "collapsible-list",
            "url": "https://example.com/specs.pdf",
            "url_label": "Technical Specifications (PDF)"
        }
    ]
}

result2 = st_page_library(config_with_urls, key="page_library_urls")

if result2:
    st.success(f"Clicked: {result2.get('clicked_title')} - {result2.get('clicked_url')}")

st.markdown("---")

# Example 3: Mixed Configuration
st.header("Example 3: Mixed Configuration")
st.markdown("This example shows a page library with both API-fetched links and direct URLs.")

config_mixed = {
    "level_1_heading": "Training Resources",
    "expand": True,
    "fetch": {
        "url": "https://api.example.com/training-resources",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        }
    },
    "collapsible_content": [
        {
            "level_2_heading": "Video Tutorials",
            "expand": True,
            "page_category_1": "Training",
            "page_category_2": "Videos",
            "page_category_3": "2025",
            "display_style": "collapsible-list",
            "url": "",
            "url_label": ""
        },
        {
            "level_2_heading": "Quick Start Guide",
            "expand": False,
            "page_category_1": "",
            "page_category_2": "",
            "page_category_3": "",
            "display_style": "collapsible-list",
            "url": "https://example.com/quick-start.pdf",
            "url_label": "Download Quick Start Guide"
        }
    ]
}

result3 = st_page_library(config_mixed, key="page_library_mixed")

if result3:
    st.success(f"Clicked: {result3.get('clicked_title')} - {result3.get('clicked_url')}")

st.markdown("---")

# Show component state
st.subheader("Component Return Values")
st.markdown("The component returns information about clicked links:")
st.code("""
{
    "clicked_url": "https://example.com/document.pdf",
    "clicked_title": "Document Title",
    "timestamp": 1234567890
}
""")
