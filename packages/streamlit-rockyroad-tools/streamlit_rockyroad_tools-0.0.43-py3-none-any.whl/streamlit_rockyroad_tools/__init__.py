"""
Streamlit RockyRoad Tools - A collection of Streamlit components

This package provides various custom Streamlit components that can be easily
imported and used in your Streamlit applications.

Available components:
- st_notification_banner: A notification banner component with message and learn more link
- st_folder_navigator: A folder navigation component with breadcrumb-style layout
- st_navigation_tile: A clickable tile component for navigation with title, body, and image
- st_notifications: Notification components (info, success, warning, error)
- st_breadcrumbs: A breadcrumb navigation component for hierarchical navigation
- st_download_base64: An invisible component for triggering file downloads from base64 data
- st_page_library: A collapsible hierarchical page library component with links
"""

# Import all components to make them available at package level
from .st_notification_banner import st_notification_banner
from .st_folder_navigator import st_folder_navigator
from .st_navigation_tile import st_navigation_tile
from .st_notifications import st_info, st_success, st_warning, st_error
from .st_breadcrumbs import st_breadcrumbs
from .st_download_tile import st_download_tile
from .st_fetch_data import st_fetch_data
from .st_download_base64 import st_download_base64
from .st_page_library import st_page_library

# Define what gets imported with "from streamlit_rockyroad_tools import *"
__all__ = [
    "st_notification_banner", 
    "st_folder_navigator",
    "st_navigation_tile",
    "st_download_tile",
    "st_fetch_data",
    "st_download_base64",
    "st_info",
    "st_success",
    "st_warning",
    "st_error",
    "st_breadcrumbs",
    "st_page_library",
]

# Package metadata
__version__ = '0.0.2'
__author__ = 'Your Name'
__description__ = 'A collection of Streamlit components'
