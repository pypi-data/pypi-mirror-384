import os
import base64
import uuid
import streamlit.components.v1 as components
from typing import Optional, Union

# Create a _RELEASE constant to switch between development and production modes
_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "st_download_base64",
        url="http://localhost:3000",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend", "build")
    _component_func = components.declare_component("st_download_base64", path=build_dir)


def st_download_base64(
    file_content: Optional[bytes] = None,
    download_filename: Optional[str] = None,
    initialize: bool = False,
    *,
    key: Optional[str] = None,
) -> Optional[dict]:
    """
    A Streamlit component that triggers automatic download of file content from base64 data.
    This is an invisible component that sets its height to 0 to minimize visual footprint.

    Parameters
    ----------
    file_content : bytes, optional
        The file content as bytes to be downloaded. If None and initialize=False, 
        no download will be triggered.
    download_filename : str, optional
        The filename to use for the downloaded file. If None and initialize=False,
        a default filename will be generated.
    initialize : bool, optional
        If True, only loads the component without triggering a download.
        Use this to pre-load the component. Defaults to False.
    key : str, optional
        Streamlit key for the component instance.

    Returns
    -------
    dict or None
        Returns a dictionary with download status information:
        - 'download_triggered': bool indicating if download was attempted
        - 'filename': str with the download filename used
        - 'file_size': int with the size of the file in bytes
        - 'error': str with error message if download failed
    """
    
    # Generate a unique ID for this download instance
    download_id = str(uuid.uuid4())
    
    # Prepare the data to send to the React component
    if initialize:
        # Initialization mode - no download
        base64_data = ""
        filename = ""
        file_size = 0
    else:
        if file_content is None:
            # No file content provided
            base64_data = ""
            filename = download_filename or "download.bin"
            file_size = 0
        else:
            # Encode file content to base64
            base64_data = base64.b64encode(file_content).decode('utf-8')
            filename = download_filename or f"download_{download_id[:8]}.bin"
            file_size = len(file_content)

    _component_func(
        base64_data=base64_data,
        filename=filename,
        file_size=file_size,
        download_id=download_id,
        initialize=initialize,
        key=str(key) if key else None,
    )

    return None
