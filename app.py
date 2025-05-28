import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io

# Page configuration
st.set_page_config(
    page_title="IHD Request Management System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def initialize_session_state():
    if 'requests' not in st.session_state:
        st.session_state.requests = pd.DataFrame()
    if 'datasets' not in st.session_state:
        st.session_state.datasets = pd.DataFrame()
    if 'last_request_id' not in st.session_state:
        st.session_state.last_request_id = 0
    if 'last_dataset_id' not in st.session_state:
        st.session_state.last_dataset_id = 0
    if 'file_uploaded' not in st.session_state:
        st.session_state.file_uploaded = False

# Extract max numeric ID from ID strings
def extract_max_id(df, col_name, prefix):
    if col_name in df.columns:
        try:
            return int(
                df[col_name].dropna().astype(str).str.extract(fr"{prefix}(\d+)").astype(float).max()[0]
            )
        except:
            return 0
    return 0

# Upload Excel
def show_import_export():
    st.title("📥 Upload Excel to Start")
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])

    if uploaded_file:
        try:
            excel_data = pd.read_excel(uploaded_file, sheet_name=None)
            st.write("📄 Found sheets:", list(excel_data.keys()))

            # Load 'Requests' sheet
            sheet_key = [k for k in excel_data if k.lower() == 'requests']
            if sheet_key:
                df = excel_data[sheet_key[0]]
                st.session_state.requests = df
                st.session_state.last_request_id = extract_max_id(df, 'REQUEST_ID', prefix='REQ-')

                st.write("✅ Preview of 'Requests':")
                st.dataframe(df.head(), use_container_width=True)
            else:
                st.error("❌ Sheet 'Requests' not found.")

            # Load 'Datasets' sheet
            dataset_key = [k for k in excel_data if k.lower() == 'datasets']
            if dataset_key:
                df = excel_data[dataset_key[0]]
                st.session_state.datasets = df
                st.session_state.last_dataset_id = extract_max_id(df, 'DATASET_ID', prefix='DS-')
                st.write("✅ Preview of 'Datasets':")
                st.dataframe(df.head(), use_container_width=True)

            st.session_state.file_uploaded = True
            st.success("✅ File successfully uploaded and data loaded!")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Failed to read Excel file: {str(e)}")

# Dashboard
def show_dashboard():
    st.title("📊 IHD Request Dashboard")
    requests_df = st.session_state.requests

    if requests_df.empty:
        st.warning("No request data loaded. Please upload an Excel file with a 'Requests' sheet.")
        return

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Requests", len(requests_df))
    col2.metric("Approved", len(requests_df[requests_df["REQUEST_STATUS"] == "Approved"]) if "REQUEST_STATUS" in requests_df.columns else 0)
    col3.metric("Pending", len(requests_df[requests_df["REQUEST_STATUS"].isin(["Draft", "Submitted", "In Review"])] if "REQUEST_STATUS" in requests_df.columns else []))

    st.markdown("### 📅 Recent Requests")

    date_cols = [c for c in requests_df.columns if "DATE_REQUEST_RECEIVED" in c.upper()]
    if date_cols:
        date_col = date_cols[0]
        requests_df[date_col] = pd.to_datetime(requests_df[date_col], errors='coerce')
        sorted_df = requests_df.sort_values(by=date_col, ascending=False)
        st.dataframe(sorted_df.head(10), use_container_width=True)
    else:
        st.warning("No 'DATE_REQUEST_RECEIVED' column found.")
        st.dataframe(requests_df.head(10), use_container_width=True)

    if "REQUEST_STATUS" in requests_df.columns:
        st.markdown("### 📊 Request Status Distribution")
        status_counts = requests_df['REQUEST_STATUS'].value_counts()
        if not status_counts.empty:
            fig = px.pie(
                names=status_counts.index,
                values=status_counts.values,
                title="Request Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

# Main app
def main():
    initialize_session_state()
    if not st.session_state.file_uploaded:
        show_import_export()
        return

    st.sidebar.title("🏥 IHD Request System")
    page = st.sidebar.selectbox("Navigate to:", ["Dashboard", "Import/Export"])

    if page == "Dashboard":
        show_dashboard()
    elif page == "Import/Export":
        show_import_export()

if __name__ == "__main__":
    main()
