import streamlit as st
import uuid

def toggle_switch(label: str, value: bool, key: str):
    return st.toggle(label, value=value, key=key)

def chat_bubble(message: str, sender: str = "user", show_audio: bool = False, audio_path: str = None):
    with st.container():
        align = "flex-start" if sender == "user" else "flex-end"
        color = "#e6f7ff" if sender == "user" else "#f6ffed"

        st.markdown(f"""
            <div style='
                display: flex;
                justify-content: {align};
                padding: 8px;
            '>
                <div style='
                    background-color: {color};
                    padding: 10px 15px;
                    border-radius: 12px;
                    max-width: 70%;
                '>
                    <p style='margin: 0;'>{message}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Optional audio player
        if show_audio and audio_path:
            st.audio(audio_path, format="audio/mp3")
