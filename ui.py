import streamlit as st
from app.ui.chat_ui import main as render_chat_ui

# Set Streamlit page config
st.set_page_config(
    page_title="TaskyAI Voice Assistant",
    page_icon="🎤",
    layout="wide"
)

# Render the full UI
render_chat_ui()
