# Directory: app/pages/3_Profile_Tables.py
# Profile CSV or DB Tables visually and via quality checks

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import inspect
from data_quality.quality_checks import run_quality_checks
from data_quality.profiler import generate_profile
from data_quality.convert_dates import convert_dates

st.title("📊 Profile Tables")

df_sources = []  # To hold dataframes from CSV or DB
uploaded_file_name = None

# --- 1. Check for uploaded CSV(s) ---
if "df" in st.session_state:
    df_sources.append(("Uploaded CSV", st.session_state["df"]))
    uploaded_file_name = st.session_state.get("uploaded_file_name")

# --- 2. Check for connected database ---
if "engine" in st.session_state:
    engine = st.session_state["engine"]
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    selected_tables = st.multiselect("Choose DB tables to profile", tables)

    for table in selected_tables:
        try:
            df = pd.read_sql(f"SELECT * FROM {table} LIMIT 1000", engine)
            df_sources.append((f"DB Table: {table}", df))
        except Exception as e:
            st.error(f"❌ Could not load table {table}: {e}")

# --- 3. If no data ---
if not df_sources:
    st.warning("Upload a CSV or connect to a database and select tables to continue.")
    st.stop()

# --- 4. Profile each DataFrame ---
for source_name, df in df_sources:

    # Set base name for report
    if source_name == "Uploaded CSV" and uploaded_file_name is not None:
        base_name = uploaded_file_name
    elif source_name.startswith("DB Table"):
        base_name = source_name.split(":")[-1].strip()
    else:
        base_name = "unknown"

    # Display source information
    st.subheader(f"🔍 {source_name}")
    st.subheader(uploaded_file_name)
    st.dataframe(df.head())

    # Convert date columns
    df = convert_dates(df)


    file_name = source_name.replace(" ", "_").replace(":", "") + "_" + base_name
    report_path = f"app/outputs/{file_name}.html"

    # Clean DataFrame before profiling
    df_cleaned = df.copy()
    df_cleaned.dropna(axis=1, how="all", inplace=True)
    df_cleaned.replace([float("inf"), float("-inf")], pd.NA, inplace=True)
    df_cleaned.dropna(axis=0, how="any", inplace=True)

    try:
        # Generate profile
        profile = generate_profile(df_cleaned)

        # Get overview data
        description = profile.get_description()
        overview = None

        # Handle old and new versions
        try:
            if hasattr(description, "table"):
                overview = description.table  # v4.x
            elif isinstance(description, dict) and "table" in description:
                overview = description["table"]  # v3.x

            if overview:
                st.markdown("### 📋 Overview Summary")
                st.markdown(f"- **Rows**: {overview.n if hasattr(overview, 'n') else overview['n']}  \n"
                            f"- **Columns**: {overview.n_var if hasattr(overview, 'n_var') else overview['n_var']}  \n"
                            f"- **Missing cells**: {overview.n_cells_missing if hasattr(overview, 'n_cells_missing') else overview['n_cells_missing']}  \n"
                            f"- **Duplicate rows**: {overview.n_duplicates if hasattr(overview, 'n_duplicates') else overview['n_duplicates']}")

                types = overview.types if hasattr(overview, "types") else overview["types"]
                st.markdown("**Data Types:**")
                for dtype, count in types.items():
                    st.markdown(f"- {dtype}: {count}")
            else:
                st.warning("⚠️ Overview not available.")
        except Exception as e:
            st.warning(f"⚠️ Profiling summary failed: {e}")

        # Run quality checks
        st.markdown("✅ Quality Checks:")
        st.json(run_quality_checks(df))

        # Save profiling report
        profile.to_file(report_path)
        st.success(f"Profiling report saved to `{report_path}`")

        with open(report_path, "rb") as f:
            st.download_button("📥 Download Full HTML Report", f, f"{file_name}.html", "text/html")

    except Exception as e:
        st.error(f"⚠️ Profiling failed: {e}")

    # Show distribution charts
    st.markdown("📈 Visuals:")
    for col in df.select_dtypes("number"):
        st.plotly_chart(px.histogram(df, x=col, title=f"Distribution of {col}"), use_container_width=True)

