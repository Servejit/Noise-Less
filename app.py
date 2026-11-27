import subprocess
import tempfile
from pathlib import Path

import noisereduce as nr
import numpy as np
import soundfile as sf
import streamlit as st


st.set_page_config(page_title="Noise Less | Video Audio Cleaner", page_icon="🎙️", layout="centered")

st.markdown("""
<style>
.stApp { background: linear-gradient(145deg, #fff7ef 0%, #ffffff 65%); }
h1, h2, h3 { color: #b85c38; }
div.stButton > button, div.stDownloadButton > button {
    background: #f4c7ab; color: #542b1b; border: 1px solid #e8ad8b;
    border-radius: 12px; font-weight: 600;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
    background: #edb18e; color: #542b1b;
}
</style>
""", unsafe_allow_html=True)

st.title("🎙️ Noise Less")
st.subheader("Make your recorded videos sound clearer")
st.write("Reduce steady background noise, traffic, fan sounds, and other unwanted noise from your video's audio.")

st.warning(
    "This starter version reduces general background noise. It cannot reliably erase "
    "a specific nearby speaker, TV music, or barking while perfectly preserving your voice. "
    "That needs a voice-separation model in a later version."
)

upload = st.file_uploader("Choose a video", type=["mp4", "mov", "avi", "mkv", "webm"])
strength = st.slider(
    "Noise reduction strength", min_value=0.10, max_value=1.00,
    value=0.70, step=0.05,
    help="Higher settings suppress more noise but can make speech sound artificial."
)

if upload:
    video_data = upload.getvalue()
    st.video(video_data)

    if st.button("✨ Clean video audio", use_container_width=True):
        with st.spinner("Extracting and cleaning audio… Keep this page open."):
            try:
                suffix = Path(upload.name).suffix or ".mp4"
                with tempfile.TemporaryDirectory() as folder:
                    folder = Path(folder)
                    source = folder / ("source" + suffix)
                    audio_in = folder / "audio_in.wav"
                    audio_out = folder / "audio_clean.wav"
                    video_out = folder / "noise_less_video.mp4"
                    source.write_bytes(video_data)

                    extract = subprocess.run(
                        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                         "-i", str(source), "-vn", "-ac", "1", "-ar", "16000",
                         "-c:a", "pcm_s16le", str(audio_in)],
                        capture_output=True, text=True
                    )
                    if extract.returncode:
                        raise RuntimeError("Audio extraction failed. Check that the video has an audio track.")

                    samples, rate = sf.read(audio_in, dtype="float32")
                    if samples.size == 0:
                        raise RuntimeError("The video audio track is empty.")

                    cleaned = nr.reduce_noise(
                        y=samples, sr=rate, stationary=False, prop_decrease=float(strength)
                    )
                    cleaned = np.nan_to_num(cleaned)
                    peak = float(np.max(np.abs(cleaned))) if cleaned.size else 0.0
                    if peak > 0:
                        cleaned = cleaned * (0.95 / peak)
                    sf.write(audio_out, cleaned, rate, subtype="PCM_16")

                    mux = subprocess.run(
                        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                         "-i", str(source), "-i", str(audio_out),
                         "-map", "0:v:0", "-map", "1:a:0",
                         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                         "-shortest", "-movflags", "+faststart", str(video_out)],
                        capture_output=True, text=True
                    )
                    if mux.returncode:
                        raise RuntimeError("Could not export the cleaned video.")

                    result_video = video_out.read_bytes()
                    result_audio = audio_out.read_bytes()

                st.success("Audio cleaning finished!")
                st.subheader("Cleaned audio preview")
                st.audio(result_audio)
                st.subheader("Cleaned video preview")
                st.video(result_video)
                st.download_button(
                    "⬇️ Download cleaned MP4", data=result_video,
                    file_name="noise_less_cleaned.mp4", mime="video/mp4",
                    use_container_width=True
                )

            except FileNotFoundError:
                st.error("FFmpeg is missing. Confirm that packages.txt contains: ffmpeg")
            except Exception as exc:
                st.error(f"Could not process this video: {exc}")
                st.caption("Try a short MP4 or MOV video with a normal audio track.")

st.divider()
st.caption("Noise Less • Python + Streamlit • First working version")
