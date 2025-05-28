import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import io
import json
import os
import pickle

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

# File paths for persistence
DATA_DIR = "data"
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.pkl")
DATASETS_FILE = os.path.join(DATA_DIR, "datasets.pkl")
COUNTERS_FILE = os.path.join(DATA_DIR, "counters.pkl")

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Persistence functions
def save_data():
    """Save all data to files"""
    try:
        # Save requests
        with open(REQUESTS_FILE, 'wb') as f:
            pickle.dump(st.session_state.requests, f)
        
        # Save datasets
        with open(DATASETS_FILE, 'wb') as f:
            pickle.dump(st.session_state.datasets, f)
        
        # Save counters
        counters = {
            'last_request_id': st.session_state.last_request_id,
            'last_dataset_id': st.session_state.last_dataset_id
        }
        with open(COUNTERS_FILE, 'wb') as f:
            pickle.dump(counters, f)
            
        return True
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        return False

def load_data():
    """Load all data from files"""
    try:
        # Load requests
        if os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, 'rb') as f:
                st.session_state.requests = pickle.load(f)
        else:
            st.session_state.requests = pd.DataFrame(columns=[
                'REQUEST_ID', 'DATE_REQUEST_RECEIVED', 'NAME', 'EMAIL',
                'COMPLETED_IHD_ACTIVITY_PROPOSAL', 'SUPPORTING_DOCUMENTS',
                'IHD_SOURCES', 'COMPANY_IHD_CRITERIA', 'REQUIRES_NONANONYMIZED',
                'NONANONYMIZED_RATIONALE', 'ANALYSIS_TYPES', 'REQUEST_TYPE',
                'LAST_UPDATED_DATE', 'LAST_UPDATED_BY', 'REQUEST_STATUS'
            ])
        
        # Load datasets
        if os.path.exists(DATASETS_FILE):
            with open(DATASETS_FILE, 'rb') as f:
                st.session_state.datasets = pickle.load(f)
        else:
            st.session_state.datasets = pd.DataFrame(columns=[
                'DATASET_ID', 'DATASET_NAME', 'DESCRIPTION', 'SOURCE_TYPE',
                'DATE_CREATED', 'CREATED_BY', 'STATUS', 'ACCESS_LEVEL'
            ])
        
        # Load counters
        if os.path.exists(COUNTERS_FILE):
            with open(COUNTERS_FILE, 'rb') as f:
                counters = pickle.load(f)
                st.session_state.last_request_id = counters.get('last_request_id', 0)
                st.session_state.last_dataset_id = counters.get('last_dataset_id', 0)
        else:
            st.session_state.last_request_id = 0
            st.session_state.last_dataset_id = 0
            
        return True
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return False

# Initialize session state with persistence
def initialize_session_state():
    if 'data_loaded' not in st.session_state:
        load_data()
        st.session_state.data_loaded = True

# Helper functions
def get_next_request_id():
    st.session_state.last_request_id += 1
    save_data()  # Save after incrementing
    return f"REQ-{st.session_state.last_request_id:04d}"

def get_next_dataset_id():
    st.session_state.last_dataset_id += 1
    save_data()  # Save after incrementing
    return f"DS-{st.session_state.last_dataset_id:04d}"

def add_request(request_data):
    new_request = pd.DataFrame([request_data])
    st.session_state.requests = pd.concat([st.session_state.requests, new_request], ignore_index=True)
    save_data()  # Save after adding

def add_dataset(dataset_data):
    new_dataset = pd.DataFrame([dataset_data])
    st.session_state.datasets = pd.concat([st.session_state.datasets, new_dataset], ignore_index=True)
    save_data()  # Save after adding

def update_requests(updated_df):
    st.session_state.requests = updated_df
    save_data()  # Save after updating

def update_datasets(updated_df):
    st.session_state.datasets = updated_df
    save_data()  # Save after updating

