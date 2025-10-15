import os
import streamlit.components.v1 as components
from typing import Optional, Dict, Any

# Create a _RELEASE constant to switch between development and production modes
_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "st_page_library",
        url="http://localhost:3000",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend", "build")
    _component_func = components.declare_component("st_page_library", path=build_dir)

def st_page_library(
    config: Dict[str, Any],
    key: Optional[str] = None,
) -> Optional[dict]:
    """
    A Streamlit component that displays a collapsible hierarchical page library with links.
    
    The component displays a three-level hierarchy:
    - Level 1: Main heading (collapsible)
    - Level 2: Sub-headings (collapsible)
    - Level 3: List of clickable links (fetched from API or provided directly)
    
    Parameters
    ----------
    config : dict
        Configuration dictionary with the following structure:
        {
            "level_1_heading": str,  # Main heading text
            "expand": bool,  # Whether level 1 is initially expanded
            "fetch": {  # Optional fetch configuration for API calls
                "url": str,
                "method": str,  # "GET" or "POST"
                "headers": dict,  # Optional headers
                "body": str  # Optional request body
            },
            "collapsible_content": [  # List of level 2 items
                {
                    "level_2_heading": str,  # Sub-heading text
                    "expand": bool,  # Whether level 2 is initially expanded
                    "page_category_1": str,  # Filter parameter 1
                    "page_category_2": str,  # Filter parameter 2
                    "page_category_3": str,  # Filter parameter 3
                    "display_style": str,  # "collapsible-list"
                    "url": str,  # Optional direct URL
                    "url_label": str  # Optional direct URL label
                }
            ]
        }
        
        The component will fetch links from the API using the fetch configuration
        and filter parameters (page_category_1, page_category_2, page_category_3).
        
        API response should be a list of objects:
        [
            {
                "title": str,  # Link text
                "url": str  # Link URL
            }
        ]
        
        Alternatively, if "url" and "url_label" are provided in a level 2 item,
        a single link will be displayed instead of fetching from the API.
        
    key : str, optional
        An optional key that uniquely identifies this component.
        
    Returns
    -------
    dict or None
        Returns a dictionary with information about clicked links:
        {
            "clicked_url": str,  # The URL that was clicked
            "clicked_title": str,  # The title of the clicked link
            "timestamp": int  # Timestamp of the click
        }
        Returns None if no link has been clicked.
    
    Examples
    --------
    >>> config = {
    ...     "level_1_heading": "Rock Breaker Systems Manuals",
    ...     "expand": True,
    ...     "fetch": {
    ...         "url": "https://api.example.com/page-library",
    ...         "method": "POST",
    ...         "headers": {"Content-Type": "application/json"},
    ...         "body": ""
    ...     },
    ...     "collapsible_content": [
    ...         {
    ...             "level_2_heading": "2025 Rock Breaker Systems Manuals",
    ...             "expand": False,
    ...             "page_category_1": "BTI",
    ...             "page_category_2": "Systems",
    ...             "page_category_3": "2025 Rockbreaker Manuals",
    ...             "display_style": "collapsible-list",
    ...             "url": "",
    ...             "url_label": ""
    ...         }
    ...     ]
    ... }
    >>> result = st_page_library(config, key="page_library")
    """
    # Call the component function
    component_value = _component_func(
        config=config,
        key=str(key) if key else None,
        default=None,
    )
    
    return component_value
