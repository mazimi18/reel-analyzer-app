# ===================================================================================
# FINAL v8.2 app.py - Non-Blocking, State-Based Analysis
# This version uses st.session_state to prevent the app from freezing.
# ===================================================================================
import os
import google.generativeai as genai
import streamlit as st
import time
import tempfile

# --- Configuration and Page Setup ---
st.set_page_config(
    page_title="AI Campaign Strategist",
    page_icon="🏆",
    layout="wide"
)
st.title("🏆 AI Campaign Strategist")
st.markdown("Select a campaign goal below, upload all your videos, and get a strategic report on what creative works... and why.")

# --- Secret & API Configuration ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except (TypeError, KeyError):
    st.error("🚨 A required GOOGLE_API_KEY secret is missing! Please check your secrets.")
    st.stop()

# --- Re-introducing Specific KPI Definitions for each Funnel Stage ---
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

# --- AI Prompt Engineering (Unchanged) ---
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


# --- REBUILT State-Based Function to Render a Campaign Analysis Tab ---
def render_campaign_tab(funnel_stage, kpi_definitions):
    """
    Creates the entire UI and logic for a single tab using st.session_state
    to manage a non-blocking workflow.
    """
    st.header(f"Analyze Your {funnel_stage} Campaign")

    # Use session_state to track the stage for each tab independently
    session_state_key = f"analysis_state_{funnel_stage}"
    if session_state_key not in st.session_state:
        st.session_state[session_state_key] = {
            "status": "not_started", # not_started -> processing -> complete
            "files": [],
            "kpis": {}
        }

    # --- UI for Step 1: Uploading Files ---
    if st.session_state[session_state_key]["status"] == "not_started":
        uploaded_files = st.file_uploader(
            f"Upload all {funnel_stage} campaign videos",
            type=["mp4", "mov", "avi", "m4v"],
            accept_multiple_files=True,
            key=f"uploader_{funnel_stage.lower()}"
        )

        if uploaded_files:
            st.subheader("Enter KPIs for Each Video")
            kpi_input_data = {}
            for file in uploaded_files:
                with st.expander(f"Metrics for: **{file.name}**"):
                    kpi_input_data[file.name] = {
                        kpi: st.text_input(kpi, placeholder=placeholder, key=f"{kpi}_{file.name}_{funnel_stage}")
                        for kpi, placeholder in kpi_definitions.items()
                    }

            if st.button(f"🚀 Start {funnel_stage} Analysis", type="primary", key=f"start_button_{funnel_stage.lower()}"):
                st.session_state[session_state_key]["kpis"] = kpi_input_data
                files_to_process = []
                for file in uploaded_files:
                    kpis = {k: v for k, v in kpi_input_data.get(file.name, {}).items() if v}
                    if not kpis:
                        st.warning(f"Skipping '{file.name}' as no KPIs were provided.")
                        continue
                    files_to_process.append(file)
                
                if files_to_process:
                    with st.spinner("Uploading and starting video processing... This may take a moment. The app will NOT freeze."):
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
                    st.rerun() # Force an immediate rerun to switch to the "processing" view

    # --- UI for Step 2: Checking Status and Generating Report ---
    elif st.session_state[session_state_key]["status"] == "processing":
        st.info("🔄 Videos are being processed by Google. This can take several minutes.")
        st.write("Click the button below to check the status. Once all videos are ready, the final report will be generated.")

        if st.button("Check Status & Generate Report", key=f"check_button_{funnel_stage.lower()}"):
            all_files_ready = True
            with st.spinner("Checking file statuses..."):
                files_to_analyze = st.session_state[session_state_key]["files"]
                for i, file_info in enumerate(files_to_analyze):
                    # Only check files that are still processing
                    if file_info["status"] == "processing":
                        try:
                            api_file = genai.get_file(name=file_info["api_file_name"])
                            if api_file.state.name == "ACTIVE":
                                files_to_analyze[i]["status"] = "active"
                                st.success(f"✅ '{file_info['original_filename']}' is ready.")
                            elif api_file.state.name == "FAILED":
                                files_to_analyze[i]["status"] = "failed"
                                st.error(f"❌ Processing failed for '{file_info['original_filename']}'.")
                            else: # Still processing
                                all_files_ready = False
                                st.info(f"⏳ '{file_info['original_filename']}' is still processing...")
                        except Exception as e:
                            st.error(f"Error checking status for '{file_info['original_filename']}': {e}")
                            files_to_analyze[i]["status"] = "failed"


            if all_files_ready:
                with st.spinner("All files ready! Generating individual and final reports..."):
                    individual_summaries = []
                    # Filter for only active files to analyze
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

                    # Synthesize final report
                    if individual_summaries:
                        all_summaries_text = "".join(individual_summaries)
                        model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
                        synthesis_prompt = create_campaign_synthesis_prompt(all_summaries_text)
                        final_response = model.generate_content(synthesis_prompt)
                        
                        st.session_state[session_state_key]["final_report"] = final_response.text
                        st.session_state[session_state_key]["status"] = "complete"
                        
                        # Cleanup cloud files after analysis
                        for file_info in st.session_state[session_state_key]["files"]:
                            try:
                                genai.delete_file(name=file_info["api_file_name"])
                            except Exception as e:
                                st.warning(f"Could not delete cloud file '{file_info['api_file_name']}'. You may need to do this manually. Error: {e}")

                        st.rerun()

    # --- UI for Step 3: Displaying the Final Report ---
    elif st.session_state[session_state_key]["status"] == "complete":
        st.subheader(f"🏆 Your {funnel_stage} Campaign Strategy Report")
        st.markdown(st.session_state[session_state_key].get("final_report", "Report not found."))
        
        if st.button(f"Start New {funnel_stage} Analysis", key=f"reset_button_{funnel_stage.lower()}"):
            # Clean up the specific state for this tab and rerun
            st.session_state[session_state_key] = {
                "status": "not_started",
                "files": [],
                "kpis": {}
            }
            st.rerun()

# --- Create the Tabs and Render Content ---
tab1, tab2, tab3 = st.tabs(["Awareness Campaigns", "Traffic Campaigns", "Conversion Campaigns"])

with tab1:
    render_campaign_tab("Awareness", CAMPAIGN_METRICS["Awareness"])

with tab2:
    render_campaign_tab("Traffic", CAMPAIGN_METRICS["Traffic"])

with tab3:
    render_campaign_tab("Conversion", CAMPAIGN_METRICS["Conversion"])
