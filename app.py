# ===================================================================================
# FINAL v9.0 app.py - Dynamic KPIs, Smart Scorecard & UI Overhaul
# This version introduces a fully dynamic KPI system based on CSV input,
# AI-powered ranking justification, and significant visual/UX enhancements.
# ===================================================================================
import os
import io
import re
import google.generativeai as genai
import streamlit as st
import pandas as pd
import tempfile

# --- Configuration and Page Setup ---
st.set_page_config(
    page_title="AI Campaign Strategist",
    page_icon="🧠",
    layout="wide"
)
st.title("🧠🏆 AI Campaign Strategist")
st.markdown("##### Upload your campaign videos and a CSV of their metrics. Get an expert-level strategic report on what creative works... and *why*.")


# --- Secret & API Configuration ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except (TypeError, KeyError):
    st.error("🚨 A required GOOGLE_API_KEY secret is missing! Please check your secrets.", icon="❗")
    st.stop()

# --- Example KPI Definitions (For User Instruction Only) ---
CAMPAIGN_EXAMPLES = {
    "Awareness": {"Impressions": "5000000", "Cost Per Thousand (CPM)": "2.50", "Video View Rate (%)": "45"},
    "Traffic": {"Click-Through Rate (CTR %)": "2.5", "Cost Per Click (CPC $)": "0.50", "Landing Page Views": "25000"},
    "Conversion": {"Purchases / Leads": "500", "Return On Ad Spend (ROAS x)": "4.5", "Cost Per Acquisition (CPA $)": "50.00"}
}

# --- AI PROMPT ENGINEERING 2.0: Smart Ranking Logic ---
def create_individual_analysis_prompt(filename, kpi_data):
    """Creates a prompt for a CONCISE analysis of a SINGLE video."""
    return f"""
    Analyze the creative of the video named '{filename}'.
    The video's performance metrics are: {kpi_data}
    Your Task: Provide a brief, one-paragraph summary (under 80 words). Focus on the visual and narrative elements. Identify the single most impactful creative element that likely drove these results and explain why. Be direct and concise.
    """

def create_campaign_synthesis_prompt(all_individual_summaries, funnel_stage):
    """Creates the master prompt to analyze the entire campaign with weighted logic."""
    
    # Define what matters most for each stage
    priority_metrics = {
        "Awareness": "impressions, high Video View Rate, and low CPM",
        "Traffic": "high Click-Through Rate (CTR) and low Cost Per Click (CPC)",
        "Conversion": "high Return On Ad Spend (ROAS), high number of Purchases/Leads, and low Cost Per Acquisition (CPA)"
    }
    
    return f"""
    You are a world-class digital marketing campaign strategist analyzing a '{funnel_stage}' campaign. Your primary goal is to identify winning creative strategies based on performance data. For this '{funnel_stage}' campaign, you should prioritize results that show **{priority_metrics.get(funnel_stage, "strong overall performance")}**.

    I have provided you with concise summaries of every video in the campaign.

    **Individual Video Summaries:**
    ---
    {all_individual_summaries}
    ---

    **Your Task:**
    Produce a strategic report with these three sections, using H3 markdown headers (e.g., ### Section Name):

    ### 1. Campaign Performance Scorecard
    Create a Markdown table ranking the videos from best to worst. The ranking MUST be based on the KPIs most relevant to a '{funnel_stage}' campaign goal.
    The table needs three columns: "Rank", "Video Name", and "Ranking Justification".
    In the "Ranking Justification" column, briefly explain *why* each video earned its rank, referencing its key performance metrics and connecting them to the campaign goal. For example: "Ranked #1 due to its exceptional CTR and low CPC, indicating it was highly effective at driving efficient traffic."

    ### 2. Common Themes in Top Performers
    Identify 2-3 common creative elements, strategies, or visual styles shared by the top 2-3 performing videos. Explain *why* you believe these themes resonated with the audience for this campaign type.

    ### 3. Actionable Recommendations
    Provide three clear, specific, and actionable recommendations for the creative team to implement in the next campaign to maximize performance. These should be based directly on the findings from the scorecard and common themes.
    """

