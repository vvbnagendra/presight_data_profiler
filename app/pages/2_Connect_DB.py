# Directory: app/pages/2_Connect_DB.py
# DB connection logic

import streamlit as st
from utils.db_connector import get_sqlalchemy_engine
from utils.file_handler import save_connection
import sqlalchemy

st.title("🔌 Connect to Database")
db_type = st.selectbox("DB Type", ["PostgreSQL", "MySQL"])
host = st.text_input("Host", "localhost")
port = st.text_input("Port", "5432" if db_type == "PostgreSQL" else "3306")
user = st.text_input("Username")
password = st.text_input("Password", type="password")
db_name = st.text_input("Database Name")

if st.button("Connect"):
    try:
        engine = get_sqlalchemy_engine(db_type, host, port, user, password, db_name)
        engine.connect()
        st.session_state["engine"] = engine
        st.success(f"Connected to {db_name}!")
        save_connection(db_name, {
            "type": db_type,
            "host": host,
            "port": port,
            "user": user,
            "password": password
        })
    except Exception as e:
        st.error(f"Failed to connect: {e}")