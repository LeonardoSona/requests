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

# Constants
REQUEST_STATUSES = ["Draft", "Submitted", "In Review", "Approved", "Rejected"]
DATASET_STATUSES = ["Pending", "In Review", "Approved - Access Granted", "Rejected"]

IHD_SOURCE_TYPES = [
    "Clinical Data",
    "Claims Data", 
    "Electronic Health Records",
    "Patient Surveys",
    "Laboratory Results",
    "Imaging Data",
    "Genomic Data"
]

ANALYSIS_TYPES = [
    "Descriptive Analysis",
    "Predictive Modeling",
    "Statistical Analysis",
    "Machine Learning",
    "Data Mining",
    "Cohort Analysis"
]

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

# Upload Excel
def show_import_export():
    st.title("📥 Upload Excel to Start")
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])
    if uploaded_file:
        try:
            excel_data = pd.read_excel(uploaded_file, sheet_name=None)
            if 'Requests' in excel_data:
                st.session_state.requests = excel_data['Requests']
                max_id = st.session_state.requests['REQUEST_ID'].dropna().str.extract(r"REQ-(\d+)").astype(float).max()[0]
                st.session_state.last_request_id = int(max_id) if pd.notna(max_id) else 0
            if 'Datasets' in excel_data:
                st.session_state.datasets = excel_data['Datasets']
                max_id = st.session_state.datasets['DATASET_ID'].dropna().str.extract(r"DS-(\d+)").astype(float).max()[0]
                st.session_state.last_dataset_id = int(max_id) if pd.notna(max_id) else 0
            st.session_state.file_uploaded = True
            st.success("✅ File successfully uploaded and data loaded!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to read Excel file: {str(e)}")

# Dashboard
def show_dashboard():
    st.title("📊 IHD Request Dashboard")

    requests_df = st.session_state.requests
    datasets_df = st.session_state.datasets

    # Fallback info if empty
    if requests_df.empty:
        st.warning("No request data loaded. Please upload an Excel file with a 'Requests' sheet.")
        return

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Requests", len(requests_df))
    col2.metric("Approved Requests", len(requests_df[requests_df["REQUEST_STATUS"] == "Approved"]))
    col3.metric("Pending Requests", len(requests_df[requests_df["REQUEST_STATUS"].isin(["Draft", "Submitted", "In Review"])]))

    st.markdown("### 📅 Recent Requests")
    try:
        # Ensure date column is proper datetime
        requests_df['DATE_REQUEST_RECEIVED'] = pd.to_datetime(requests_df['DATE_REQUEST_RECEIVED'], errors='coerce')
        sorted_df = requests_df.sort_values(by='DATE_REQUEST_RECEIVED', ascending=False)
        st.dataframe(sorted_df.head(10)[['REQUEST_ID', 'NAME', 'EMAIL', 'REQUEST_STATUS', 'DATE_REQUEST_RECEIVED']], use_container_width=True)
    except Exception as e:
        st.error(f"Failed to render recent requests: {e}")
        st.dataframe(requests_df.head(), use_container_width=True)

    st.markdown("### 📊 Request Status Distribution")
    status_counts = requests_df['REQUEST_STATUS'].value_counts()
    if not status_counts.empty:
        fig = px.pie(
            names=status_counts.index,
            values=status_counts.values,
            title="Request Status Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No valid 'REQUEST_STATUS' values to plot.")


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
