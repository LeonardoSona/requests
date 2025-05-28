import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="IHD Request Management", layout="wide")

# Initialize session state
if "requests" not in st.session_state:
    st.session_state.requests = pd.DataFrame()

# Import Excel
def show_import_export():
    st.subheader("📥 Upload Excel File")
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            df = df.astype(str)
            st.session_state.requests = df.copy()
            st.success("✅ File uploaded and data loaded!")
            st.dataframe(df.head(), use_container_width=True)
        except Exception as e:
            st.error(f"Failed to load Excel file: {str(e)}")

# Dashboard
def show_dashboard():
    st.subheader("📊 Dashboard")
    df = st.session_state.requests
    if df.empty or "REQUEST_ID" not in df.columns:
        st.info("No request data available.")
        return

    total_requests = len(df["REQUEST_ID"].dropna().unique())
    total_datasets = len(df["DATASET_ID"].dropna().unique()) if "DATASET_ID" in df.columns else 0
    approved = len(df[df["REQUEST_STATUS"] == "Approved"]) if "REQUEST_STATUS" in df.columns else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Requests", total_requests)
    col2.metric("Approved Requests", approved)
    col3.metric("Total Datasets", total_datasets)

    if "REQUEST_STATUS" in df.columns:
        status_counts = df["REQUEST_STATUS"].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Request Status Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

    if "DATE_REQUEST_RECEIVED_X" in df.columns:
        df["DATE_REQUEST_RECEIVED_X"] = pd.to_datetime(df["DATE_REQUEST_RECEIVED_X"], errors="coerce")
        timeline = df.groupby(df["DATE_REQUEST_RECEIVED_X"].dt.to_period("M")).size()
        fig = px.line(
            x=timeline.index.astype(str),
            y=timeline.values,
            labels={"x": "Month", "y": "Request Count"},
            title="Monthly Request Trends"
        )
        st.plotly_chart(fig, use_container_width=True)

# Request Form Editor
def show_request_form_editor():
    st.subheader("📝 Request Form Editor")

    df = st.session_state.requests.copy()
    if df.empty or "REQUEST_ID" not in df.columns:
        st.warning("No request data available.")
        return

    unique_requests = df["REQUEST_ID"].dropna().unique().tolist()
    selected_id = st.selectbox("Select Request ID", unique_requests)

    req_df = df[df["REQUEST_ID"] == selected_id].copy()
    if req_df.empty:
        st.info("No data found for this Request ID.")
        return

    request_row = req_df.iloc[0].copy()

    st.markdown("### 🧩 Select Request Columns to View/Edit")
    request_columns = st.multiselect(
        "Pick request-level columns",
        options=req_df.columns.tolist(),
        default=["REQUEST_ID", "NAME", "EMAIL", "REQUEST_STATUS"]
    )

    if request_columns:
        st.markdown("### ✏️ Request Details")
        edited_request = st.data_editor(
            req_df[request_columns].copy(),
            use_container_width=True,
            num_rows="dynamic"
        )

        if st.button("💾 Save Request Changes"):
            for idx, row in edited_request.iterrows():
                mask = (st.session_state.requests["REQUEST_ID"] == row["REQUEST_ID"])
                for col in request_columns:
                    st.session_state.requests.loc[mask, col] = row[col]
            st.success("✅ Request data updated.")

    st.markdown("### 🧩 Select Dataset Columns to View/Edit")
    if "DATASET_ID" in req_df.columns:
        dataset_columns = st.multiselect(
            "Pick dataset-level columns",
            options=req_df.columns.tolist(),
            default=["DATASET_ID", "DATASET_NAME", "DATASET_STATUS"]
        )

        if dataset_columns:
            st.markdown("### 📄 Associated Datasets")
            edited_datasets = st.data_editor(
                req_df[dataset_columns].copy(),
                use_container_width=True,
                num_rows="dynamic"
            )

            if st.button("💾 Save Dataset Changes"):
                for idx, row in edited_datasets.iterrows():
                    mask = (st.session_state.requests["REQUEST_ID"] == selected_id) & (
                        st.session_state.requests["DATASET_ID"] == row["DATASET_ID"]
                    )
                    for col in dataset_columns:
                        st.session_state.requests.loc[mask, col] = row[col]
                st.success("✅ Dataset data updated.")
    else:
        st.info("No dataset info available for this request.")

# App Tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Request Form Editor", "📥 Import Excel"])
with tab1:
    show_dashboard()
with tab2:
    show_request_form_editor()
with tab3:
    show_import_export()
