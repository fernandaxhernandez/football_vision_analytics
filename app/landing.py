# app/landing.py
# Landing Page + routing to analysis inside the SAME Streamlit app
# Copy/paste as-is. Assumes this file is inside your Streamlit app folder.
# It sets st.session_state["route"] = "app" when clicking "Start analysis".

import base64
from pathlib import Path
from tkinter import font
import streamlit as st


def render_landing():
    
    # Ensure route exists
    st.session_state.setdefault("route", "landing")

    # --- Logo as base64 (OK because it's small) ---
    logo_path = Path("assets\logo_white.png")
    logo_b64 = ""
    if logo_path.exists():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")

    # --- Video URL (Cloudinary or local static) ---
    hero_video_url = "https://res.cloudinary.com/dnsgamlxf/video/upload/v1773264555/video_football_hero_1_l1tifg.mp4"
    # If local: put at app/assets/hero_video.mp4 and use:
    # hero_video_url = str((Path(__file__).parent / "assets" / "hero_video.mp4").as_posix())

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap');

        /* Apply to *everything* Streamlit renders */
        html, body {{
          font-family: 'Montserrat', sans-serif !important;
        }}

        [data-testid="stAppViewContainer"] * {{
          font-family: 'Montserrat', sans-serif !important;
        }}

        /* Sidebar too */
        [data-testid="stSidebar"] * {{
          font-family: 'Montserrat', sans-serif !important;
        }}

        /* Inputs/buttons explicit (sometimes needed) */
        button, input, textarea, select {{
          font-family: 'Montserrat', sans-serif !important;
        }}
        :root{{
          --bg0: #06121a;
          --card: rgba(255,255,255,0.06);
          --stroke: rgba(255,255,255,0.12);
          --text: rgba(255,255,255,0.92);
          --muted: rgba(255,255,255,0.72);
          --accent1: rgba(223, 135, 79, 0.7);
          --accent2: rgba(159, 196, 53, 0.6);
          --radius: 18px;
        }}

        header[data-testid="stHeader"] {{ display: none; }}
        .block-container {{ padding-top: 0rem; padding-bottom: 0rem; max-width: 100%; }}

        /* Navbar */
        .topnav {{
            position: fixed;
            top: 0; left: 0; right: 0;
            z-index: 10000;
            padding: 20px 22px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(8, 12, 20, 0.55);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255,255,255,0.10);
        }}

        .navlinks a {{
            color: var(--muted);
            text-decoration: none;
            font-size: 16px;
            padding: 4px 8px;
            border-radius: 10px;
        }}
        .navlinks a:hover {{
            background: rgba(255,255,255,0.06);
            color: var(--text);
        }}

        .brand {{
            display:flex; align-items:center; gap: 10px;
            color: var(--text); font-weight: 800; letter-spacing: -0.02em;
            font-size: 17px;
        }}

        .brand-logo {{
            height: 80px;
            width: auto;
            display:block;
            padding-left: 20px;
            padding-right: 15px;
        }}

        .navlinks {{ display:flex; gap: 18px; color: var(--muted); font-size: 14px; }}
        .navlinks span {{ cursor: default; }}

        .nav-actions {{ display:flex; gap: 10px; align-items:center; }}
        .btn {{
            padding: 9px 14px; border-radius: 999px;
            border: 1px solid var(--stroke);
            background: var(--card);
            color: var(--text);
            font-weight: 650;
            font-size: 18px;
        }}
        .btn-primary {{
            border: none;
            background: linear-gradient(90deg, var(--accent1), var(--accent2));
        }}

        /* Hero with video background */
        .hero {{
            padding-top: 10vh;
            height: 95vh;
            position: relative;
            display:flex;
            align-items:center;
            justify-content:center;
            overflow: hidden;
            background: radial-gradient(circle at 20% 20%, rgba(238, 140, 85, 0.22), rgba(11,18,32,1));
        }}

        .hero-video {{
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          object-fit: cover;
          z-index: 0;
        }}

        .hero-overlay {{
          position: absolute;
          inset: 0;
          background: rgba(0,0,0,0.35);
          z-index: 1;
        }}

        .inner {{
          position: relative;
          z-index: 2;
          max-width: 980px;
          text-align:center;
          padding: 0 7vw;
          margin-top: 40px;
        }}

        .pill {{
            display:inline-flex; gap:10px; align-items:center;
            padding: 8px 14px;
            border-radius: 999px;
            border: 1px solid var(--stroke);
            background: var(--card);
            color: var(--text);
            font-size: 13px;
        }}

        .title {{
            margin: 18px 0 0 0;
            font-size: clamp(44px, 5.2vw, 76px);
            line-height: 1.02;
            font-weight: 850;
            letter-spacing: -0.04em;
            color: var(--text);
        }}

        .sub {{
            margin-top: 16px;
            font-size: 18px;
            line-height: 1.5;
            color: var(--muted);
            max-width: 820px;
            margin-left:auto; margin-right:auto;
        }}

        /* ---- Landing CTA: position Streamlit button block ---- */
        div[data-testid="stHorizontalBlock"]{{
          position: absolute;
          top: calc(50vh + 185px);
          left: 50%;
          transform: translateX(-50%);
          width: min(420px, 84vw);
          z-index: 3;
          background: transparent;
        }}

        /* --- Services section--- */
        .section {{
          padding: 120px 10vw;
          background: linear-gradient(180deg,
            rgba(255,255,255,0.00) 0%,
            rgba(255,255,255,0.02) 45%,
            rgba(255,255,255,0.00) 100%);
        }}

        .section-inner {{
          max-width: 1180px;
          margin: 0 auto;
        }}

        .services-hero {{
          display: grid;
          grid-template-columns: 1.2fr 0.8fr;
          gap: 40px;
          align-items: center;
          padding: 46px 46px;
          border-radius: 28px;
          border: 1px solid rgba(255,255,255,0.10);
          background:
            radial-gradient(1200px 700px at 10% 10%, rgba(223,135,79,0.16), rgba(0,0,0,0) 55%),
            radial-gradient(900px 600px at 90% 0%, rgba(159,196,53,0.14), rgba(0,0,0,0) 60%),
            rgba(255,255,255,0.02);
          box-shadow: 0 18px 60px rgba(0,0,0,0.40);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
        }}

        .services-title {{
          font-size: clamp(34px, 4.0vw, 56px);
          line-height: 1.08;
          letter-spacing: -0.03em;
          font-weight: 900;
          color: var(--text);
          margin: 0;
          max-width: 680px;
        }}

        .services-copy {{
          margin-top: 14px;
          color: var(--muted);
          font-size: 18px;
          line-height: 1.6;
          max-width: 720px;
        }}

        /* Responsive */
        @media (max-width: 980px) {{
          .services-hero {{
            grid-template-columns: 1fr;
            padding: 30px 26px;
          }}
        }}
        </style>

        <div class="topnav">
            <div class="brand">
              <img class="brand-logo" src="data:image/png;base64,{logo_b64}" />
              <span>Football Vision Analytics</span>
            </div>
            <div class="navlinks">
                <a href="#services">Services</a>
                <a href="#data">Data</a>
                <a href="#resources">Resources</a>
                <a href="#about">About</a>
            </div>
            <div class="nav-actions">
                <div class="btn">Login</div>
                <div class="btn btn-primary">Request a demo</div>
            </div>
        </div>

        <div class="hero">
          <video class="hero-video" autoplay muted loop playsinline preload="metadata">
            <source src="{hero_video_url}" type="video/mp4">
          </video>

          <div class="hero-overlay"></div>


        </div>

      
        """,
        unsafe_allow_html=True,
    )

    # CTA real (Streamlit button) centrado
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("Start analysis", type="primary", use_container_width=True, key="start_analysis_btn"):
            st.session_state["route"] = "app"
            st.rerun()


# ---------------------------
# OPTIONAL: minimal router you can paste in your main streamlit entrypoint (e.g., app/main.py)
# ---------------------------
def router(render_app_fn):
    """
    Usage:
      from landing import render_landing, router
      from analysis_app import render_app

      router(render_app)
    """
    st.session_state.setdefault("route", "landing")

    if st.session_state["route"] == "landing":
        render_landing()
    else:
        render_app_fn()