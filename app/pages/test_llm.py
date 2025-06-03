# Directory: app/pages/4_Chat_with_Data.py
# LLM-based data chat

import pandas as pd
from data_quality.pandasai_chat import get_smart_df
import psycopg2
import streamlit as st


st.title("💬 Chat with")

conn = psycopg2.connect(
    dbname='testdb',
    user='testuser',
    password='testpass',
    host='localhost',
    port=5432
)

df = pd.read_sql('SELECT * FROM users', conn)
conn.close()

st.dataframe(df.head())

smart_df = get_smart_df(df)
# st.dataframe(smart_df.head())
response = smart_df.chat('how many records are there?')
st.markdown(f"**🧠 Response:** {response}")