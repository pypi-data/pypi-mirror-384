import streamlit as st
import sys
import os

# Ensure package import works when running example directly, regardless of CWD
_this_file = os.path.abspath(__file__)
_component_dir = os.path.dirname(_this_file)  # .../streamlit_rockyroad_tools/st_fetch_data
_package_dir = os.path.dirname(_component_dir)  # .../streamlit_rockyroad_tools
_repo_root = os.path.dirname(_package_dir)  # repo root containing streamlit_rockyroad_tools
if _repo_root not in sys.path:
    sys.path.append(_repo_root)
from streamlit_rockyroad_tools import st_fetch_data

st.set_page_config(page_title="Fetch Data Example")

st.markdown("## st_fetch_data example")

# Example controls
url = st.text_input("URL", value="https://httpbin.org/get")
method = st.selectbox("Method", options=["GET", "POST"], index=0)
source = st.text_input("Data Source Label", value="httpbin")

payload = None
if method == "POST":
    payload_text = st.text_area("POST JSON Body", value='{"hello": "world"}')
    try:
        import json
        payload = json.loads(payload_text)
    except Exception:
        st.warning("Invalid JSON; sending no body")
        payload = None

if 'fetched' not in st.session_state:
    st.session_state.fetched = False


def on_fetch_handler(tag: str):
    st.session_state.fetched = True
    st.toast(f"Fetch completed for {tag}")

res = st_fetch_data(
    url=url,
    type=method,
    data_source=source,
    data=payload,
    key="fetch1",
    on_fetch=on_fetch_handler,
    args=[source],
)

st.write("Return value:", res)

if st.session_state.fetched:
    st.success("Fetch completed! Check the return value above.")
