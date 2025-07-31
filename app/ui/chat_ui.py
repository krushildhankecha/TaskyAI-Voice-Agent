import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import av
import numpy as np
import soundfile as sf
import tempfile
import logging
from app.core.stt import transcribe_audio
from app.core.tts import speak
from app.core.action_handler import perform_action

logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title="TaskyAI Voice", layout="centered")

# --- SESSION STATE INIT ---
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
if "current_index" not in st.session_state:
    st.session_state.current_index = 0  # index of current chat pair being shown
if "awaiting_response" not in st.session_state:
    st.session_state.awaiting_response = False

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

    # Voice Output toggle
    st.toggle("🔊 Enable Voice Output", key="auto_tts_enabled", value=True)

    # --- Chat Display (Latest Pair) ---
    if len(st.session_state.messages) >= 2:
        i = st.session_state.current_index * 2
        if len(st.session_state.messages) > i + 1:
            user_msg = st.session_state.messages[i]
            bot_msg = st.session_state.messages[i + 1]

            st.markdown("## 🧾 Conversation")
            with st.container():
                st.markdown(f"<div style='background-color:#e6f7ff; color:#000000; padding:10px; border-radius:10px;'><b>🧑 You:</b><br>{user_msg['content']}</div>", unsafe_allow_html=True)
                if user_msg.get("audio"):
                    st.audio(user_msg["audio"], format="audio/wav")

                st.markdown("""
                    <hr style='border:1px solid #ccc;'>
                """, unsafe_allow_html=True)

                st.markdown(f"<div style='background-color:#f9f0ff; color:#000000; padding:10px; border-radius:10px;'><b>🤖 Assistant:</b><br>{bot_msg['content']}</div>", unsafe_allow_html=True)
                if st.session_state.current_index == (len(st.session_state.messages) // 2 - 1) and bot_msg.get("audio") and st.session_state.auto_tts_enabled:
                    st.audio(bot_msg["audio"], format="audio/mp3")

    # --- Input Section: Always Visible ---
    col1, col2 = st.columns([4, 1])
    with col1:
        user_text = st.text_input("💬 Type your message", key="text_input")
        if st.button("Send"):
            if user_text.strip():
                append_user_message(user_text.strip(), None)
                st.session_state.awaiting_response = True
                st.rerun()

    with col2:
        record = st.toggle("🎙️ Mic", key="recording")

    # Audio Recording Logic
    if record:
        ctx = webrtc_streamer(
            key="voice",
            mode=WebRtcMode.SENDRECV,
            audio_processor_factory=AudioRecorder,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={"audio": True, "video": False},
        )
        st.session_state.ctx = ctx

    if not record and "ctx" in st.session_state and st.session_state.ctx:
        ctx = st.session_state.ctx
        processor = ctx.audio_processor
        if processor and processor.frames:
            audio_file = save_audio(processor)
            transcript = transcribe_audio(audio_file)
            append_user_message(transcript, audio_file)
            st.session_state.awaiting_response = True
            st.rerun()

    # --- Awaiting Response: Show spinner and get answer ---
    if st.session_state.awaiting_response:
        with st.spinner("🤖 Thinking..."):
            user_msg = st.session_state.messages[-1]
            response = perform_action(user_msg['content'], api_key=st.session_state.groq_api_key)
            audio_path = speak(response) if st.session_state.auto_tts_enabled else None
            st.session_state.messages.append({"role": "assistant", "content": response, "audio": audio_path})
            st.session_state.awaiting_response = False
            st.session_state.current_index = len(st.session_state.messages) // 2 - 1
            st.rerun()

    # --- Navigation Buttons ---
    left, center, right = st.columns([1, 5, 1])
    with left:
        if st.button("⬅️", disabled=st.session_state.current_index == 0):
            st.session_state.current_index -= 1
    with right:
        if st.button("➡️", disabled=(st.session_state.current_index + 1) * 2 >= len(st.session_state.messages)):
            st.session_state.current_index += 1

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
    st.session_state.messages.append({"role": "user", "content": text, "audio": audio_path})


