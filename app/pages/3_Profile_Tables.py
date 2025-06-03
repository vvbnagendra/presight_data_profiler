# Directory: app/pages/3_Profile_Tables.py
# Table selector + visual profile

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import inspect
from data_quality.quality_checks import run_quality_checks
from data_quality.profiler import generate_profile
from data_quality.convert_dates import convert_dates

st.title("📊 Profile Tables")

if "engine" not in st.session_state:
    st.warning("Connect to a database first in 'Connect DB' page.")
else:
    engine = st.session_state["engine"]
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    selected_tables = st.multiselect("Choose tables to profile", tables)

    for table in selected_tables:
        st.subheader(f"🔍 {table}")
        df = pd.read_sql(f"SELECT * FROM {table} LIMIT 1000", engine)
        st.dataframe(df.head())

        df = convert_dates(df)

        st.dataframe(df.head())

        st.markdown("**📈 Visuals:**")
        for col in df.select_dtypes("number"):
            st.plotly_chart(px.histogram(df, x=col, title=f"Distribution of {col}"), use_container_width=True)

        st.markdown("**✅ Quality Checks:**")
        st.json(run_quality_checks(df))

        file_name = table
        report_path = f"app/outputs/{file_name}.html"

        st.markdown("📈 Profiling Report")
        profile = generate_profile(df)
        profile.to_file(report_path)
        st.success("Profiling report saved to {}".format(report_path))
        with open(report_path, "rb") as f:
            st.download_button("Download Report", f, f"{file_name}.html","text/html")