import streamlit as st
from components.upload import render_uploader
from components.history_download import render_history_download
from components.chatUI import render_chat


st.set_page_config(page_title="AI Medical Assistant", page_icon="🩺", layout="centered")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 820px;}
    .hero {
        background: linear-gradient(135deg, #0E7C86 0%, #14A3A8 100%);
        color: white; padding: 1.4rem 1.6rem; border-radius: 16px;
        margin-bottom: 1.2rem;
    }
    .hero h1 {margin: 0; font-size: 1.8rem; color: white;}
    .hero p {margin: 0.3rem 0 0 0; opacity: 0.92;}
    .stChatMessage {border-radius: 14px;}
    </style>
    <div class="hero">
      <h1>🩺 Medical Assistant Chatbot</h1>
      <p>Upload your medical PDFs in the sidebar, then ask questions about them.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# The chat runs first so the download button below always sees the newest messages.
render_chat()

with st.sidebar:
    st.title("🩺 MediBot")
    render_uploader()
    st.divider()
    render_history_download()
    st.divider()
    st.caption("General information only, not medical advice. Do not upload private patient records.")