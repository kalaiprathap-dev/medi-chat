
import streamlit as st
from utils.api import upload_pdfs_api


def render_uploader():
    st.sidebar.header("Upload medical documents (.PDF)")
    uploaded_files = st.sidebar.file_uploader(
        "Upload multiple PDFs", type="pdf", accept_multiple_files=True
    )
    if st.sidebar.button("Upload DB", use_container_width=True, disabled=not uploaded_files):
        with st.sidebar:
            with st.spinner("Reading and indexing your files... the first request can take about a minute."):
                try:
                    response = upload_pdfs_api(uploaded_files)
                except Exception as e:
                    st.error(f"Could not reach the server. Try again in a minute. ({e})")
                    return
        if response.status_code == 200:
            st.sidebar.success("Uploaded successfully")
        else:
            st.sidebar.error(f"Error: {response.text}")


'''import streamlit as st
from utils.api import upload_pdfs_api


def render_uploader():
    st.sidebar.header("Upload Medical documents (.PDFs)")
    uploaded_files=st.sidebar.file_uploader("Upload multiple PDFs",type="pdf",accept_multiple_files=True)
    if st.sidebar.button("Upload DB") and uploaded_files:
        response=upload_pdfs_api(uploaded_files)
        if response.status_code==200:
            st.sidebar.success("Uploaded successfully")
        else:
            st.sidebar.error(f"Error:{response.text}")'''