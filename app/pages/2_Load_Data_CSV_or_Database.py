import streamlit as st
import pandas as pd
from utils.db_connector import get_sqlalchemy_engine
from utils.file_handler import save_connection, load_connections

st.title("📂 Load Data: CSV or Database")

# Option to select data source
data_source = st.radio("Select Data Source:", ["Upload CSV", "Connect to Database"])

if data_source == "Upload CSV":
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state["df"] = df
            st.session_state["uploaded_file_name"] = uploaded_file.name
            st.success("✅ CSV file loaded successfully!")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {e}")

else:
    # Load previously saved connections
    saved_connections = load_connections()
    saved_names = list(saved_connections.keys())

    # Option to select or create a new connection
    connection_name = st.selectbox("Use saved connection or create new", ["New Connection"] + saved_names)

    if connection_name == "New Connection":
        db_type = st.selectbox("DB Type", ["PostgreSQL", "MySQL"])
        host = st.text_input("Host", "localhost")
        port = st.text_input("Port", "5432" if db_type == "PostgreSQL" else "3306")
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        db_name = st.text_input("Database Name")
        label = st.text_input("Save this connection as (label)", "")

        if st.button("Connect"):
            try:
                engine = get_sqlalchemy_engine(db_type, host, port, user, password, db_name)
                engine.connect()
                st.session_state["engine"] = engine
                st.success(f"✅ Connected to {db_name}!")

                if label:
                    save_connection(label, {
                        "type": db_type,
                        "host": host,
                        "port": port,
                        "user": user,
                        "password": password,
                        "db_name": db_name
                    })
            except Exception as e:
                st.error(f"❌ Failed to connect: {e}")

    else:
        conn_info = saved_connections[connection_name]
        try:
            engine = get_sqlalchemy_engine(
                conn_info["type"],
                conn_info["host"],
                conn_info["port"],
                conn_info["user"],
                conn_info["password"],
                conn_info["db_name"]
            )
            engine.connect()
            st.session_state["engine"] = engine
            st.success(f"✅ Connected to {conn_info['db_name']} using saved connection!")
        except Exception as e:
            st.error(f"❌ Failed to connect: {e}")
