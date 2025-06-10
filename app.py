# ===================================================================================
# FINAL v8.3 app.py - Added CSV Metric Import Feature
# ===================================================================================
import os
import google.generativeai as genai
import streamlit as st
import time
import tempfile
import pandas as pd  # <--- IMPORT PANDAS

# --- Configuration and Page Setup (UNCHANGED) ---
st.set_page_config(
    page_title="AI Campaign Strategist",
    page_icon="🏆",
    layout="wide"
)
st.title("🏆 AI Campaign Strategist")
st.markdown("Select a campaign goal below, upload all your videos, and get a strategic report on what creative works... and why.")

# --- Secret & API Configuration (UNCHANGED) ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except (TypeError, KeyError):
    st.error("🚨 A required GOOGLE_API_KEY secret is missing! Please check your secrets.")
    st.stop()

# --- KPI Definitions (UNCHANGED) ---
CAMPAIGN_METRICS = {
    "Awareness": {
        "Impressions": "e.g., 5,000,000",
        "Cost Per Thousand (CPM)": "e.g., $2.50",
        "Video View Rate (%)": "e.g., 45%"
    },
    "Traffic": {
        "Click-Through Rate (CTR %)": "e.g., 2.5%",
        "Cost Per Click (CPC $)": "e.g., $0.50",
        "Landing Page Views": "e.g., 25,000"
    },
    "Conversion": {
        "Purchases / Leads": "e.g., 500",
        "Return On Ad Spend (ROAS x)": "e.g., 4.5x",
        "Cost Per Acquisition (CPA $)": "e.g., $50.00"
    }
}

# --- AI Prompt Engineering (UNCHANGED) ---
def create_individual_analysis_prompt(filename, kpi_data):
    """Creates a prompt for a CONCISE analysis of a SINGLE video."""
    return f"""
    Analyze the creative of the video '{filename}'.
    Reported KPIs: {kpi_data}
    Your Task: Provide a brief, one-paragraph summary (under 80 words). Identify the single most impactful creative element that likely drove these results and explain why.
    """

def create_campaign_synthesis_prompt(all_individual_summaries):
    """Creates the master prompt to analyze the entire campaign."""
    return f"""
    You are a world-class digital marketing campaign strategist. I have provided you with concise summaries of every video in a recent campaign.

    **Individual Video Summaries:**
    ---
    {all_individual_summaries}
    ---

    **Your Task:**
    Produce a strategic report with these three sections:

    ### 1. Campaign Performance Scorecard
    Create a simple table ranking the videos from best to worst performing based on their summaries. Include the video name and a "Key Creative Takeaway".

    ### 2. Common Themes in Top Performers
    Identify 2-3 common creative elements or strategies that the top-performing videos shared. Explain *why* you believe these themes resonated.

    ### 3. Actionable Recommendations
    Provide three clear recommendations for the next campaign to maximize performance.
    """