# Dashboard page
def show_dashboard():
    st.title("📊 IHD Request Dashboard")
    
    # Auto-save indicator
    col1, col2 = st.columns([3, 1])
    with col2:
        st.success("✅ Auto-save enabled")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", len(st.session_state.requests))
    
    with col2:
        approved_count = len(st.session_state.requests[st.session_state.requests['REQUEST_STATUS'] == 'Approved']) if len(st.session_state.requests) > 0 else 0
        st.metric("Approved Requests", approved_count)
    
    with col3:
        pending_count = len(st.session_state.requests[st.session_state.requests['REQUEST_STATUS'].isin(['Draft', 'Submitted', 'In Review'])]) if len(st.session_state.requests) > 0 else 0
        st.metric("Pending Requests", pending_count)
    
    with col4:
        st.metric("Total Datasets", len(st.session_state.datasets))
    
    # Charts
    if len(st.session_state.requests) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Request Status Distribution")
            status_counts = st.session_state.requests['REQUEST_STATUS'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        title="Request Status Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Requests Over Time")
            if 'DATE_REQUEST_RECEIVED' in st.session_state.requests.columns:
                requests_copy = st.session_state.requests.copy()
                requests_copy['DATE_REQUEST_RECEIVED'] = pd.to_datetime(requests_copy['DATE_REQUEST_RECEIVED'], errors='coerce')
                requests_by_date = requests_copy.groupby(requests_copy['DATE_REQUEST_RECEIVED'].dt.date).size()
                
                fig = px.line(x=requests_by_date.index, y=requests_by_date.values,
                             title="Requests Submitted Over Time")
                fig.update_xaxes(title="Date")
                fig.update_yaxes(title="Number of Requests")
                st.plotly_chart(fig, use_container_width=True)
    
    # Recent requests
    st.subheader("Recent Requests")
    if len(st.session_state.requests) > 0:
        recent_requests = st.session_state.requests.tail(5)[['REQUEST_ID', 'NAME', 'EMAIL', 'REQUEST_STATUS', 'DATE_REQUEST_RECEIVED']]
        st.dataframe(recent_requests, use_container_width=True)
    else:
        st.info("No requests found. Create your first request using the 'New Request' page.")

# New request page
def show_new_request():
    st.title("➕ New IHD Request")
    
    with st.form("new_request_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name*", placeholder="Enter full name")
            email = st.text_input("Email*", placeholder="Enter email address")
            date_received = st.date_input("Date Request Received", value=date.today())
            
        with col2:
            completed_proposal = st.selectbox("Completed IHD Activity Proposal", ["Yes", "No"])
            supporting_docs = st.text_area("Supporting Documents", placeholder="List any supporting documents")
            request_type = st.selectbox("Request Type", ["New Request", "Amendment", "Retrospective Entry"])
        
        st.subheader("IHD Sources")
        ihd_sources = st.multiselect("Types of IHD Sources", IHD_SOURCE_TYPES)
        
        company_criteria = st.text_area("Company IHD Criteria (if applicable)", 
                                       placeholder="Describe criteria for company IHD sources")
        
        col1, col2 = st.columns(2)
        with col1:
            requires_nonanonymized = st.selectbox("Requires Non-anonymized IHD", ["Yes", "No"])
        
        with col2:
            if requires_nonanonymized == "Yes":
                nonanonymized_rationale = st.text_area("Rationale for Non-anonymized IHD", 
                                                     placeholder="Explain why non-anonymized data is required")
            else:
                nonanonymized_rationale = ""
        
        st.subheader("Analysis Information")
        analysis_types = st.multiselect("Types of IHD Analysis", ANALYSIS_TYPES)
        
        request_status = st.selectbox("Initial Status", REQUEST_STATUSES, index=0)
        
        submitted = st.form_submit_button("Submit Request", type="primary")
        
        if submitted:
            if name and email:
                request_data = {
                    'REQUEST_ID': get_next_request_id(),
                    'DATE_REQUEST_RECEIVED': date_received,
                    'NAME': name,
                    'EMAIL': email,
                    'COMPLETED_IHD_ACTIVITY_PROPOSAL': completed_proposal,
                    'SUPPORTING_DOCUMENTS': supporting_docs,
                    'IHD_SOURCES': ', '.join(ihd_sources),
                    'COMPANY_IHD_CRITERIA': company_criteria,
                    'REQUIRES_NONANONYMIZED': requires_nonanonymized,
                    'NONANONYMIZED_RATIONALE': nonanonymized_rationale,
                    'ANALYSIS_TYPES': ', '.join(analysis_types),
                    'REQUEST_TYPE': request_type,
                    'LAST_UPDATED_DATE': datetime.now(),
                    'LAST_UPDATED_BY': name,
                    'REQUEST_STATUS': request_status
                }
                
                add_request(request_data)
                st.success(f"✅ Request {request_data['REQUEST_ID']} created and saved successfully!")
                st.rerun()
            else:
                st.error("Please fill in all required fields (marked with *)")

