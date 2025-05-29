import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Request Management", layout="wide")

# Initialize session state
if "requests" not in st.session_state:
    st.session_state.requests = pd.DataFrame()

# Utility: Enhanced metrics
def compute_enhanced_metrics(df):
    metrics = {}
    df['DATE_REQUEST_RECEIVED_X'] = pd.to_datetime(df.get('DATE_REQUEST_RECEIVED_X'), errors='coerce')
    df['DATE_ACCESS_GRANTED_X'] = pd.to_datetime(df.get('DATE_ACCESS_GRANTED_X'), errors='coerce')
    df['TIME_TO_APPROVAL'] = (df['DATE_ACCESS_GRANTED_X'] - df['DATE_REQUEST_RECEIVED_X']).dt.days

    metrics['avg_time_to_approval'] = df['TIME_TO_APPROVAL'].mean()
    metrics['median_time_to_approval'] = df['TIME_TO_APPROVAL'].median()

    if 'DATASET_STATUS' in df.columns:
        metrics['dataset_status_counts'] = df['DATASET_STATUS'].value_counts().to_dict()
    else:
        metrics['dataset_status_counts'] = {}

    today = pd.Timestamp.now()
    df['DAYS_SINCE_REQUEST'] = (today - df['DATE_REQUEST_RECEIVED_X']).dt.days
    df['OVERDUE'] = (df['REQUEST_STATUS'] != 'Approved') & (df['DAYS_SINCE_REQUEST'] > 90)
    metrics['overdue_count'] = df['OVERDUE'].sum()

    return metrics

# Import Excel
def show_import_export():
    st.subheader("📥 Upload Excel File")
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            st.session_state.requests = df.copy()
            st.success("✅ File uploaded and data loaded!")
            st.dataframe(df.astype(str).head(), use_container_width=True)
        except Exception as e:
            st.error(f"Failed to load Excel file: {str(e)}")

# Dashboard
def show_dashboard():
    st.subheader("📊 Dashboard")
    df = st.session_state.requests
    if df.empty or "REQUEST_ID" not in df.columns:
        st.info("No request data available.")
        return

    metrics = compute_enhanced_metrics(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Requests", len(df["REQUEST_ID"].dropna().unique()))
    col2.metric("Approved Requests", len(df[df["REQUEST_STATUS"] == "Approved"]) if "REQUEST_STATUS" in df.columns else 0)
    col3.metric("Total Datasets", len(df["DATASET_ID"].dropna().unique()) if "DATASET_ID" in df.columns else 0)

    col1, col2, col3 = st.columns(3)
    col1.metric("⏱️ Avg. Time to Approval", f"{metrics['avg_time_to_approval']:.1f} days" if metrics['avg_time_to_approval'] else "N/A")
    col2.metric("📉 Median Time to Approval", f"{metrics['median_time_to_approval']:.1f} days" if metrics['median_time_to_approval'] else "N/A")
    col3.metric("⚠️ Overdue Requests", metrics['overdue_count'])

    if metrics['dataset_status_counts']:
        st.markdown("#### 📦 Dataset Status Summary")
        status_df = pd.DataFrame(metrics['dataset_status_counts'].items(), columns=["Status", "Count"])
        st.dataframe(status_df, use_container_width=True)

    if "REQUEST_STATUS" in df.columns:
        st.markdown("#### 🧁 Request Status Distribution")
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

# Request Form Editor with DQ flag icons and status filter
def show_request_form_editor():
    st.subheader("📝 Request Form Editor")
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = 0
    df = st.session_state.requests.copy()
    if df.empty or "REQUEST_ID" not in df.columns:
        st.warning("No request data available.")
        return

    # Filter by request status
    statuses = sorted(df["REQUEST_STATUS"].dropna().unique().tolist()) if "REQUEST_STATUS" in df.columns else []
    selected_status = st.selectbox("Filter by Request Status", ["All"] + statuses, key="status_filter_form")
    if selected_status != "All":
        df = df[df["REQUEST_STATUS"] == selected_status]

    unique_requests = sorted(df["REQUEST_ID"].dropna().unique().tolist())
    num_requests = len(unique_requests)
    if num_requests == 0:
        st.warning("No valid Request IDs found.")
        return

    if st.session_state.selected_index >= num_requests:
        st.session_state.selected_index = 0

    # Navigation
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("⬅️ Previous Request ID"):
            st.session_state.selected_index = (st.session_state.selected_index - 1) % num_requests
    with col2:
        if st.button("➡️ Next Request ID"):
            st.session_state.selected_index = (st.session_state.selected_index + 1) % num_requests
    with col3:
        selected_id = st.selectbox("Select Request ID", unique_requests, index=st.session_state.selected_index)
        st.session_state.selected_index = unique_requests.index(selected_id)

    req_df = df[df["REQUEST_ID"] == selected_id].copy()
    request_row = req_df.iloc[0].copy()

    st.markdown("### ✏️ Request Details")
    req_columns = req_df.columns.tolist()
    selected_req_cols = st.multiselect("Choose columns to display/edit for the request", req_columns,
                                       default=["NAME", "EMAIL", "REQUEST_STATUS", "IS_THIS_A_NEW_REQUEST_AMENDMENT_OR_RETROSPECTIVE_ENTRY", "DATE_REQUEST_RECEIVED_X"])

    # 🔍 Requests with Missing Fields
    st.markdown("### 🔍 Requests with Missing Fields")
    flagged_df = df[df[selected_req_cols].isna().any(axis=1) | (df[selected_req_cols] == "").any(axis=1)]
    if not flagged_df.empty:
        st.warning(f"⚠️ {len(flagged_df)} request(s) with missing values in selected fields.")
        st.dataframe(flagged_df[["REQUEST_ID"] + selected_req_cols], use_container_width=True)
    else:
        st.success("✅ No missing fields in selected columns.")

    # Determine missing values in selected fields
    missing_fields = [col for col in selected_req_cols if pd.isna(request_row.get(col)) or str(request_row.get(col)).strip() == ""]

    req_data = {}
    for col in selected_req_cols:
        is_missing = col in missing_fields
        label_col, input_col = st.columns([3, 7])
        with label_col:
            st.markdown(f"**{col}** {'⚠️' if is_missing else ''}")
        with input_col:
            value = request_row.get(col, "")
            if "DATE" in col.upper():
                parsed_date = pd.to_datetime(value, errors="coerce")
                parsed_date = parsed_date if pd.notna(parsed_date) else date.today()
                req_data[col] = st.date_input("", value=parsed_date, key=f"date_{col}")
            else:
                req_data[col] = st.text_input("", value, key=f"text_{col}")

    if st.button("💾 Save Request"):
        idxs = df[df["REQUEST_ID"] == selected_id].index
        for idx in idxs:
            for col, val in req_data.items():
                st.session_state.requests.at[idx, col] = val
        st.success("✅ Request updated.")

    st.markdown("### 📄 Associated Datasets")
    dataset_columns = [col for col in req_df.columns if "DATASET" in col.upper()]
    if dataset_columns:
        selected_ds_cols = st.multiselect("Choose dataset columns to display", dataset_columns,
                                          default=["DATASET_ID", "DATASET_NAME", "DATASET_STATUS"])
        dataset_df = req_df[selected_ds_cols].copy()
        st.dataframe(dataset_df, use_container_width=True)

    

# App Tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📋 Request Form Editor", "📥 Import Excel"])
with tab1:
    show_dashboard()
with tab2:
    show_request_form_editor()
with tab3:
    show_import_export()
