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

    df["DATE_REQUEST_RECEIVED_X"] = pd.to_datetime(df["DATE_REQUEST_RECEIVED_X"], errors="coerce")
    df["DATE_ACCESS_GRANTED_X"] = pd.to_datetime(df["DATE_ACCESS_GRANTED_X"], errors="coerce")
    df["TIME_TO_APPROVAL"] = (df["DATE_ACCESS_GRANTED_X"] - df["DATE_REQUEST_RECEIVED_X"]).dt.days

    total_requests = len(df["REQUEST_ID"].dropna().unique())
    total_datasets = len(df["DATASET_ID"].dropna().unique()) if "DATASET_ID" in df.columns else 0
    approved = len(df[df["REQUEST_STATUS"] == "Approved"]) if "REQUEST_STATUS" in df.columns else 0
    avg_time = df["TIME_TO_APPROVAL"].mean()
    overdue_count = ((df["REQUEST_STATUS"] != "Approved") &
                     ((pd.Timestamp.now() - df["DATE_REQUEST_RECEIVED_X"]).dt.days > 90)).sum()
    dataset_summary = df["DATASET_STATUS"].value_counts() if "DATASET_STATUS" in df.columns else pd.Series()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Requests", total_requests)
    col2.metric("Approved Requests", approved)
    col3.metric("Overdue Requests", int(overdue_count))
    col4.metric("Avg. Time to Approval", f"{avg_time:.1f} days" if pd.notnull(avg_time) else "N/A")

    if "REQUEST_STATUS" in df.columns:
        status_counts = df["REQUEST_STATUS"].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Request Status Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

    if "DATE_REQUEST_RECEIVED_X" in df.columns:
        timeline = df.groupby(df["DATE_REQUEST_RECEIVED_X"].dt.to_period("M")).size()
        fig = px.line(
            x=timeline.index.astype(str),
            y=timeline.values,
            labels={"x": "Month", "y": "Request Count"},
            title="Monthly Request Trends"
        )
        st.plotly_chart(fig, use_container_width=True)

    if not dataset_summary.empty:
        st.subheader("📦 Dataset Status Summary")
        st.plotly_chart(
            px.pie(
                names=dataset_summary.index,
                values=dataset_summary.values,
                title="Dataset Status Distribution"
            ),
            use_container_width=True
        )

# View/Edit Requests
def show_view_requests():
    st.subheader("📋 View & Edit Requests")

    df = st.session_state.requests.copy()
    if df.empty:
        st.warning("No data available. Please upload a file.")
        return

    with st.expander("🔍 Advanced Filters", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        request_id_filter = col1.text_input("Filter by REQUEST_ID")
        dataset_id_filter = col2.text_input("Filter by DATASET_ID")
        request_status_filter = col3.text_input("Filter by REQUEST_STATUS")
        dataset_status_filter = col4.text_input("Filter by DATASET_STATUS")

    filtered_df = df.copy()
    if request_id_filter:
        filtered_df = filtered_df[
            filtered_df["REQUEST_ID"].astype(str).str.contains(request_id_filter, case=False, na=False)
        ]
    if dataset_id_filter and "DATASET_ID" in df.columns:
        filtered_df = filtered_df[
            filtered_df["DATASET_ID"].astype(str).str.contains(dataset_id_filter, case=False, na=False)
        ]
    if request_status_filter and "REQUEST_STATUS" in df.columns:
        filtered_df = filtered_df[
            filtered_df["REQUEST_STATUS"].astype(str).str.contains(request_status_filter, case=False, na=False)
        ]
    if dataset_status_filter and "DATASET_STATUS" in df.columns:
        filtered_df = filtered_df[
            filtered_df["DATASET_STATUS"].astype(str).str.contains(dataset_status_filter, case=False, na=False)
        ]

    st.markdown("### 🧩 Select Columns to Display/Edit")
    columns_to_display = st.multiselect(
        "Pick columns",
        options=filtered_df.columns.tolist(),
        default=["REQUEST_ID", "DATASET_ID", "NAME", "EMAIL", "REQUEST_STATUS"]
    )

    if not columns_to_display:
        st.info("Please select at least one column.")
        return

    edit_df = filtered_df[columns_to_display].copy()
    st.markdown("### ✏️ Editable Table")
    edited_df = st.data_editor(edit_df, num_rows="dynamic", use_container_width=True)

    if st.button("💾 Save Changes"):
        for idx, row in edited_df.iterrows():
            mask = (st.session_state.requests["REQUEST_ID"] == row["REQUEST_ID"])
            if "DATASET_ID" in row:
                mask &= (st.session_state.requests["DATASET_ID"] == row["DATASET_ID"])
            for col in columns_to_display:
                st.session_state.requests.loc[mask, col] = row[col]
        st.success("✅ Changes saved.")

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

    st.markdown("### ✏️ Request Details")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name", value=request_row.get("NAME", ""))
        email = st.text_input("Email", value=request_row.get("EMAIL", ""))
        request_status = st.text_input("Request Status", value=request_row.get("REQUEST_STATUS", ""))
    with col2:
        request_type = st.text_input("Request Type", value=request_row.get("IS_THIS_A_NEW_REQUEST_AMENDMENT_OR_RETROSPECTIVE_ENTRY", ""))
        date_received = st.date_input("Date Request Received",
                                      pd.to_datetime(request_row.get("DATE_REQUEST_RECEIVED_X", date.today())))

    if st.button("💾 Save Request"):
        idxs = df[df["REQUEST_ID"] == selected_id].index
        for idx in idxs:
            st.session_state.requests.at[idx, "NAME"] = name
            st.session_state.requests.at[idx, "EMAIL"] = email
            st.session_state.requests.at[idx, "REQUEST_STATUS"] = request_status
            st.session_state.requests.at[idx, "IS_THIS_A_NEW_REQUEST_AMENDMENT_OR_RETROSPECTIVE_ENTRY"] = request_type
            st.session_state.requests.at[idx, "DATE_REQUEST_RECEIVED_X"] = date_received
        st.success("✅ Request updated.")

    st.markdown("### 📄 Associated Datasets")
    if "DATASET_ID" in req_df.columns:
        dataset_df = req_df[["DATASET_ID", "DATASET_NAME", "DATASET_STATUS"]].copy()
        st.dataframe(dataset_df, use_container_width=True)
    else:
        st.info("No dataset info available for this request.")

# App Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📋 View/Edit Requests", "📝 Request Form Editor", "📥 Import Excel"])
with tab1:
    show_dashboard()
with tab2:
    show_view_requests()
with tab3:
    show_request_form_editor()
with tab4:
    show_import_export()
