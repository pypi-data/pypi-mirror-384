import os
import json
import streamlit.components.v1 as components
from typing import Optional, Callable, Any, List, Dict

# Create a _RELEASE constant to switch between development and production modes
_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "st_fetch_data",
        url="http://localhost:3000",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend", "build")
    _component_func = components.declare_component("st_fetch_data", path=build_dir)


def st_fetch_data(
    *,
    url: Optional[str] = None,
    type: Optional[str] = "GET",
    data_source: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
    on_fetch: Optional[Callable[..., Any]] = None,
    args: Optional[List] = None,
    kwargs: Optional[Dict] = None,
) -> Optional[dict]:
    """
    A Streamlit component that performs a fetch/AJAX request to a remote URL and
    returns the data once fetched. Can optionally execute a callback when the fetch completes.

    Parameters
    ----------
    url : str, optional
        The URL to fetch.
    type : str, optional
        HTTP method to use, e.g. "GET" or "POST". Defaults to "GET".
    data_source : str, optional
        A label or identifier for the data source. Returned along with the data.
    data : dict, optional
        Data to include with the request (e.g., for POST body). Will be JSON-encoded.
    key : str, optional
        Streamlit key for the component instance.
    on_fetch : callable, optional
        Callback executed when the fetch operation completes (similar to on_click).
    args : list, optional
        Positional args forwarded to on_fetch.
    kwargs : dict, optional
        Keyword args forwarded to on_fetch.

    Returns
    -------
    dict or None
        Returns a dictionary with fields like 'fetched', 'status', 'data', 'url',
        'method', 'data_source', and potentially 'error' if a failure occurred.
    """
    # Handle the on_fetch callback similar to st_download_tile's on_click
    if callable(on_fetch):
        args = args or []
        kwargs = kwargs or {}

        def create_callback(callback, *cb_args, **cb_kwargs):
            def wrapper(_=None):
                return callback(*cb_args, **cb_kwargs)
            return wrapper

        on_fetch = create_callback(on_fetch, *args, **kwargs)

    component_value = _component_func(
        url=url or "",
        method=(type or "GET").upper(),
        data_source=data_source or "",
        # Pass JSON string to avoid complex serialization issues
        body_json=json.dumps(data) if data is not None else None,
        key=str(key),
        on_change=on_fetch if callable(on_fetch) else None,
    )

    return component_value
