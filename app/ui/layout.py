import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import numpy as np
import soundfile as sf
import tempfile
import os
from app.core.stt import transcribe_audio
from app.core.tts import speak
from app.core.action_handler import perform_action
from app.ui.processor import AudioRecorder
from app.ui.components import api_key_input, toggles, display_transcript

def main_ui():
    st.set_page_config(page_title="Tasky Voice AI", page_icon="🎤")
    st.title("🎙️ TaskyAI Voice Assistant")

    api_key = api_key_input()
    if not api_key:
        st.warning("Please enter your API key.")
        return

    mic_enabled, tts_enabled = toggles()

    if "recording" not in st.session_state:
        st.session_state.recording = False

    if st.button("▶️ Start Listening"):
        st.session_state.recording = True
    if st.button("⏹️ Stop & Process"):
        st.session_state.recording = False

    if st.session_state.recording:
        ctx = webrtc_streamer(
            key="voice",
            mode=WebRtcMode.SENDRECV,
            audio_processor_factory=AudioRecorder,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={"audio": True, "video": False},
        )
        st.session_state.ctx = ctx

    if not st.session_state.recording and "ctx" in st.session_state:
        ctx = st.session_state.ctx
        processor = ctx.audio_processor

        if processor and processor.frames:
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            audio = np.concatenate(processor.frames, axis=0)

            if audio.dtype != np.int16:
                audio = (audio * 32767).astype(np.int16)

            sf.write(temp_wav.name, audio, samplerate=processor.sample_rate, subtype="PCM_16")

            transcript = transcribe_audio(temp_wav.name)
            response = perform_action(transcript, api_key=api_key)

            display_transcript(transcript, response)

            if tts_enabled:
                tts_path = speak(response)
                if tts_path:
                    st.audio(tts_path, format="audio/mp3")
