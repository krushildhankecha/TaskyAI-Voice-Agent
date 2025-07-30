import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import av
import numpy as np
import soundfile as sf
import tempfile
import uuid
import os
import logging

from app.core.stt import transcribe_audio
from app.core.tts import speak
from app.core.action_handler import perform_action

logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title="TaskyAI Voice", layout="centered")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "recording" not in st.session_state:
    st.session_state.recording = False
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = ""
if "auto_tts_enabled" not in st.session_state:
    st.session_state.auto_tts_enabled = True


# --- AUDIO RECORDER ---
class AudioRecorder(AudioProcessorBase):
    def __init__(self) -> None:
        self.frames = []
        self.sample_rate = None

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray()
        self.sample_rate = frame.sample_rate
        self.frames.append(pcm.T)
        return frame


# --- MAIN UI ---
def main():

    # Initialize session state variables at the top
    if "groq_api_key" not in st.session_state:
        st.session_state.groq_api_key = ""

    if "text_input" not in st.session_state:
        st.session_state.text_input = ""

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "mic_enabled" not in st.session_state:
        st.session_state.mic_enabled = True

    if "tts_enabled" not in st.session_state:
        st.session_state.tts_enabled = True


    st.title("🎙️ TaskyAI Voice Assistant")

    # API Key
    st.session_state.groq_api_key = st.text_input(
        "🔑 Enter Groq API Key",
        type="password",
        placeholder="sk-...",
        value=st.session_state.groq_api_key,
    )

    if not st.session_state.groq_api_key:
        st.warning("API key required to continue.")
        return

    # Toggle for TTS Output
    st.toggle("🔊 Enable Voice Output", key="auto_tts_enabled", value=True)

    # --- TEXT OR VOICE INPUT BOX ---
    col1, col2 = st.columns([4, 1])
    with col1:
        user_text = st.text_input("💬 Type your message")

        if st.button("Send"):
            if user_text.strip():
                transcript = user_text.strip()
                st.session_state.messages.append({
                    "role": "user",
                    "content": transcript,
                    "audio": None
                })
                st.session_state.text_input = ""  # Only reset after submission

    with col2:
        record = st.toggle("🎙️ Mic", key="recording")

    # --- WebRTC Recording ---
    if record:
        ctx = webrtc_streamer(
            key="voice",
            mode=WebRtcMode.SENDRECV,
            audio_processor_factory=AudioRecorder,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={"audio": True, "video": False},
        )
        st.session_state.ctx = ctx

    # --- PROCESS AUDIO AFTER STOP ---
    if not record and "ctx" in st.session_state and st.session_state.ctx:
        ctx = st.session_state.ctx
        processor = ctx.audio_processor
        if processor and processor.frames:
            audio_file = save_audio(processor)
            transcript = transcribe_audio(audio_file)
            append_user_message(transcript, audio_file)
            get_bot_response(transcript)

    # --- PROCESS TEXT INPUT ---
    if user_text:
        append_user_message(user_text, None)
        get_bot_response(user_text)
        st.session_state.text_input = ""

    # --- CHAT DISPLAY ---
    st.markdown("### 🧾 Conversation")
    for msg in st.session_state.messages:
        print("\n\n--- Message ---")
        print(type(msg))
        print(msg)  # Debugging line to see message structure
        print(msg["role"], msg["content"])
        align = "flex-start" if msg["role"] == "user" else "flex-end"
        bg_color = "#e6f7ff" if msg["role"] == "user" else "#f9f0ff"
        with st.container():
            st.markdown(
                f"""
                <div style='background-color: {bg_color}; padding: 10px; border-radius: 10px; margin: 5px 0; text-align: left; max-width: 80%; align-self: {align};'>
                    <b>{'🧑 You' if msg["role"] == "user" else '🤖 Assistant'}</b><br>
                    {msg["content"]}
                </div>
                """,
                unsafe_allow_html=True
            )
            if msg.get("audio") and msg["role"] == "user":
                st.audio(msg["audio"], format="audio/wav")
            if msg.get("audio") and msg["role"] == "assistant" and st.session_state.auto_tts_enabled:
                st.audio(msg["audio"], format="audio/mp3", start_time=0)


# --- HELPER FUNCTIONS ---

def save_audio(processor) -> str:
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio_data = np.concatenate(processor.frames, axis=0)
    if audio_data.dtype != np.int16:
        audio_data = (audio_data * 32767).astype(np.int16)
    sf.write(temp_wav.name, audio_data, samplerate=processor.sample_rate, subtype='PCM_16')
    logging.info(f"✅ Audio saved to {temp_wav.name}")
    return temp_wav.name


def append_user_message(text: str, audio_path: str):
    st.session_state.messages.append({
        "role": "user",
        "content": text,
        "audio": audio_path
    })


def get_bot_response(prompt: str):
    response = perform_action(prompt, api_key=st.session_state.groq_api_key)
    audio_path = speak(response) if st.session_state.auto_tts_enabled else None
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "audio": audio_path
    })


# --- ENTRY POINT ---
if __name__ == "__main__":
    main()
