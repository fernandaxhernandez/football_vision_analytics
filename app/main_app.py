import os
import subprocess
from pathlib import Path

import streamlit as st
from landing import router
from analysis_app import render_app  # <-- your analysis page function

router(render_app)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_VIDEOS_DIR = PROJECT_ROOT / "outputs" / "videos"
RUNS_DIR = PROJECT_ROOT / "outputs" / "runs"

st.set_page_config(page_title="Football Vision Analytics", layout="wide")
st.title("Football Vision Analytics")

OUTPUT_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)

uploaded = st.file_uploader("Upload a video (.mp4)", type=["mp4"])

model_name = st.text_input("Model (Ultralytics name or path)", value="yolov8n.pt")
conf = st.slider("Confidence threshold", 0.05, 0.90, 0.25, 0.05)

if uploaded:
    save_path = OUTPUT_VIDEOS_DIR / uploaded.name
    with open(save_path, "wb") as f:
        f.write(uploaded.getbuffer())

    st.success(f"Saved to: {save_path}")
    st.video(str(save_path))

    if st.button("Run inference"):
        # Use Ultralytics CLI to avoid Python import issues
        cmd = [
            "yolo",
            "task=detect",
            "mode=predict",
            f"model={model_name}",
            f"source={str(save_path)}",
            f"conf={conf}",
            "save=True",
            "project=" + str(RUNS_DIR),
            "name=predict",
        ]

        st.write("Running command:")
        st.code(" ".join(cmd))

        try:
            subprocess.run(cmd, check=True)
            st.success("Inference finished ✅")
        except subprocess.CalledProcessError as e:
            st.error("Inference failed ❌")
            st.exception(e)

        # Ultralytics saves outputs in: project/name/
        pred_dir = RUNS_DIR / "predict"
        st.write("Output folder:", str(pred_dir))

        # Try to find the produced video
        out_mp4 = None
        if pred_dir.exists():
            mp4s = list(pred_dir.rglob("*.mp4"))
            if mp4s:
                out_mp4 = mp4s[0]

        if out_mp4:
            st.subheader("Output video")
            st.video(str(out_mp4))
        else:
            st.warning("No output .mp4 found yet. Check the output folder.")