# Directory: app/main.py
# App launcher

import streamlit as st

st.set_page_config(page_title="Smart Data Profiler", layout="wide")
st.image("app/assets/logo.png", width=100)
st.title("🧠 Smart Data Profiler")
st.markdown("Use the sidebar to navigate: Connect to your DB, Profile Tables, and Chat with Data.")
# st.title("🏠 Home")
# st.markdown("Welcome to the Smart Data Profiler. Start by connecting to your database.")