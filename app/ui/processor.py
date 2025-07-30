from streamlit_webrtc import AudioProcessorBase
import av

class AudioRecorder(AudioProcessorBase):
    def __init__(self) -> None:
        self.frames = []
        self.sample_rate = None

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray()
        self.sample_rate = frame.sample_rate
        self.frames.append(pcm.T)
        return frame