# --- REBUILT State-Based Function with CSV Import ---
def render_campaign_tab(funnel_stage, kpi_definitions):
    """
    Creates the entire UI and logic for a single tab, now with CSV import.
    """
    st.header(f"Analyze Your {funnel_stage} Campaign")

    session_state_key = f"analysis_state_{funnel_stage}"
    if session_state_key not in st.session_state:
        st.session_state[session_state_key] = {
            "status": "not_started",
            "files": [],
            "kpis": {},
            "parsed_kpis": {} #<-- NEW: To store data from CSV
        }

    # --- UI for Step 1: Uploading Files ---
    if st.session_state[session_state_key]["status"] == "not_started":
        col1, col2 = st.columns(2)
        with col1:
             uploaded_files = st.file_uploader(
                f"1. Upload all {funnel_stage} campaign videos",
                type=["mp4", "mov", "avi", "m4v"],
                accept_multiple_files=True,
                key=f"uploader_{funnel_stage.lower()}"
            )
        with col2:
            st.markdown("---") # Visual separator
            st.subheader("2. (Optional) Upload a CSV with Metrics")

            # Instructions for the user on CSV format
            with st.expander("Click here for CSV formatting instructions"):
                st.markdown(f"""
                Your CSV file **must** have a header row and a `filename` column.
                - The `filename` column must contain the **exact** name of the uploaded video files (e.g., `my_video_ad_1.mp4`).
                - The other column headers must **exactly** match the KPI names for this tab.
                - **Example for {funnel_stage} Campaign:**
                """)
                # Create an example DataFrame and show it as CSV text
                example_kpis = { 'filename': ['video_A.mp4', 'video_B.mp4'] }
                for kpi in kpi_definitions.keys():
                    example_kpis[kpi] = ['value1', 'value2']
                example_df = pd.DataFrame(example_kpis)
                st.code(example_df.to_csv(index=False), language="text")

            # The CSV uploader
            kpi_csv_file = st.file_uploader("Upload KPI data", type="csv", key=f"csv_uploader_{funnel_stage.lower()}")

            # Logic to parse the CSV and store in session state
            if kpi_csv_file:
                try:
                    df = pd.read_csv(kpi_csv_file)
                    if 'filename' not in df.columns:
                        st.error("CSV parsing error: Your file is missing the required 'filename' column.", icon="❌")
                    else:
                        # Convert all data to string type for consistency with st.text_input
                        df = df.astype(str)
                        # Set the filename as the index and convert to a dictionary
                        parsed_data = df.set_index('filename').to_dict('index')
                        st.session_state[session_state_key]['parsed_kpis'] = parsed_data
                        st.success("✅ Metrics CSV loaded successfully! Fields below are pre-populated.", icon="🎉")
                except Exception as e:
                    st.error(f"Error reading CSV file: {e}", icon="❌")

        if uploaded_files:
            st.markdown("---")
            st.subheader("3. Enter or Verify KPIs for Each Video")
            kpi_input_data = {}
            # Get the parsed data from session state
            parsed_kpis = st.session_state[session_state_key].get('parsed_kpis', {})

            for file in uploaded_files:
                # Check if this filename has pre-populated data
                prepopulated_metrics = parsed_kpis.get(file.name, {})

                with st.expander(f"Metrics for: **{file.name}**"):
                    kpi_input_data[file.name] = {
                        kpi: st.text_input(
                            kpi,
                            # Use the pre-populated value, or empty string if not found
                            value=prepopulated_metrics.get(kpi, ""),
                            placeholder=placeholder,
                            key=f"{kpi}_{file.name}_{funnel_stage}"
                        )
                        for kpi, placeholder in kpi_definitions.items()
                    }

            if st.button(f"🚀 Start {funnel_stage} Analysis", type="primary", key=f"start_button_{funnel_stage.lower()}"):
                # This part of the logic remains the same
                st.session_state[session_state_key]["kpis"] = kpi_input_data
                files_to_process = []
                for file in uploaded_files:
                    kpis = {k: v for k, v in kpi_input_data.get(file.name, {}).items() if v}
                    if not kpis:
                        st.warning(f"Skipping '{file.name}' as no KPIs were provided.")
                        continue
                    files_to_process.append(file)
                
                if files_to_process:
                    with st.spinner("Uploading and starting video processing... The app will NOT freeze."):
                        # The rest of the processing logic is unchanged
                        for file in files_to_process:
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp_file:
                                    tmp_file.write(file.getvalue())
                                    video_path = tmp_file.name
                                
                                video_file_for_api = genai.upload_file(path=video_path)
                                st.session_state[session_state_key]["files"].append({
                                    "original_filename": file.name,
                                    "api_file_name": video_file_for_api.name,
                                    "status": "processing"
                                })
                                os.remove(video_path)
                            except Exception as e:
                                st.error(f"Failed to upload '{file.name}': {e}")
                    
                    st.session_state[session_state_key]["status"] = "processing"
                    st.rerun()

    # --- THE REST OF THE FUNCTION (Processing and Complete states) is UNCHANGED ---
    elif st.session_state[session_state_key]["status"] == "processing":
        st.info("🔄 Videos are being processed by Google. This can take several minutes.")
        st.write("Click the button below to check the status. Once all videos are ready, the final report will be generated.")

        if st.button("Check Status & Generate Report", key=f"check_button_{funnel_stage.lower()}"):
            all_files_ready = True
            with st.spinner("Checking file statuses..."):
                files_to_analyze = st.session_state[session_state_key]["files"]
                for i, file_info in enumerate(files_to_analyze):
                    if file_info["status"] == "processing":
                        try:
                            api_file = genai.get_file(name=file_info["api_file_name"])
                            if api_file.state.name == "ACTIVE":
                                files_to_analyze[i]["status"] = "active"
                                st.success(f"✅ '{file_info['original_filename']}' is ready.")
                            elif api_file.state.name == "FAILED":
                                files_to_analyze[i]["status"] = "failed"
                                st.error(f"❌ Processing failed for '{file_info['original_filename']}'.")
                            else:
                                all_files_ready = False
                                st.info(f"⏳ '{file_info['original_filename']}' is still processing...")
                        except Exception as e:
                            st.error(f"Error checking status for '{file_info['original_filename']}': {e}")
                            files_to_analyze[i]["status"] = "failed"

            if all_files_ready:
                with st.spinner("All files ready! Generating individual and final reports..."):
                    individual_summaries = []
                    active_files = [f for f in st.session_state[session_state_key]["files"] if f["status"] == 'active']
                    for file_info in active_files:
                        try:
                            original_filename = file_info["original_filename"]
                            kpis = st.session_state[session_state_key]["kpis"].get(original_filename, {})
                            kpi_text = ", ".join([f"{k}: {v}" for k, v in kpis.items()])
                            api_file_name = file_info["api_file_name"]
                            model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
                            prompt = create_individual_analysis_prompt(original_filename, kpi_text)
                            api_file = genai.get_file(name=api_file_name)
                            response = model.generate_content([prompt, api_file])
                            summary = f"**Video: {original_filename}**\n{response.text}\n\n"
                            individual_summaries.append(summary)
                        except Exception as e:
                            st.error(f"Error during final analysis of '{original_filename}': {e}")
                            individual_summaries.append(f"**Video: {original_filename}**\nAnalysis failed.\n\n")

                    if individual_summaries:
                        all_summaries_text = "".join(individual_summaries)
                        model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
                        synthesis_prompt = create_campaign_synthesis_prompt(all_summaries_text)
                        final_response = model.generate_content(synthesis_prompt)
                        st.session_state[session_state_key]["final_report"] = final_response.text
                        st.session_state[session_state_key]["status"] = "complete"
                        for file_info in st.session_state[session_state_key]["files"]:
                            try:
                                genai.delete_file(name=file_info["api_file_name"])
                            except Exception as e:
                                st.warning(f"Could not delete cloud file '{file_info['api_file_name']}'. You may need to do this manually. Error: {e}")
                        st.rerun()

    elif st.session_state[session_state_key]["status"] == "complete":
        st.subheader(f"🏆 Your {funnel_stage} Campaign Strategy Report")
        st.markdown(st.session_state[session_state_key].get("final_report", "Report not found."))
        if st.button(f"Start New {funnel_stage} Analysis", key=f"reset_button_{funnel_stage.lower()}"):
            st.session_state[session_state_key] = {
                "status": "not_started", "files": [], "kpis": {}, "parsed_kpis": {}
            }
            st.rerun()

# --- Create the Tabs and Render Content (UNCHANGED) ---
tab1, tab2, tab3 = st.tabs(["Awareness Campaigns", "Traffic Campaigns", "Conversion Campaigns"])

with tab1:
    render_campaign_tab("Awareness", CAMPAIGN_METRICS["Awareness"])
with tab2:
    render_campaign_tab("Traffic", CAMPAIGN_METRICS["Traffic"])
with tab3:
    render_campaign_tab("Conversion", CAMPAIGN_METRICS["Conversion"])
