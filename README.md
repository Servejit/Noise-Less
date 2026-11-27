# Noise Less

An open-source Streamlit video audio-enhancement app.

## Processing engine

- **DeepFilterNet3**: neural speech enhancement to reduce background noise while preserving speech.
- **FFmpeg**: extracts the audio and muxes the enhanced audio back into the original video while copying the original video stream.
- No paid API keys or external inference API are used.

## Deploy on Streamlit Community Cloud

Repository: `Servejit/Noise-Less`  
Branch: `main`  
Main file: `app.py`

The app uses Python 3.11. Install dependencies from `requirements.txt` and Linux packages from `packages.txt`.

## Usage

1. Upload a short MP4/MOV video (maximum 100 MB).
2. Select **Enhance voice and clean video**.
3. Wait for the model to enhance speech and FFmpeg to rebuild the video.
4. Preview and download the result.

The first run can take longer because DeepFilterNet downloads its pretrained model.

## Limitations

- The app is designed for speech enhancement, not perfect separation of each sound source.
- Overlapping TV speech, loud music, barking, and other complex sounds may remain.
- Streamlit Community Cloud has limited CPU/RAM. Short videos are recommended.
- This repository does not use Demucs yet: its music-source separation models are substantially heavier and would risk exhausting the free Streamlit server. It can be evaluated as a separate optional workflow if hosting resources permit.

## License

This app code is provided as open source. DeepFilterNet and FFmpeg retain their own upstream licenses.
