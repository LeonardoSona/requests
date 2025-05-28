import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import io

st.set_page_config(page_title="IHD Request Management", layout="wide")

# Initialize session state
if "requests" not in st.session_state:
    st.session_state.requests = pd.DataFrame()

# Import Page
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

    total_requests = len(df["REQUEST_ID"].dropna().unique())
    total_datasets = len(df["DATASET_ID"].dropna().unique()) if "DATASET_ID" in df.columns else 0
    approved = len(df[df["REQUEST_STATUS"] == "Approved"]) if "REQUEST_STATUS" in df.columns else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Requests", total_requests)
    col2.metric("Approved Requests", approved)
    col3.metric("Total Datasets", total_datasets)

    # Plotly pie chart
    if "REQUEST_STATUS" in df.columns:
        status_counts = df["REQUEST_STATUS"].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Request Status Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Requests over time
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

# View & Edit
def show_view_requests():
    st.subheader("📋 View & Edit Requests")

    df = st.session_state.requests.copy()
    if df.empty:
        st.warning("No data available. Please upload a file.")
        return

    if "REQUEST_ID" in df.columns and "DATASET_ID" in df.columns:
        df["UNIQUE_KEY"] = df["REQUEST_ID"].astype(str) + "_" + df["DATASET_ID"].astype(str)
    else:
        df["UNIQUE_KEY"] = df.index.astype(str)

    col1, col2 = st.columns(2)
    search = col1.text_input("Search by NAME or EMAIL")
    request_id_filter = col2.text_input("Filter by REQUEST_ID")

    filtered_df = df.copy()
    if search:
        filtered_df = filtered_df[
            filtered_df["NAME"].str.contains(search, case=False, na=False) |
            filtered_df["EMAIL"].str.contains(search, case=False, na=False)
        ]
    if request_id_filter:
        filtered_df = filtered_df[
            filtered_df["REQUEST_ID"].astype(str).str.contains(request_id_filter, case=False, na=False)
        ]

    st.markdown("### 🧩 Select Columns to Display/Edit")
    columns_to_display = st.multiselect(
        "Pick columns",
        options=[col for col in filtered_df.columns if col != "UNIQUE_KEY"],
        default=["REQUEST_ID", "DATASET_ID", "NAME", "EMAIL", "REQUEST_STATUS"]
    )

    if not columns_to_display:
        st.info("Please select at least one column.")
        return

    edit_df = filtered_df[["UNIQUE_KEY"] + columns_to_display].copy()
    edit_df = edit_df.set_index("UNIQUE_KEY")

    st.markdown("### ✏️ Editable Table")
    edited_df = st.data_editor(edit_df, num_rows="dynamic", use_container_width=True).reset_index()

    if st.button("💾 Save Changes"):
        for _, row in edited_df.iterrows():
            mask = (st.session_state.requests["REQUEST_ID"].astype(str) + "_" +
                    st.session_state.requests["DATASET_ID"].astype(str)) == row["UNIQUE_KEY"]
            for col in columns_to_display:
                if col in st.session_state.requests.columns:
                    st.session_state.requests.loc[mask, col] = row[col]
        st.success("✅ Changes saved.")

# Form Editor
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
        request_status = st.selectbox(
            "Request Status",
            df["REQUEST_STATUS"].dropna().unique().tolist() if "REQUEST_STATUS" in df.columns else [],
            index=0 if pd.isna(request_row.get("REQUEST_STATUS")) else
            df["REQUEST_STATUS"].dropna().unique().tolist().index(request_row["REQUEST_STATUS"])
        )
    with col2:
        request_type = st.selectbox(
            "Request Type",
            df["IS_THIS_A_NEW_REQUEST_AMENDMENT_OR_RETROSPECTIVE_ENTRY"].dropna().unique().tolist() if "IS_THIS_A_NEW_REQUEST_AMENDMENT_OR_RETROSPECTIVE_ENTRY" in df.columns else [],
            index=0 if pd.isna(request_row.get("IS_THIS_A_NEW_REQUEST_AMENDMENT_OR_RETROSPECTIVE_ENTRY")) else
            df["IS_THIS_A_NEW_REQUEST_AMENDMENT_OR_RETROSPECTIVE_ENTRY"].dropna().unique().tolist().index(
                request_row["IS_THIS_A_NEW_REQUEST_AMENDMENT_OR_RETROSPECTIVE_ENTRY"])
        )
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

# Main app
tab = st.tabs(["📊 Dashboard", "📋 View/Edit Requests", "📝 Request Form Editor", "📥 Import Excel"])
if tab[0]:
    show_dashboard()
elif tab[1]:
    show_view_requests()
elif tab[2]:
    show_request_form_editor()
elif tab[3]:
    show_import_export()