# View/Edit requests page
def show_view_requests():
    st.title("📋 View & Edit Requests")
    
    if len(st.session_state.requests) == 0:
        st.info("No requests found. Create your first request using the 'New Request' page.")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All"] + REQUEST_STATUSES)
    
    with col2:
        search_term = st.text_input("Search by Name or Email", placeholder="Enter search term")
    
    with col3:
        if st.button("🔄 Refresh Data"):
            load_data()
            st.success("Data refreshed!")
            st.rerun()
    
    # Apply filters
    filtered_requests = st.session_state.requests.copy()
    
    if status_filter != "All":
        filtered_requests = filtered_requests[filtered_requests['REQUEST_STATUS'] == status_filter]
    
    if search_term:
        mask = (filtered_requests['NAME'].str.contains(search_term, case=False, na=False) |
                filtered_requests['EMAIL'].str.contains(search_term, case=False, na=False))
        filtered_requests = filtered_requests[mask]
    
    # Display requests
    if len(filtered_requests) > 0:
        st.subheader(f"Found {len(filtered_requests)} request(s)")
        
        # Editable dataframe
        edited_df = st.data_editor(
            filtered_requests,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "REQUEST_STATUS": st.column_config.SelectboxColumn(
                    "Status",
                    options=REQUEST_STATUSES,
                    required=True
                ),
                "DATE_REQUEST_RECEIVED": st.column_config.DateColumn(
                    "Date Received",
                    format="YYYY-MM-DD"
                ),
                "LAST_UPDATED_DATE": st.column_config.DatetimeColumn(
                    "Last Updated",
                    format="YYYY-MM-DD HH:mm"
                )
            },
            hide_index=True
        )
        
        # Update session state with changes
        if not edited_df.equals(filtered_requests):
            # Update the main dataframe
            for idx, row in edited_df.iterrows():
                request_id = row['REQUEST_ID']
                st.session_state.requests.loc[st.session_state.requests['REQUEST_ID'] == request_id] = row
            
            update_requests(st.session_state.requests)
            st.success("✅ Changes saved successfully!")
    else:
        st.warning("No requests match the current filters.")

