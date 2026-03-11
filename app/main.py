# app/main.py
from pathlib import Path
import sys

# Asegura que el root del repo esté en PYTHONPATH (para poder importar src/)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from landing import router
from analysis_app import render_app

st.set_page_config(page_title="Football Vision Analytics", layout="wide")
router(render_app)