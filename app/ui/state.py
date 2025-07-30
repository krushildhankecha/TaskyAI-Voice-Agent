# app/ui/state.py

import streamlit as st

def init_session_state():
    defaults = {
        "recording": False,
        "chat_history": [],
        "groq_api_key": "",
        "tts_enabled": True,
        "mic_enabled": True,
        "current_input": "",  # Text input fallback
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
