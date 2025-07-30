import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
import av
import soundfile as sf
import tempfile
import os, time
import numpy as np
import logging
import wave
import shutil

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
    def __init__(self):
        self.frames = []
        self.sample_rate = None

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray()  # shape: (channels, samples)
        self.sample_rate = frame.sample_rate
        # Convert to mono by averaging channels if stereo
        if pcm.shape[0] > 1:
            pcm = np.mean(pcm, axis=0, dtype=np.int16, keepdims=True)
        self.frames.append(pcm)
        return frame



def main():
    st.write("🎤 Press **Start Listening** to begin and **Stop & Process** to get response.")

    st.set_page_config(page_title="Tasky Voice AI", page_icon="🎤")
    st.title("🎙️ TaskyAI Voice Assistant")

    # 🔐 API Key Input
    if "groq_api_key" not in st.session_state:
        st.session_state.groq_api_key = ""

    st.session_state.groq_api_key = st.text_input(
        "🔑 Enter your Groq API Key",
        type="password",
        value=st.session_state.groq_api_key,
        placeholder="Enter your Groq API key...",
    )

    if st.checkbox("📄 Show transcript and response"):
        st.markdown(f"**Transcript:** {transcript}")
        st.markdown(f"**Response:** {response}")


    if not st.session_state.groq_api_key:
        st.warning("Please enter your Groq API key to continue.")
        return

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
            async_processing=True,  # Enable this
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
            # (1, samples) → flatten to (samples,)
            stacked = np.concatenate(processor.frames, axis=1).flatten()

            # Normalize volume
            stacked = (stacked / np.max(np.abs(stacked))) * 32767
            stacked = stacked.astype(np.int16)

            sf.write(temp_wav.name, stacked, samplerate=processor.sample_rate, subtype='PCM_16')
            logging.info(f"✅ Audio saved to {temp_wav.name}")

            st.audio(temp_wav.name, format="audio/wav")
            shutil.copy(temp_wav.name, f"debug_audio/{time.time()}.wav")

            # Add this after saving the WAV file

            def log_audio_details(filepath):
                with wave.open(filepath, 'rb') as wf:
                    logging.info(f"📊 Channels: {wf.getnchannels()}")
                    logging.info(f"📊 Sample Width: {wf.getsampwidth()}")
                    logging.info(f"📊 Frame Rate: {wf.getframerate()}")
                    logging.info(f"📊 Frame Count: {wf.getnframes()}")
                    logging.info(f"📊 Duration: {wf.getnframes() / wf.getframerate():.2f} seconds")

            log_audio_details(temp_wav.name)


            # ---------------- Whisper Transcription ----------------
            logging.info("🔠 Transcribing with Whisper...")
            # transcript = transcribe_audio(temp_wav.name)
            transcript = transcribe_audio(temp_wav.name)
            logging.info(f"📝 Transcript: {transcript}")

            # ---------------- Assistant Logic ----------------
            logging.info("🧠 Running assistant logic...")
            response = perform_action(transcript, api_key=st.session_state.groq_api_key)
            logging.info(f"💬 Assistant response: {response}")

            # ---------------- TTS Output ----------------
            logging.info("🔊 Generating TTS audio...")
            tts_path = speak(response)
            logging.info(f"✅ TTS saved at {tts_path}")

            if tts_path and os.path.exists(tts_path):
                st.audio(tts_path, format="audio/mp3")

                with open(tts_path, "rb") as f:
                    st.download_button("🔽 Download Response Audio", f, file_name=os.path.basename(tts_path))
            else:
                st.error("TTS generation failed or file not found.")


if __name__ == "__main__":
    main()
