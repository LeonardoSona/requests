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
    
    # Early return if DataFrame is empty
    if df.empty:
        return {
            'avg_time_to_approval': None,
            'median_time_to_approval': None,
            'overdue_count': 0,
            'dataset_status_counts': {}
        }, df
    
    # Make a copy to avoid modifying the original DataFrame
    df = df.copy()
    
    # Convert date columns to datetime if they exist
    if 'DATE_REQUEST_RECEIVED_X' in df.columns:
        df['DATE_REQUEST_RECEIVED_X'] = pd.to_datetime(df['DATE_REQUEST_RECEIVED_X'], errors='coerce')
    if 'DATE_ACCESS_GRANTED_X' in df.columns:
        df['DATE_ACCESS_GRANTED_X'] = pd.to_datetime(df['DATE_ACCESS_GRANTED_X'], errors='coerce')

    # Calculate TIME_TO_APPROVAL (not CYCLE_TIME_DAYS)
    if ('DATE_REQUEST_RECEIVED_X' in df.columns and 
        'DATE_ACCESS_GRANTED_X' in df.columns):
        df['TIME_TO_APPROVAL'] = (df['DATE_ACCESS_GRANTED_X'] - df['DATE_REQUEST_RECEIVED_X']).dt.days
        
        # Only calculate metrics if we have valid data
        valid_times = df['TIME_TO_APPROVAL'].dropna()
        if len(valid_times) > 0:
            metrics['avg_time_to_approval'] = valid_times.mean()
            metrics['median_time_to_approval'] = valid_times.median()
        else:
            metrics['avg_time_to_approval'] = None
            metrics['median_time_to_approval'] = None
    else:
        metrics['avg_time_to_approval'] = None
        metrics['median_time_to_approval'] = None

    # Calculate overdue requests
    if 'DATE_REQUEST_RECEIVED_X' in df.columns and 'REQUEST_STATUS' in df.columns:
        today = pd.Timestamp.now()
        df['DAYS_SINCE_REQUEST'] = (today - df['DATE_REQUEST_RECEIVED_X']).dt.days
        df['OVERDUE'] = (df['REQUEST_STATUS'] != 'Approved') & (df['DAYS_SINCE_REQUEST'] > 90)
        metrics['overdue_count'] = int(df['OVERDUE'].sum())
    else:
        metrics['overdue_count'] = 0

    # Dataset status counts
    if 'DATASET_STATUS' in df.columns:
        metrics['dataset_status_counts'] = df['DATASET_STATUS'].value_counts().to_dict()
    else:
        metrics['dataset_status_counts'] = {}

    return metrics, df

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
    df = st.session_state.requests.copy()
    
    # Check if data is available BEFORE calling compute_enhanced_metrics
    if df.empty or "REQUEST_ID" not in df.columns:
        st.info("No request data available.")
        return

    # Now call compute_enhanced_metrics and get both metrics and updated df
    metrics, df = compute_enhanced_metrics(df)

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
        # Create week column for time series analysis
        df['WEEK'] = df["DATE_REQUEST_RECEIVED_X"].dt.to_period("W").astype(str)
    
        # Total Requests Per Week
        st.markdown("#### 📈 Total Requests Per Week")
        total_per_week = df.groupby('WEEK').size().reset_index(name='Total Requests')
        fig1 = px.line(total_per_week, x='WEEK', y='Total Requests', title='Total Requests Per Week')
        st.plotly_chart(fig1, use_container_width=True)
    
        # Requests by Status Per Week
        st.markdown("#### 🗂️ Requests by Status Per Week")
        if 'REQUEST_STATUS' in df.columns:
            status_week = df.groupby(['WEEK', 'REQUEST_STATUS']).size().reset_index(name='Count')
            fig2 = px.line(status_week, x='WEEK', y='Count', color='REQUEST_STATUS', title='Requests by Status Per Week')
            st.plotly_chart(fig2, use_container_width=True)

        # Avg. Cycle Time for Completed Requests
        st.markdown("#### ⏳ Avg. Cycle Time for Completed Requests Per Week")
        if 'TIME_TO_APPROVAL' in df.columns and 'REQUEST_STATUS' in df.columns:
            completed = df[df['REQUEST_STATUS'] == 'Approved'].dropna(subset=['TIME_TO_APPROVAL'])
            if not completed.empty:
                avg_cycle = completed.groupby('WEEK')['TIME_TO_APPROVAL'].mean().reset_index()
                fig3 = px.line(avg_cycle, x='WEEK', y='TIME_TO_APPROVAL', title='Avg. Cycle Time for Completed Requests')
                st.plotly_chart(fig3, use_container_width=True)

        # Weekly Breakdown: Submitted vs. Completed vs. In Progress
        st.markdown("#### 📊 Weekly Breakdown: Submitted vs. Completed vs. In Progress")
        if "REQUEST_STATUS" in df.columns and 'DATE_ACCESS_GRANTED_X' in df.columns:
            submitted = df.groupby('WEEK').size().rename("Submitted")
            completed = df.dropna(subset=['DATE_ACCESS_GRANTED_X']).groupby('WEEK').size().rename("Completed")
            in_progress = df[df['DATE_ACCESS_GRANTED_X'].isna()].groupby('WEEK').size().rename("In Progress")
            
            weekly_summary = pd.concat([submitted, completed, in_progress], axis=1).fillna(0).reset_index()
            melted_summary = weekly_summary.melt(id_vars='WEEK', var_name='Metric', value_name='Count')
            
            fig4 = px.line(melted_summary, x='WEEK', y='Count', color='Metric', title='Submitted vs Completed vs In Progress Per Week')
            st.plotly_chart(fig4, use_container_width=True)

        # Per-Step Cycle Times (if available)
        step_columns = [
            ("DATE_INITIAL_REVIEW", "Initial Review"),
            ("DATE_SCIENTIFIC_REVIEW", "Scientific Review"),
            ("DATE_DUG_REVIEW", "DUG Review"),
            ("DATE_CURATION_COMPLETE", "Curation Complete")
        ]
        
        for step_col, label in step_columns:
            if step_col in df.columns:
                df[step_col] = pd.to_datetime(df[step_col], errors='coerce')
                df[f'{label}_DAYS'] = (df[step_col] - df['DATE_REQUEST_RECEIVED_X']).dt.days
                step_avg = df.dropna(subset=[f'{label}_DAYS']).groupby('WEEK')[f'{label}_DAYS'].mean().reset_index()
                if not step_avg.empty:
                    fig_step = px.line(step_avg, x='WEEK', y=f'{label}_DAYS', title=f'Average Time to {label} Per Week')
                    st.plotly_chart(fig_step, use_container_width=True)

        # 🧩 Milestone-Based Cycle Durations
        st.markdown("#### 🧪 Cycle Durations by Stage")
        
        # Define milestones as tuples: (start_col, end_col, label) - matching your specification
        milestone_stages = [
            ("DATE_REQUEST_RECEIVED_X", "DATE_SHARED_WITH_SCIENTIFIC_SPADM", "Initial Review"),
            ("DATE_SHARED_WITH_SCIENTIFIC_SPADM", "DATE_OF_SCIENTIFIC_REVIEW_DECISION", "Scientific Decision"),
            ("DATE_SHARED_WITH_DATA_USE_GOVERNANCE_SPADM", "DATE_OF_DATA_USE_GOVERNANCE_DECISION", "Governance Review"),
            ("DATE_OF_ANONYMIZATION_STARTED_IF_APPLICABLE", "DATE_OF_ANONYMIZATION_COMPLETED_IF_APPLICABLE", "Anonymization"),
            ("DATE_OF_DATA_USE_GOVERNANCE_DECISION", "V1_PROPOSAL_COMPLETE_DATE", "Proposal"),
            ("DATE_REQUEST_RECEIVED_X", "DATE_ACCESS_GRANTED_X", "Total Cycle"),
        ]
        
        # Parse all date columns at once to avoid duplication
        all_date_cols = set([col for pair in milestone_stages for col in pair[:2]])
        for col in all_date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        
        # Compute and plot duration per milestone stage
        for start_col, end_col, label in milestone_stages:
            if start_col in df.columns and end_col in df.columns:
                df[f"{label}_DAYS"] = (df[end_col] - df[start_col]).dt.days
                stage_avg = df.dropna(subset=[f"{label}_DAYS"]).groupby('WEEK')[f"{label}_DAYS"].mean().reset_index()
                if not stage_avg.empty:
                    fig = px.line(stage_avg, x='WEEK', y=f"{label}_DAYS", title=f"Average Time to {label} Per Week")
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

    st.markdown("### ✏️ Request Details - Editable Table")
    req_columns = req_df.columns.tolist()
    
    milestone_columns = [
        "NAME",
        "REQUEST_STATUS",
        "DATE_REQUEST_RECEIVED_X",
        "DATE_SHARED_WITH_SCIENTIFIC_SPADM",
        "DATE_OF_SCIENTIFIC_REVIEW_DECISION",
        "DATE_SHARED_WITH_DATA_USE_GOVERNANCE_SPADM",
        "DATE_OF_DATA_USE_GOVERNANCE_DECISION",
        "DATE_OF_ANONYMIZATION_STARTED_IF_APPLICABLE",
        "DATE_OF_ANONYMIZATION_COMPLETED_IF_APPLICABLE",
        "V1_PROPOSAL_COMPLETE_DATE",
        "DATE_ACCESS_GRANTED_X"
    ]

    selected_req_cols = st.multiselect(
        "Choose columns to display/edit for the request",
        req_columns,
        default=[col for col in milestone_columns if col in req_columns]
    )

    if selected_req_cols:
        # Create editable dataframe for the current request
        edit_df = req_df[["REQUEST_ID"] + selected_req_cols].copy()
        
        # Clean the DataFrame to avoid PyArrow issues
        for col in edit_df.columns:
            if "DATE" in col.upper():
                # Convert to proper datetime, then to date for consistency
                edit_df[col] = pd.to_datetime(edit_df[col], errors='coerce')
                # Convert to date objects to avoid timezone issues
                edit_df[col] = edit_df[col].dt.date
            else:
                # Convert to string and handle NaN values
                edit_df[col] = edit_df[col].astype(str)
                edit_df[col] = edit_df[col].replace('nan', '')
                edit_df[col] = edit_df[col].replace('<NA>', '')
        
        # Configure column types for better editing experience
        column_config = {}
        for col in selected_req_cols:
            if "DATE" in col.upper():
                column_config[col] = st.column_config.DateColumn(
                    col,
                    help=f"Enter date for {col}",
                    format="YYYY-MM-DD"
                )
            elif col == "REQUEST_STATUS":
                # Get unique status values from the full dataset for dropdown
                status_options = sorted(df["REQUEST_STATUS"].dropna().unique().tolist()) if "REQUEST_STATUS" in df.columns else []
                if status_options:
                    column_config[col] = st.column_config.SelectboxColumn(
                        col,
                        help="Select request status",
                        options=status_options
                    )
            else:
                column_config[col] = st.column_config.TextColumn(
                    col,
                    help=f"Enter value for {col}"
                )
        
        # Display editable table
        edited_df = st.data_editor(
            edit_df,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            key=f"editor_{selected_id}",
            num_rows="fixed"
        )
        
        # Save button with validation
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 Save Changes", key="save_table_changes"):
                try:
                    # Get the edited row (first row since we're editing one request at a time)
                    edited_row = edited_df.iloc[0]
                    
                    # Validation logic
                    errors = []
                    warnings = []
                    
                    # Date validation
                    for col in selected_req_cols:
                        if "DATE" in col.upper() and pd.notna(edited_row[col]):
                            current_date = pd.to_datetime(edited_row[col])
                            
                            # Check if date is in the future
                            if current_date > pd.Timestamp.now():
                                warnings.append(f"⚠️ {col}: Date is in the future")
                            
                            # Validate date sequences
                            request_received = edited_row.get("DATE_REQUEST_RECEIVED_X")
                            if pd.notna(request_received) and col != "DATE_REQUEST_RECEIVED_X":
                                if current_date < pd.to_datetime(request_received):
                                    errors.append(f"❌ {col}: Cannot be before request received date")
                            
                            # Business logic validations
                            if col == "DATE_OF_SCIENTIFIC_REVIEW_DECISION":
                                shared_sci = edited_row.get("DATE_SHARED_WITH_SCIENTIFIC_SPADM")
                                if pd.notna(shared_sci) and current_date < pd.to_datetime(shared_sci):
                                    errors.append(f"❌ Scientific review decision cannot be before sharing with scientific team")
                            
                            if col == "DATE_OF_DATA_USE_GOVERNANCE_DECISION":
                                shared_gov = edited_row.get("DATE_SHARED_WITH_DATA_USE_GOVERNANCE_SPADM")
                                if pd.notna(shared_gov) and current_date < pd.to_datetime(shared_gov):
                                    errors.append(f"❌ Governance decision cannot be before sharing with governance team")
                    
                    # Status validation
                    if edited_row.get("REQUEST_STATUS") == "Approved" and pd.isna(edited_row.get("DATE_ACCESS_GRANTED_X")):
                        errors.append("❌ Approved requests must have an access granted date")
                    
                    # Display errors and warnings
                    if errors:
                        st.error("**Cannot save due to validation errors:**")
                        for error in errors:
                            st.error(error)
                    else:
                        if warnings:
                            for warning in warnings:
                                st.warning(warning)
                        
                        # Save changes to session state
                        original_request_idx = st.session_state.requests[st.session_state.requests["REQUEST_ID"] == selected_id].index[0]
                        
                        changes = []
                        for col in selected_req_cols:
                            old_val = st.session_state.requests.at[original_request_idx, col]
                            new_val = edited_row[col]
                            
                            if str(old_val) != str(new_val):
                                st.session_state.requests.at[original_request_idx, col] = new_val
                                changes.append(f"**{col}**: `{old_val}` → `{new_val}`")
                        
                        if changes:
                            st.success("✅ Changes saved successfully!")
                            st.info("**Changes made:**\n" + "\n".join(changes))
                        else:
                            st.info("ℹ️ No changes detected")
                            
                except Exception as e:
                    st.error(f"❌ Error saving changes: {str(e)}")
        
        with col2:
            st.caption("💡 Tip: Click on cells to edit directly. Use Tab to move between fields.")

    # 🔍 Requests with Missing Fields - Enhanced editable table
    st.markdown("### 🔍 Requests with Missing Fields - Bulk Edit")
    if selected_req_cols:
        flagged_df = df[df[selected_req_cols].isna().any(axis=1) | (df[selected_req_cols] == "").any(axis=1)]
        if not flagged_df.empty:
            st.warning(f"⚠️ {len(flagged_df)} request(s) with missing values in selected fields.")
            
            # Create editable table for bulk editing
            bulk_edit_df = flagged_df[["REQUEST_ID"] + selected_req_cols].copy()
            
            # Clean the DataFrame to avoid PyArrow issues
            for col in bulk_edit_df.columns:
                if "DATE" in col.upper():
                    # Convert to proper datetime, then to date for consistency
                    bulk_edit_df[col] = pd.to_datetime(bulk_edit_df[col], errors='coerce')
                    # Convert to date objects, keeping None for NaT
                    bulk_edit_df[col] = bulk_edit_df[col].dt.date
                else:
                    # Convert to string and handle NaN values
                    bulk_edit_df[col] = bulk_edit_df[col].astype(str)
                    bulk_edit_df[col] = bulk_edit_df[col].replace('nan', '')
                    bulk_edit_df[col] = bulk_edit_df[col].replace('<NA>', '')
                    bulk_edit_df[col] = bulk_edit_df[col].replace('None', '')
            
            # Use the same column config as above
            bulk_edited_df = st.data_editor(
                bulk_edit_df,
                column_config=column_config,
                use_container_width=True,
                hide_index=True,
                key="bulk_editor",
                num_rows="fixed"
            )
            
            # Bulk save button
            if st.button("💾 Save All Missing Field Updates", key="save_bulk_changes"):
                try:
                    changes_made = 0
                    for idx, edited_row in bulk_edited_df.iterrows():
                        original_idx = st.session_state.requests[st.session_state.requests["REQUEST_ID"] == edited_row["REQUEST_ID"]].index[0]
                        
                        for col in selected_req_cols:
                            old_val = st.session_state.requests.at[original_idx, col]
                            new_val = edited_row[col]
                            
                            if str(old_val) != str(new_val) and pd.notna(new_val):
                                st.session_state.requests.at[original_idx, col] = new_val
                                changes_made += 1
                    
                    if changes_made > 0:
                        st.success(f"✅ Saved {changes_made} changes across {len(bulk_edited_df)} requests!")
                    else:
                        st.info("ℹ️ No changes detected")
                        
                except Exception as e:
                    st.error(f"❌ Error saving bulk changes: {str(e)}")
        else:
            st.success("✅ No missing fields in selected columns.")

    st.markdown("### 📄 Associated Datasets")
    dataset_columns = [col for col in req_df.columns if "DATASET" in col.upper()]
    if dataset_columns:
        # Only show available columns in the default
        available_defaults = [col for col in ["DATASET_ID", "DATASET_NAME", "DATASET_STATUS"] if col in dataset_columns]
        selected_ds_cols = st.multiselect("Choose dataset columns to display", dataset_columns,
                                          default=available_defaults)
        if selected_ds_cols:
            dataset_df = req_df[selected_ds_cols].copy()
            # Convert to string to avoid PyArrow type errors
            dataset_df = dataset_df.astype(str)
            st.dataframe(dataset_df, use_container_width=True)

# App Tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📋 Request Form Editor", "📥 Import Excel"])
with tab1:
    show_dashboard()
with tab2:
    show_request_form_editor()
with tab3:
    show_import_export()
