# app/analysis_app.py
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.run_analysis import run_analysis
import streamlit as st

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap');

    html, body {
      font-family: 'Montserrat', sans-serif !important;
    }

    [data-testid="stAppViewContainer"] * {
      font-family: 'Montserrat', sans-serif !important;
    }

    [data-testid="stSidebar"] * {
      font-family: 'Montserrat', sans-serif !important;
    }

    button, input, textarea, select {
      font-family: 'Montserrat', sans-serif !important;
    }
    </style>
    """, unsafe_allow_html=True)

def render_app():
    inject_css()
    st.title("Football Vision Analytics")
    st.caption("Upload a clip and render the overlay (teams + possession).")

    with st.sidebar:
        st.header("Inputs")
        annotated_json = st.text_input(
            "Annotated JSON (Paula)",
            value="outputs/tracks_annotated_paula.json",
            help="Debe existir. (Generado por match_analysis.run_paula_pipeline)",
        )

        st.divider()
        if st.button("Back to landing", use_container_width=True):
            st.session_state["route"] = "landing"
            st.rerun()

    uploaded = st.file_uploader("Upload a video (.mp4)", type=["mp4"])

    if not uploaded:
        st.info("Sube un video para empezar.")
        return

    # Save uploaded file
    uploads_dir = Path("outputs/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    video_path = uploads_dir / uploaded.name
    with open(video_path, "wb") as f:
        f.write(uploaded.getbuffer())

    st.success(f"Video guardado en: {video_path}")
    st.video(str(video_path))

    json_path = Path(annotated_json)
    if not json_path.exists():
        st.error(f"No encuentro el JSON anotado: {json_path}")
        st.stop()

    col1, col2 = st.columns([1, 1])
    with col1:
        run = st.button("Run overlay", type="primary", use_container_width=True)
    with col2:
        st.write("")  # espacio

    if run:
        with st.spinner("Rendering overlay..."):
            out_video = run_analysis(video_path, json_path)

        st.success("✅ Overlay listo")
        st.video(str(out_video))

        with open(out_video, "rb") as f:
            st.download_button(
                "Download overlay video",
                data=f,
                file_name=out_video.name,
                mime="video/mp4",
                use_container_width=True,
            )