def parse_report_and_display(report_text, all_kpis):
    """Parses the AI's markdown report and displays it in a polished UI."""
    st.subheader("🏆 Your Strategic Report", anchor=False)

    # Use regex to find the scorecard table
    scorecard_match = re.search(r"### 1\. Campaign Performance Scorecard\s*\n*(.*?)(\n###|$)", report_text, re.DOTALL | re.IGNORECASE)
    themes_match = re.search(r"### 2\. Common Themes in Top Performers\s*\n*(.*?)(\n###|$)", report_text, re.DOTALL | re.IGNORECASE)
    recs_match = re.search(r"### 3\. Actionable Recommendations\s*\n*(.*)", report_text, re.DOTALL | re.IGNORECASE)

    if scorecard_match:
        scorecard_md = scorecard_match.group(1).strip()
        try:
            # Convert markdown table to DataFrame
            scorecard_df = pd.read_csv(io.StringIO(scorecard_md), sep='|', index_col=False).dropna(axis=1, how='all').iloc[1:]
            scorecard_df.columns = [col.strip() for col in scorecard_df.columns]
            
            # --- Top Performer Dashboard ---
            top_video_name = scorecard_df['Video Name'].iloc[0].strip()
            top_kpis = all_kpis.get(top_video_name, {})

            st.success(f"**Top Performing Video: {top_video_name}**", icon="🥇")
            with st.container(border=True):
                # Dynamically show the top 2-3 most relevant KPIs
                cols = st.columns(len(top_kpis) if len(top_kpis) <= 4 else 4)
                kpi_count = 0
                for k, v in top_kpis.items():
                    if kpi_count < 4:
                        cols[kpi_count].metric(label=k, value=v)
                        kpi_count += 1
                
            # --- Display Full Scorecard ---
            with st.expander("**Campaign Performance Scorecard**", expanded=True):
                st.dataframe(scorecard_df, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error("Could not parse the AI's scorecard. Displaying raw text.")
            st.markdown(scorecard_md)

    if themes_match:
        with st.expander("**Common Themes in Top Performers**"):
            st.markdown(themes_match.group(1).strip())

    if recs_match:
        with st.expander("**Actionable Recommendations**"):
            st.markdown(recs_match.group(1).strip())


# --- REBUILT State-Based Function with Dynamic KPIs and New UI ---
def render_campaign_tab(funnel_stage, kpi_examples):
    """Main function to render a tab's UI and logic."""
    
    session_state_key = f"analysis_state_{funnel_stage}"
    if session_state_key not in st.session_state:
        st.session_state[session_state_key] = {"status": "not_started", "files": [], "kpis": {}}

    # --- UI for Step 1: Uploading Files & KPIs ---
    if st.session_state[session_state_key]["status"] == "not_started":
        with st.container(border=True):
            st.subheader("Step 1: Upload Assets", anchor=False)
            col1, col2 = st.columns(2)
            with col1:
                uploaded_files = st.file_uploader(
                    f"Upload all {funnel_stage} campaign videos",
                    type=["mp4", "mov", "avi", "m4v"], accept_multiple_files=True,
                    key=f"uploader_{funnel_stage.lower()}"
                )
            with col2:
                with st.expander("CSV Formatting Instructions"):
                    st.markdown(f"""
                    Your CSV must have a `filename` column with the exact video names.
                    The other columns will become your KPIs. **Column names matter!**
                    """)
                    example_df = pd.DataFrame({
                        'filename': ['video_A.mp4', 'video_B.mp4'],
                        **kpi_examples
                    })
                    st.code(example_df.to_csv(index=False), language="text")
                kpi_csv_file = st.file_uploader("Upload a CSV with your metrics", type="csv", key=f"csv_uploader_{funnel_stage.lower()}")

        if uploaded_files:
            # Parse CSV and display KPI inputs
            kpi_input_data = {}
            parsed_kpis_from_csv = {}
            if kpi_csv_file:
                try:
                    df = pd.read_csv(kpi_csv_file).astype(str)
                    if 'filename' not in df.columns:
                        st.error("CSV Error: Your file is missing the required 'filename' column.", icon="❌")
                    else:
                        parsed_kpis_from_csv = df.set_index('filename').to_dict('index')
                        st.success("✅ Metrics CSV loaded successfully!", icon="🎉")
                except Exception as e:
                    st.error(f"Error reading CSV file: {e}", icon="❌")
            
            with st.container(border=True):
                st.subheader("Step 2: Verify Metrics", anchor=False)
                st.info("Metrics from your CSV are pre-filled. You can make edits below.", icon="✍️")
                for file in uploaded_files:
                    file_kpis = parsed_kpis_from_csv.get(file.name, {})
                    # If no CSV data, create empty inputs for all potential KPIs from other files
                    if not file_kpis and parsed_kpis_from_csv:
                        all_kpi_keys = next(iter(parsed_kpis_from_csv.values())).keys()
                        file_kpis = {key: "" for key in all_kpi_keys}

                    with st.expander(f"Metrics for: **{file.name}**"):
                        if not file_kpis:
                            st.warning("No metrics found for this file in the CSV. Please enter them manually.")
                            # Simple case: add one input if no CSV is present at all
                            if not parsed_kpis_from_csv:
                                file_kpis = {"Metric 1": ""}
                        
                        cols = st.columns(4)
                        col_idx = 0
                        temp_kpis = {}
                        for kpi_name, kpi_value in file_kpis.items():
                             with cols[col_idx % 4]:
                                temp_kpis[kpi_name] = st.text_input(kpi_name, value=kpi_value, key=f"{kpi_name}_{file.name}_{funnel_stage}")
                             col_idx += 1
                        kpi_input_data[file.name] = temp_kpis
            
            # --- Start Analysis Button ---
            if st.button(f"🚀 Analyze {funnel_stage} Campaign", type="primary", use_container_width=True, key=f"start_button_{funnel_stage.lower()}"):
                st.session_state[session_state_key]["kpis"] = kpi_input_data
                # ... [rest of the button logic is the same]
                files_to_process = [f for f in uploaded_files if any(kpi_input_data.get(f.name, {}).values())]
                if not files_to_process:
                    st.error("No videos with KPIs found. Please enter metrics to begin analysis.")
                else:
                    with st.spinner("Uploading and starting video processing... The app will NOT freeze."):
                        for file in files_to_process:
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
                                    tmp.write(file.getvalue())
                                    video_path = tmp.name
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

    # --- Step 2 & 3: Processing and Report Display (Logic mostly unchanged, just UI calls) ---
    elif st.session_state[session_state_key]["status"] == "processing":
        st.info("🔄 Videos are being processed by Google. This can take several minutes.", icon="⏳")
        st.write("Click the button below to check the status. Once all videos are ready, the final report will be generated.")
        if st.button("Check Status & Generate Report", use_container_width=True, key=f"check_button_{funnel_stage.lower()}"):
            # This logic remains the same
            all_files_ready = True
            with st.spinner("Checking file statuses..."):
                for file_info in st.session_state[session_state_key]["files"]:
                    if file_info["status"] == "processing":
                        api_file = genai.get_file(name=file_info["api_file_name"])
                        if api_file.state.name == "ACTIVE": file_info["status"] = "active"; st.success(f"✅ '{file_info['original_filename']}' is ready.")
                        elif api_file.state.name == "FAILED": file_info["status"] = "failed"; st.error(f"❌ Processing failed for '{file_info['original_filename']}'.")
                        else: all_files_ready = False; st.info(f"⏳ '{file_info['original_filename']}' is still processing...")
            if all_files_ready:
                with st.spinner("All files ready! Generating individual and final reports..."):
                    individual_summaries = []
                    active_files = [f for f in st.session_state[session_state_key]["files"] if f["status"] == 'active']
                    for file_info in active_files:
                        original_filename = file_info["original_filename"]
                        kpis = st.session_state[session_state_key]["kpis"].get(original_filename, {})
                        kpi_text = ", ".join([f"{k}: {v}" for k, v in kpis.items() if v])
                        prompt = create_individual_analysis_prompt(original_filename, kpi_text)
                        api_file = genai.get_file(name=file_info["api_file_name"])
                        response = model.generate_content([prompt, api_file])
                        summary = f"**Video: {original_filename}**\n{response.text}\n\n"
                        individual_summaries.append(summary)

                    if individual_summaries:
                        model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest") # Using Pro for better reasoning
                        synthesis_prompt = create_campaign_synthesis_prompt("".join(individual_summaries), funnel_stage)
                        final_response = model.generate_content(synthesis_prompt)
                        st.session_state[session_state_key]["final_report"] = final_response.text
                        st.session_state[session_state_key]["status"] = "complete"
                        # Cleanup
                        for file_info in st.session_state[session_state_key]["files"]:
                            try: genai.delete_file(name=file_info["api_file_name"])
                            except Exception: pass # Fail silently on cleanup
                        st.rerun()

    elif st.session_state[session_state_key]["status"] == "complete":
        parse_report_and_display(
            st.session_state[session_state_key].get("final_report", "Report not found."),
            st.session_state[session_state_key].get("kpis", {})
        )
        if st.button(f"↩️ Start New {funnel_stage} Analysis", use_container_width=True, key=f"reset_button_{funnel_stage.lower()}"):
            st.session_state[session_state_key] = {"status": "not_started", "files": [], "kpis": {}}
            st.rerun()

# --- Create the Tabs and Render Content ---
tab_names = ["Awareness", "Traffic", "Conversion"]
tab1, tab2, tab3 = st.tabs([f"**{name}**" for name in tab_names])

with tab1:
    render_campaign_tab("Awareness", CAMPAIGN_EXAMPLES["Awareness"])
with tab2:
    render_campaign_tab("Traffic", CAMPAIGN_EXAMPLES["Traffic"])
with tab3:
    render_campaign_tab("Conversion", CAMPAIGN_EXAMPLES["Conversion"])
