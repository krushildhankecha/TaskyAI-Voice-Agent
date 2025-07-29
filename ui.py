import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import av
import soundfile as sf
import tempfile
import os
import numpy as np
import logging

# Your core logic imports
from app.core.stt import transcribe_audio
from app.core.tts import speak
from app.core.action_handler import perform_action

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="Tasky Voice AI", page_icon="🎤")
st.title("🎙️ TaskyAI Voice Assistant")

# Session state to control recording
if "recording" not in st.session_state:
    st.session_state.recording = False
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None


class AudioRecorder(AudioProcessorBase):
    def __init__(self) -> None:
        self.frames = []
        self.sample_rate = None

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray()
        self.sample_rate = frame.sample_rate
        self.frames.append(pcm.T)
        return frame


def main():
    st.write("🎤 Press **Start Listening** to begin and **Stop & Process** to get response.")

    # Start Listening Button
    if st.button("▶️ Start Listening"):
        st.session_state.recording = True
        st.session_state.audio_file = None

    # Stop & Process Button
    if st.button("⏹️ Stop & Process"):
        st.session_state.recording = False

    # Start WebRTC only if listening
    if st.session_state.recording:
        ctx = webrtc_streamer(
            key="voice",
            mode=WebRtcMode.SENDRECV,
            audio_processor_factory=AudioRecorder,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={"audio": True, "video": False},
        )
        st.session_state.ctx = ctx

    # Process after stop
    if not st.session_state.recording and "ctx" in st.session_state:
        ctx = st.session_state.ctx
        processor = ctx.audio_processor

        if processor and processor.frames:
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

            # Stack frames along time axis → shape: (samples, 1)
            stacked_frames = np.concatenate(processor.frames, axis=0)

            if stacked_frames.dtype != np.int16:
                stacked_frames = (stacked_frames * 32767).astype(np.int16)

            sf.write(temp_wav.name, stacked_frames, samplerate=processor.sample_rate, subtype='PCM_16')
            logging.info(f"✅ Audio saved to {temp_wav.name}")

            # ---------------- Whisper Transcription ----------------
            logging.info("🔠 Transcribing with Whisper...")
            # transcript = transcribe_audio(temp_wav.name)
            transcript = transcribe_audio("/Users/krushildhankecha/Desktop/Projects/TaskyAI-Voice-Agent/app/data/tell_me_some.mp3")
            logging.info(f"📝 Transcript: {transcript}")

            # ---------------- Assistant Logic ----------------
            logging.info("🧠 Running assistant logic...")
            response = perform_action(transcript)
            logging.info(f"💬 Assistant response: {response}")

            # ---------------- TTS Output ----------------
            logging.info("🔊 Generating TTS audio...")
            tts_path = speak(response)
            logging.info(f"✅ TTS saved at {tts_path}")

            if tts_path:
                st.audio(tts_path, format="audio/mp3")

                # Optional: allow user to download
                with open(tts_path, "rb") as f:
                    st.download_button("🔽 Download Response Audio", f, file_name=os.path.basename(tts_path))

if __name__ == "__main__":
    main()
