import streamlit as st

def render_app():
    st.title("Analysis")
    st.write("Upload video here, run YOLO, show outputs...")
    if st.button("Back to landing"):
        st.session_state["route"] = "landing"
        st.rerun()