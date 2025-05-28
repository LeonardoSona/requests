import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date

# Page configuration
st.set_page_config(
    page_title="IHD Request Management System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✅ Define your schema (column names you care about)
REQUEST_COLUMNS = [
    "REQUEST_ID", "DATE_REQUEST_RECEIVED_X", "NAME", "EMAIL",
    "COMPLETED_IHD_ACTIVITY_PROPOSAL", "SUPPORTING_DOCUMENTS",
    "WHAT_TYPES_OF_IHD_SOURCES_DOES_THIS_REQUEST_INCLUDE",
    "IF_YOUR_REQUEST_INCLUDES_COMPANY_IHD_SOURCES_PLEASE_SELECT_WHICH_OF_THE_FOLLOWING_CRITERIA_APPLY_TO_THE_",
    "DOES_THIS_REQUEST_REQUIRE_NONANONYMIZED_IHD",
    "PLEASE_INCLUDE_A_BRIEF_DESCRIPTION_OF_THE_RATIONALE_FOR_WHY_NONANONYMIZED_IHD_IS_REQUIRED",
    "WHAT_TYPES_OF_IHD_ANALYSIS_DOES_THIS_REQUEST_INCLUDE",
    "IS_THIS_A_NEW_REQUEST_AMENDMENT_OR_RETROSPECTIVE_ENTRY",
    "LAST_UPDATED_DATE_X", "LAST_UPDATED_BY_X", "REQUEST_STATUS",
    "FASTTRACK_APPROVAL_YN", "FASTTRACK_TYPE", "COMMENTS",
    "THE_EXPECTED_DURATION_OF_THE_IHD_ACTIVITY",
    "EVALUATION_RELATED_TO_A_COMPANY_PRIORITY_EG_TOP_121_PIPELINE_ASSET_DISEASE_AREA",
    "DATE_ACCESS_GRANTED_X", "BUSINESS_DAYS_FOR_INITIAL_REVIEW_X",
    "BUSINESS_DAYS_FOR_SCIENTIFIC_REVIEW_X", "SCIENTIFIC_REVIEW_TIME_OPEN",
    "BUSINESS_DAYS_FOR_DATA_USE_GOVERNANCE_REVIEW_X", "DATA_USE_GOVERNANCE_TIME_OPEN",
    "BUSINESS_DAYS_FOR_ANONYMIZATION_X", "ANONYMIZATION_TIME_OPEN",
    "BUSINESS_DAYS_FOR_CURATION", "CURATION_TIME_OPEN", "BUSINESS_DAYS_FOR_ACCESS_X",
    "ACCESS_TIME_OPEN", "USE_VS_REUSE", "AUTOAPPROVED_REQUEST_YN",
    "ACTIVITY_DURATION_START_DATE", "ACTIVITY_DURATION_END_DATE",
    "ACCESS_REVOKED", "DATE_EMAIL_SENT_FOR_REVOCATION_4_WEEKS_PENDING_FOR_ACCESS_REVOCATION",
    "TIME_FROM_REQUEST_RECIEVED_TO_ACCESS_GRANTED", "TIME_IN_PROGRESS_BUSINESS_DAYS",
    "TIME_AT_CURRENT_TRIAGE_STEP_X", "ACTIVE_FLAGS", "DATE_REQUEST_RECEIVED_Y",
    "DATASET_ID", "DATASET_NAME", "IHD_SOURCE_STUDY_ID_IF_COMPANY_SOURCE",
    "TYPE_OF_IHD_SOURCE", "EVALUATION_RELATED_TO_A_COMPANY_PRODUCT", "V1_PROPOSAL",
    "V1_PROPOSAL_COMPLETE_DATE", "BUSINESS_DAYS_FOR_INITIAL_REVIEW_Y",
    "LAST_UPDATED_DATE_Y", "LAST_UPDATED_BY_Y", "DATASET_STATUS",
    "SCIENTIFIC_SPADM", "SCIENTIFIC_SPADM_NAME", "DATE_SHARED_WITH_SCIENTIFIC_SPADM",
    "DATE_OF_SCIENTIFIC_REVIEW_DECISION", "BUSINESS_DAYS_FOR_SCIENTIFIC_REVIEW_Y",
    "SCIENTIFIC_REVIEW_TIME_RANGE", "SCIENTIFIC_REVIEW_DECISION", "V2_PROPOSAL",
    "DATA_USE_GOVERNANCE_SPADM", "DATA_USE_GOVERNANCE_SPADM_NAME",
    "DSAP_REQUEST_NUMBER_IF_APPLICABLE", "DATE_SHARED_WITH_DATA_USE_GOVERNANCE_SPADM",
    "DATE_OF_DATA_USE_GOVERNANCE_DECISION", "BUSINESS_DAYS_FOR_DATA_USE_GOVERNANCE_REVIEW_Y",
    "DATA_USE_GOVERNANCE_REVIEW_TIME_RANGE", "DATA_USE_GOVERNANCE_DECISION",
    "V3_PROPOSAL", "DATE_ANONYMIZATION_BO_NOTIFIED_IF_APPLICABLE",
    "DATE_OF_ANONYMIZATION_STARTED_IF_APPLICABLE", "DATE_OF_ANONYMIZATION_COMPLETED_IF_APPLICABLE",
    "BUSINESS_DAYS_FOR_ANONYMIZATION_Y", "ANONYMIZATION_TIME_RANGE",
    "DATE_SHARED_WITH_BDO", "DATE_ACCESS_GRANTED_Y", "BUSINESS_DAYS_FOR_ACCESS_Y",
    "ACCESS_TIME_RANGE", "TIME_FROM_REQUEST_RECEIVED_TO_INDIVIDUAL_DATA_SET_DECISION_BUSINESS_DAYS",
    "TIME_AT_CURRENT_TRIAGE_STEP_Y", "TIME_FROM_REQUEST_RECIEVED_TO_ACCESS_GRANTED_BUSINESS_DAYS"
]

# Initialize session state
def initialize_session_state():
    if 'requests' not in st.session_state:
        st.session_state.requests = pd.DataFrame()
    if 'last_request_id' not in st.session_state:
        st.session_state.last_request_id = 0
    if 'file_uploaded' not in st.session_state:
        st.session_state.file_uploaded = False

def extract_max_id(df, col_name, prefix):
    if col_name in df.columns:
        try:
            return int(
                df[col_name].dropna().astype(str).str.extract(fr"{prefix}(\\d+)").astype(float).max()[0]
            )
        except:
            return 0
    return 0

# Upload Excel
def show_import_export():
    st.subheader("📥 Upload Excel File")
    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx", "xls"])
    if uploaded_file:
        try:
            excel_data = pd.read_excel(uploaded_file, sheet_name=None)
            first_sheet = list(excel_data.keys())[0]
            raw_df = excel_data[first_sheet]

            known_columns = [col for col in REQUEST_COLUMNS if col in raw_df.columns]
            df = raw_df[known_columns] if known_columns else raw_df.copy()

            st.session_state.requests = df
            st.session_state.last_request_id = extract_max_id(df, 'REQUEST_ID', prefix='REQ-')

            st.success(f"✅ Loaded {len(df)} rows from sheet: '{first_sheet}'")
            st.dataframe(df.head(), use_container_width=True)

            st.session_state.file_uploaded = True
            st.rerun()

        except Exception as e:
            st.error(f"❌ Failed to load file: {e}")

# Dashboard
def show_dashboard():
    st.subheader("📊 Dashboard")
    df = st.session_state.requests
    if df.empty:
        st.warning("No data loaded. Please upload a file.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Requests", len(df))
    col2.metric("Approved", len(df[df["REQUEST_STATUS"] == "Approved"]) if "REQUEST_STATUS" in df.columns else 0)
    col3.metric("Pending", len(df[df["REQUEST_STATUS"].isin(["Draft", "Submitted", "In Review"])] if "REQUEST_STATUS" in df.columns else []))

    st.markdown("### 📅 Recent Requests")
    date_cols = [c for c in df.columns if "DATE_REQUEST_RECEIVED" in c.upper()]
    if date_cols:
        date_col = date_cols[0]
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        sorted_df = df.sort_values(by=date_col, ascending=False)
        st.dataframe(sorted_df.head(10), use_container_width=True)
    else:
        st.dataframe(df.head(10), use_container_width=True)

    if "REQUEST_STATUS" in df.columns:
        st.markdown("### 📊 Request Status Distribution")
        status_counts = df['REQUEST_STATUS'].value_counts()
        fig = px.pie(names=status_counts.index, values=status_counts.values, title="Request Status Distribution")
        st.plotly_chart(fig, use_container_width=True)

# View/Edit
def show_view_requests():
    st.subheader("📋 View & Edit Requests")

    df = st.session_state.requests.copy()
    if df.empty:
        st.warning("No data available. Please upload first.")
        return

    # Unique rows based on REQUEST_ID + DATASET_ID
    if "REQUEST_ID" in df.columns and "DATASET_ID" in df.columns:
        df["UNIQUE_KEY"] = df["REQUEST_ID"].astype(str) + "_" + df["DATASET_ID"].astype(str)
    else:
        df["UNIQUE_KEY"] = df.index.astype(str)

    with st.expander("🔍 Filters", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            search = st.text_input("Search NAME or EMAIL")
        with col2:
            request_id_filter = st.text_input("Filter by REQUEST_ID")

        if search:
            df = df[df["NAME"].str.contains(search, case=False, na=False) | df["EMAIL"].str.contains(search, case=False, na=False)]
        if request_id_filter:
            df = df[df["REQUEST_ID"].astype(str).str.contains(request_id_filter, case=False, na=False)]

    # Dynamic column selector
    with st.expander("🧩 Select Columns to Display", expanded=True):
        columns_to_display = st.multiselect(
            "Pick columns to show/edit",
            options=df.columns.tolist(),
            default=["REQUEST_ID", "DATASET_ID", "NAME", "EMAIL", "REQUEST_STATUS"]
        )
        df_display = df[columns_to_display + ["UNIQUE_KEY"]]  # Always include unique key for edit tracking

    st.markdown("### ✏️ Edit Below and Click Save")
    edited_df = st.data_editor(
        df_display.set_index("UNIQUE_KEY"),
        use_container_width=True,
        num_rows="dynamic",
        key="editor"
    ).reset_index()

    if st.button("💾 Save Changes"):
        for _, row in edited_df.iterrows():
            mask = (st.session_state.requests["REQUEST_ID"].astype(str) + "_" + st.session_state.requests["DATASET_ID"].astype(str)) == row["UNIQUE_KEY"]
            for col in columns_to_display:
                st.session_state.requests.loc[mask, col] = row[col]
        st.success("✅ Changes saved.")


# Main app
def main():
    initialize_session_state()
    if not st.session_state.file_uploaded:
        show_import_export()
        return

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📋 View/Edit Requests", "📥 Import Excel"])

    with tab1:
        show_dashboard()
    with tab2:
        show_view_requests()
    with tab3:
        show_import_export()

if __name__ == "__main__":
    main()
