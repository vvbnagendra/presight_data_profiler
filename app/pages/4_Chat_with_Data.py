# Directory: app/pages/4_Chat_with_Data.py
# LLM-based data chat with CSV or DB

import streamlit as st
import pandas as pd
from data_quality.pandasai_chat import get_smart_df
from sqlalchemy import inspect

st.title("💬 Chat with Data")

data_sources = {}

# --- 1. From Uploaded CSV ---
if "df" in st.session_state:
    data_sources["Uploaded CSV"] = st.session_state["df"]

# --- 2. From DB Tables ---
if "engine" in st.session_state:
    engine = st.session_state["engine"]
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    for table in tables:
        try:
            df = pd.read_sql(f"SELECT * FROM {table} LIMIT 1000", engine)
            data_sources[f"DB Table: {table}"] = df
        except Exception as e:
            st.error(f"❌ Could not load table {table}: {e}")

# --- 3. If nothing available ---
if not data_sources:
    st.warning("Please upload a CSV or connect to a database to start chatting.")
    st.stop()

# --- 4. Choose Source ---
selected_source = st.selectbox("Choose a data source to chat with", list(data_sources.keys()))
df = data_sources[selected_source]
st.dataframe(df.head())

# --- 5. Ask Question ---
user_query = st.text_input("Ask a question about this data:")
if user_query:
    smart_df = get_smart_df(df)
    try:
        response = smart_df.chat(user_query)
        st.markdown(f"🧠 Response:** {response}")
    except Exception as e:
        st.error(f"❌ Error: {e}")