# Manage datasets page
def show_manage_datasets():
    st.title("🗄️ Manage Datasets")
    
    tab1, tab2 = st.tabs(["View Datasets", "Add New Dataset"])
    
    with tab1:
        if len(st.session_state.datasets) > 0:
            edited_datasets = st.data_editor(
                st.session_state.datasets,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "STATUS": st.column_config.SelectboxColumn(
                        "Status",
                        options=DATASET_STATUSES,
                        required=True
                    ),
                    "DATE_CREATED": st.column_config.DateColumn(
                        "Date Created",
                        format="YYYY-MM-DD"
                    )
                },
                hide_index=True
            )
            
            if not edited_datasets.equals(st.session_state.datasets):
                update_datasets(edited_datasets)
                st.success("✅ Dataset changes saved!")
        else:
            st.info("No datasets found. Add your first dataset using the 'Add New Dataset' tab.")
    
    with tab2:
        with st.form("new_dataset_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                dataset_name = st.text_input("Dataset Name*")
                source_type = st.selectbox("Source Type", IHD_SOURCE_TYPES)
                created_by = st.text_input("Created By*")
            
            with col2:
                description = st.text_area("Description")
                access_level = st.selectbox("Access Level", ["Public", "Restricted", "Confidential"])
                status = st.selectbox("Status", DATASET_STATUSES)
            
            submitted = st.form_submit_button("Add Dataset", type="primary")
            
            if submitted:
                if dataset_name and created_by:
                    dataset_data = {
                        'DATASET_ID': get_next_dataset_id(),
                        'DATASET_NAME': dataset_name,
                        'DESCRIPTION': description,
                        'SOURCE_TYPE': source_type,
                        'DATE_CREATED': date.today(),
                        'CREATED_BY': created_by,
                        'STATUS': status,
                        'ACCESS_LEVEL': access_level
                    }
                    
                    add_dataset(dataset_data)
                    st.success(f"✅ Dataset {dataset_data['DATASET_ID']} created and saved successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields (marked with *)")

# Reports page  
def show_reports():
    st.title("📈 Reports & Analytics")
    
    if len(st.session_state.requests) == 0:
        st.info("No data available for reports. Please add some requests first.")
        return
    
    # Report selection
    report_type = st.selectbox("Select Report Type", [
        "Request Status Summary",
        "Monthly Request Trends",
        "IHD Source Analysis",
        "User Activity Report"
    ])
    
    if report_type == "Request Status Summary":
        st.subheader("Request Status Summary")
        
        status_summary = st.session_state.requests['REQUEST_STATUS'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(x=status_summary.index, y=status_summary.values,
                        title="Request Status Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(status_summary.reset_index())
    
    elif report_type == "Monthly Request Trends":
        st.subheader("Monthly Request Trends")
        
        requests_copy = st.session_state.requests.copy()
        requests_copy['DATE_REQUEST_RECEIVED'] = pd.to_datetime(requests_copy['DATE_REQUEST_RECEIVED'], errors='coerce')
        requests_copy['Month'] = requests_copy['DATE_REQUEST_RECEIVED'].dt.to_period('M')
        
        monthly_counts = requests_copy.groupby('Month').size()
        
        fig = px.line(x=monthly_counts.index.astype(str), y=monthly_counts.values,
                     title="Requests per Month")
        st.plotly_chart(fig, use_container_width=True)
    
    elif report_type == "IHD Source Analysis":
        st.subheader("IHD Source Analysis")
        
        all_sources = []
        for sources_str in st.session_state.requests['IHD_SOURCES'].dropna():
            if sources_str:
                all_sources.extend([s.strip() for s in sources_str.split(',')])
        
        if all_sources:
            source_counts = pd.Series(all_sources).value_counts()
            fig = px.bar(x=source_counts.index, y=source_counts.values,
                        title="Most Requested IHD Source Types")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No IHD source data available.")
    
    elif report_type == "User Activity Report":
        st.subheader("User Activity Report")
        
        user_activity = st.session_state.requests.groupby('NAME').agg({
            'REQUEST_ID': 'count',
            'REQUEST_STATUS': lambda x: (x == 'Approved').sum(),
            'DATE_REQUEST_RECEIVED': 'max'
        }).rename(columns={
            'REQUEST_ID': 'Total Requests',
            'REQUEST_STATUS': 'Approved Requests',
            'DATE_REQUEST_RECEIVED': 'Last Request Date'
        })
        
        st.dataframe(user_activity, use_container_width=True)

# Import/Export page with better persistence handling
def show_import_export():
    st.title("📥📤 Import/Export Data")
    
    tab1, tab2 = st.tabs(["Export Data", "Import Data"])
    
    with tab1:
        st.subheader("Export to Excel")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export Requests to Excel", use_container_width=True):
                if len(st.session_state.requests) > 0:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        st.session_state.requests.to_excel(writer, sheet_name='Requests', index=False)
                        if len(st.session_state.datasets) > 0:
                            st.session_state.datasets.to_excel(writer, sheet_name='Datasets', index=False)
                    
                    st.download_button(
                        label="💾 Download Excel File",
                        data=output.getvalue(),
                        file_name=f"ihd_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No data to export.")
        
        with col2:
            if st.button("🗄️ Export Datasets to Excel", use_container_width=True):
                if len(st.session_state.datasets) > 0:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        st.session_state.datasets.to_excel(writer, sheet_name='Datasets', index=False)
                    
                    st.download_button(
                        label="💾 Download Datasets Excel",
                        data=output.getvalue(),
                        file_name=f"ihd_datasets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No datasets to export.")
    
    with tab2:
        st.subheader("Import from Excel")
        
        uploaded_file = st.file_uploader(
            "Choose an Excel file",
            type=['xlsx', 'xls'],
            help="Upload an Excel file with 'Requests' and/or 'Datasets' sheets"
        )
        
        if uploaded_file is not None:
            try:
                excel_data = pd.read_excel(uploaded_file, sheet_name=None)
                
                st.success(f"File uploaded successfully! Found sheets: {list(excel_data.keys())}")
                
                col1, col2 = st.columns(2)
                
                # Import requests
                if 'Requests' in excel_data:
                    with col1:
                        if st.button("📊 Import Requests", type="primary", use_container_width=True):
                            requests_df = excel_data['Requests']
                            
                            # Update IDs to avoid conflicts
                            max_existing_id = st.session_state.last_request_id
                            for idx, row in requests_df.iterrows():
                                if pd.isna(row['REQUEST_ID']) or row['REQUEST_ID'] == '':
                                    max_existing_id += 1
                                    requests_df.at[idx, 'REQUEST_ID'] = f"REQ-{max_existing_id:04d}"
                            
                            st.session_state.last_request_id = max_existing_id
                            st.session_state.requests = pd.concat([st.session_state.requests, requests_df], ignore_index=True)
                            save_data()
                            st.success(f"✅ Imported {len(requests_df)} requests and saved!")
                            st.rerun()
                
                # Import datasets
                if 'Datasets' in excel_data:
                    with col2:
                        if st.button("🗄️ Import Datasets", type="primary", use_container_width=True):
                            datasets_df = excel_data['Datasets']
                            
                            # Update IDs to avoid conflicts
                            max_existing_id = st.session_state.last_dataset_id
                            for idx, row in datasets_df.iterrows():
                                if pd.isna(row['DATASET_ID']) or row['DATASET_ID'] == '':
                                    max_existing_id += 1
                                    datasets_df.at[idx, 'DATASET_ID'] = f"DS-{max_existing_id:04d}"
                            
                            st.session_state.last_dataset_id = max_existing_id
                            st.session_state.datasets = pd.concat([st.session_state.datasets, datasets_df], ignore_index=True)
                            save_data()
                            st.success(f"✅ Imported {len(datasets_df)} datasets and saved!")
                            st.rerun()
                
                # Preview data
                st.subheader("Data Preview")
                for sheet_name, df in excel_data.items():
                    st.write(f"**{sheet_name}** ({len(df)} rows)")
                    st.dataframe(df.head(), use_container_width=True)
                    
            except Exception as e:
                st.error(f"Error reading Excel file: {str(e)}")

# Main app
def main():
    initialize_session_state()
    
    # Sidebar navigation
    st.sidebar.title("🏥 IHD Request System")
    
    page = st.sidebar.selectbox(
        "Navigate to:",
        ["Dashboard", "New Request", "View/Edit Requests", "Manage Datasets", "Reports", "Import/Export"]
    )
    
    # Data summary in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Quick Stats")
    st.sidebar.metric("Total Requests", len(st.session_state.requests))
    st.sidebar.metric("Total Datasets", len(st.session_state.datasets))
    
    if len(st.session_state.requests) > 0:
        approved_count = len(st.session_state.requests[st.session_state.requests['REQUEST_STATUS'] == 'Approved'])
        approval_rate = (approved_count / len(st.session_state.requests)) * 100
        st.sidebar.metric("Approval Rate", f"{approval_rate:.1f}%")
    
    # Manual save/load buttons
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Data Management")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("💾 Save", use_container_width=True):
            if save_data():
                st.sidebar.success("Saved!")
    
    with col2:
        if st.button("🔄 Load", use_container_width=True):
            if load_data():
                st.sidebar.success("Loaded!")
                st.rerun()
    
    # Page routing
    if page == "Dashboard":
        show_dashboard()
    elif page == "New Request":
        show_new_request()
    elif page == "View/Edit Requests":
        show_view_requests()
    elif page == "Manage Datasets":
        show_manage_datasets()
    elif page == "Reports":
        show_reports()
    elif page == "Import/Export":
        show_import_export()

if __name__ == "__main__":
    main()
