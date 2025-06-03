# Directory: app/pages/4_Chat_with_Data.py
# LLM-based data chat

import streamlit as st
import pandas as pd
from data_quality.pandasai_chat import get_smart_df
from sqlalchemy import inspect

st.title("💬 Chat with Data")

if "engine" not in st.session_state:
    st.warning("Please connect to a database first.")
else:
    engine = st.session_state["engine"]
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    table = st.selectbox("Select table to chat with", tables)

    if table:
        df = pd.read_sql(f"SELECT * FROM {table} LIMIT 1000", engine)
        user_query = st.text_input("Ask a question:")
        if user_query:
            smart_df = get_smart_df(df)
            try:
                print("Buchiki2")
                response = smart_df.chat(user_query)
                st.markdown(f"**🧠 Response:** {response}")
            except Exception as e:
                st.error(f"Error: {e}")


