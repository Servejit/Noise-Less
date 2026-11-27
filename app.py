import shutil
import subprocess
import tempfile
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Noise Less | AI Voice Cleaner",
    page_icon="🎙️",
    layout="centered",
)

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
st.subheader("AI voice enhancement for your videos")
st.write(
    "Reduce unwanted background noise and make speech clearer using "
    "the open-source DeepFilterNet speech-enhancement model."
)

st.info(
    "This version uses AI speech enhancement. It is designed to preserve speech "
    "while reducing noise, but it cannot guarantee perfect removal of every "
    "TV voice, song, bus sound, or dog bark. Loud overlapping voices may remain."
)

MAX_VIDEO_MB = 100
upload = st.file_uploader(
    "Choose a video",
    type=["mp4", "mov", "avi", "mkv", "webm"],
    help=f"For the free hosting environment, use videos smaller than {MAX_VIDEO_MB} MB.",
)

st.caption("Best first test: a short video (10–60 seconds) with speech and background noise.")

if upload is not None:
    if upload.size > MAX_VIDEO_MB * 1024 * 1024:
        st.error(f"Please upload a video smaller than {MAX_VIDEO_MB} MB.")
        st.stop()

    st.video(upload.getvalue())

    if st.button("✨ Enhance voice and clean video", use_container_width=True):
        ffmpeg = shutil.which("ffmpeg")
        deepfilter = shutil.which("deepFilter")

        if not ffmpeg:
            st.error("FFmpeg is not installed. Check that packages.txt contains ffmpeg.")
            st.stop()
        if not deepfilter:
            st.error(
                "DeepFilterNet did not install correctly. Open Manage app → Logs "
                "and share the dependency installation error."
            )
            st.stop()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                work = Path(temp_dir)
                source = work / ("source" + (Path(upload.name).suffix or ".mp4"))
                audio_input = work / "voice_input.wav"
                enhanced_dir = work / "enhanced"
                enhanced_dir.mkdir()
                video_output = work / "noise_less_cleaned.mp4"

                # Write upload to disk rather than making extra in-memory copies.
                with source.open("wb") as output_file:
                    output_file.write(upload.getbuffer())

                progress = st.progress(5, text="Extracting the original audio…")

                extract = subprocess.run(
                    [
                        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                        "-i", str(source), "-vn", "-ac", "1", "-ar", "48000",
                        "-c:a", "pcm_s16le", str(audio_input),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                if extract.returncode != 0 or not audio_input.exists():
                    detail = (extract.stderr or "No audio track was found.")[-1200:]
                    raise RuntimeError(f"Could not extract audio. {detail}")

                progress.progress(25, text="AI is enhancing speech. First run may take longer while the model downloads…")

                # DeepFilterNet3 command-line interface. The model is downloaded
                # and cached by DeepFilterNet on first use.
                enhance = subprocess.run(
                    [
                        deepfilter, "--pf", "--model-base-dir", "DeepFilterNet3",
                        "--output-dir", str(enhanced_dir),
                        "--log-level", "error", str(audio_input),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=900,
                )

                if enhance.returncode != 0:
                    detail = (enhance.stderr or enhance.stdout or "Unknown DeepFilterNet error.")[-1800:]
                    raise RuntimeError(f"AI speech enhancement failed. {detail}")

                candidates = list(enhanced_dir.glob("*.wav"))
                if not candidates:
                    # Some CLI builds write the enhanced WAV beside the input.
                    candidates = [
                        p for p in work.glob("*.wav")
                        if p != audio_input
                    ]
                if not candidates:
                    raise RuntimeError("DeepFilterNet finished but no enhanced WAV file was created.")

                enhanced_audio = candidates[0]
                progress.progress(70, text="Combining enhanced audio with the original video…")

                mux = subprocess.run(
                    [
                        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                        "-i", str(source), "-i", str(enhanced_audio),
                        "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-map_metadata", "0", "-shortest",
                        "-movflags", "+faststart", str(video_output),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if mux.returncode != 0 or not video_output.exists():
                    detail = (mux.stderr or "Video export failed.")[-1200:]
                    raise RuntimeError(f"Could not create the cleaned video. {detail}")

                progress.progress(90, text="Preparing your download…")
                # Keep the final result only; do not retain intermediate WAVs.
                result_size = video_output.stat().st_size
                if result_size > 150 * 1024 * 1024:
                    raise RuntimeError("The cleaned video is too large for this free app to prepare safely. Try a shorter or smaller video.")

                result_video = video_output.read_bytes()
                progress.progress(100, text="Finished!")

            st.success("Your video audio has been enhanced.")
            st.video(result_video)
            st.download_button(
                "⬇️ Download cleaned video",
                data=result_video,
                file_name="noise_less_cleaned.mp4",
                mime="video/mp4",
                use_container_width=True,
            )

        except subprocess.TimeoutExpired:
            st.error("Processing took longer than the free server allows. Try a shorter video.")
        except Exception as exc:
            st.error(f"Could not process this video: {exc}")
            st.caption("If the error mentions model download or DeepFilterNet, share the latest Manage app logs.")

st.divider()
st.caption("Noise Less • DeepFilterNet3 + FFmpeg • Open-source processing")
