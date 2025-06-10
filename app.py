# ===================================================================================
# FINAL v10.0 app.py - Robust API Retry Logic
# This version implements exponential backoff to handle API rate limits gracefully
# and prevent crashes from ResourceExhausted errors.
# ===================================================================================
import os
import io
import re
import google.generativeai as genai
import streamlit as st
import pandas as pd
import tempfile
import time

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

# --- NEW: ROBUST API CALLER WITH RETRY LOGIC ---
def generate_with_retry(model, prompt_parts, retries=5, base_delay=5):
    """
    Calls the Google API with exponential backoff to handle rate limiting.
    """
    num_attempts = 0
    while num_attempts < retries:
        try:
            # Make the API call
            response = model.generate_content(prompt_parts)
            # If successful, return the response and break the loop
            return response
        except google.api_core.exceptions.ResourceExhausted as e:
            num_attempts += 1
            if num_attempts < retries:
                st.warning(f"API rate limit hit. Retrying in {base_delay} seconds... (Attempt {num_attempts}/{retries})", icon="⏳")
                time.sleep(base_delay)
                base_delay *= 2  # Double the delay for the next attempt
            else:
                st.error(f"API rate limit error after {retries} retries. The API is too busy. Please wait a few minutes and try again.")
                raise e # Re-raise the final exception to stop the app
        except Exception as e:
            # Handle other potential errors
            st.error(f"An unexpected error occurred during API call: {e}")
            raise e

# --- AI PROMPT ENGINEERING (Unchanged) ---
def create_individual_analysis_prompt(filename, kpi_data):
    return f"""
    Analyze the creative of the video named '{filename}'.
    The video's performance metrics are: {kpi_data}
    Your Task: Provide a brief, one-paragraph summary (under 80 words). Focus on the visual and narrative elements. Identify the single most impactful creative element that likely drove these results and explain why. Be direct and concise.
    """

def create_campaign_synthesis_prompt(all_individual_summaries, funnel_stage):
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
    Create a Markdown table ranking the videos from best to worst. The ranking MUST be based on the KPIs most relevant to a '{funnel_stage}' campaign goal. The table needs three columns: "Rank", "Video Name", and "Ranking Justification". In the "Ranking Justification" column, briefly explain *why* each video earned its rank, referencing its key performance metrics and connecting them to the campaign goal. For example: "Ranked #1 due to its exceptional CTR and low CPC, indicating it was highly effective at driving efficient traffic."
    ### 2. Common Themes in Top Performers
    Identify 2-3 common creative elements, strategies, or visual styles shared by the top 2-3 performing videos. Explain *why* you believe these themes resonated with the audience for this campaign type.
    ### 3. Actionable Recommendations
    Provide three clear, specific, and actionable recommendations for the creative team to implement in the next campaign to maximize performance. These should be based directly on the findings from the scorecard and common themes.
    """

# --- UI FUNCTION to parse and display the report (Unchanged) ---
def parse_report_and_display(report_text, all_kpis):
    st.subheader("🏆 Your Strategic Report", anchor=False)
    # ... (This function remains the same as before)
    scorecard_match = re.search(r"### 1\. Campaign Performance Scorecard\s*\n*(.*?)(\n###|$)", report_text, re.DOTALL | re.IGNORECASE)
    themes_match = re.search(r"### 2\. Common Themes in Top Performers\s*\n*(.*?)(\n###|$)", report_text, re.DOTALL | re.IGNORECASE)
    recs_match = re.search(r"### 3\. Actionable Recommendations\s*\n*(.*)", report_text, re.DOTALL | re.IGNORECASE)
    if scorecard_match:
        scorecard_md = scorecard_match.group(1).strip()
        try:
            lines = [line.strip() for line in scorecard_md.split('\n') if line.strip() and not line.strip().startswith('---')]
            header = [h.strip() for h in lines[0].split('|') if h.strip()]
            data = [dict(zip(header, [d.strip() for d in row.split('|')[1:-1]])) for row in lines[1:]]
            scorecard_df = pd.DataFrame(data)
            top_video_name = scorecard_df['Video Name'].iloc[0].strip()
            top_kpis = all_kpis.get(top_video_name, {})
            st.success(f"**Top Performing Video: {top_video_name}**", icon="🥇")
            if top_kpis:
                with st.container(border=True):
                    cols = st.columns(len(top_kpis) if len(top_kpis) <= 4 else 4)
                    for i, (k, v) in enumerate(top_kpis.items()):
                        if i < 4: cols[i].metric(label=k, value=v)
            with st.expander("**Campaign Performance Scorecard**", expanded=True):
                st.dataframe(scorecard_df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Could not parse the AI's scorecard. Displaying raw text. Error: {e}")
            st.markdown(scorecard_md)
    if themes_match:
        with st.expander("**Common Themes in Top Performers**"): st.markdown(themes_match.group(1).strip())
    if recs_match:
        with st.expander("**Actionable Recommendations**"): st.markdown(recs_match.group(1).strip())


# --- REBUILT State-Based Function with Robust Retry Logic ---
def render_campaign_tab(funnel_stage):
    session_state_key = f"analysis_state_{funnel_stage}"
    if session_state_key not in st.session_state:
        st.session_state[session_state_key] = {"status": "not_started", "files": [], "kpis": {}, "manual_kpis": {}}

    if st.session_state[session_state_key]["status"] == "not_started":
        # ... (This entire "not_started" block is the same as before) ...
        with st.container(border=True):
            st.subheader("Step 1: Upload Assets", anchor=False, help="Upload your videos and an optional CSV with performance metrics.")
            col1, col2 = st.columns(2)
            with col1: uploaded_files = st.file_uploader("Upload campaign videos", type=["mp4", "mov", "avi", "m4v"], accept_multiple_files=True, key=f"uploader_{funnel_stage.lower()}")
            with col2: kpi_csv_file = st.file_uploader("Upload a CSV with your metrics (Optional)", type="csv", key=f"csv_uploader_{funnel_stage.lower()}", help="Must have a 'filename' column. The filename can be with or without the extension (e.g., .mp4).")
        if uploaded_files:
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
                st.subheader("Step 2: Enter or Verify Metrics", anchor=False)
                kpi_input_data = {}
                for file in uploaded_files:
                    with st.expander(f"Metrics for: **{file.name}**"):
                        basename, _ = os.path.splitext(file.name)
                        file_kpis_from_csv = parsed_kpis_from_csv.get(file.name) or parsed_kpis_from_csv.get(basename)
                        if file_kpis_from_csv:
                            st.markdown("###### Metrics from CSV (editable)")
                            temp_kpis = {}
                            cols = st.columns(3)
                            for i, (k, v) in enumerate(file_kpis_from_csv.items()):
                                with cols[i % 3]: temp_kpis[k] = st.text_input(f"**{k}**", value=v, key=f"csv_{k}_{file.name}_{funnel_stage}")
                            kpi_input_data[file.name] = temp_kpis
                        else:
                            st.info("No metrics found for this file in CSV. Add them manually below.", icon="✍️")
                            if file.name not in st.session_state[session_state_key]["manual_kpis"]:
                                st.session_state[session_state_key]["manual_kpis"][file.name] = []
                            temp_manual_kpis = {}
                            for i, item in enumerate(st.session_state[session_state_key]["manual_kpis"][file.name]):
                                c1, c2 = st.columns([2, 2])
                                with c1: name = st.text_input("Metric Name", value=item.get("name", ""), key=f"manual_name_{i}_{file.name}_{funnel_stage}")
                                with c2: value = st.text_input("Metric Value", value=item.get("value", ""), key=f"manual_value_{i}_{file.name}_{funnel_stage}")
                                if name and value: temp_manual_kpis[name] = value
                            kpi_input_data[file.name] = temp_manual_kpis
                            if st.button("Add Metric", key=f"add_kpi_{file.name}_{funnel_stage}"):
                                st.session_state[session_state_key]["manual_kpis"][file.name].append({"name": "", "value": ""}); st.rerun()
            if st.button(f"🚀 Analyze {funnel_stage} Campaign", type="primary", use_container_width=True, key=f"start_button_{funnel_stage.lower()}"):
                st.session_state[session_state_key]["kpis"] = kpi_input_data
                files_to_process = [f for f in uploaded_files if any(kpi_input_data.get(f.name, {}).values())]
                if not files_to_process:
                    st.error("No videos with KPIs found. Please enter metrics to begin analysis.")
                else:
                    with st.spinner("Uploading and starting video processing... The app will NOT freeze."):
                        for file in files_to_process:
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
                                    tmp.write(file.getvalue())
                                video_file_for_api = genai.upload_file(path=tmp.name)
                                st.session_state[session_state_key]["files"].append({"original_filename": file.name, "api_file_name": video_file_for_api.name, "status": "processing"})
                                os.remove(tmp.name)
                            except Exception as e: st.error(f"Failed to upload '{file.name}': {e}")
                    st.session_state[session_state_key]["status"] = "processing"; st.rerun()

    elif st.session_state[session_state_key]["status"] == "processing":
        st.info("🔄 Videos are being processed by Google...", icon="⏳")
        st.write("Click the button below to check the status. Once all videos are ready, the report will be generated.")
        if st.button("Check Status & Generate Report", use_container_width=True, key=f"check_button_{funnel_stage.lower()}"):
            all_files_ready = True
            with st.spinner("Checking file statuses..."):
                # ... (This status check block is the same as before) ...
                for file_info in st.session_state[session_state_key]["files"]:
                    if file_info["status"] == "processing":
                        api_file = genai.get_file(name=file_info["api_file_name"])
                        if api_file.state.name == "ACTIVE": file_info["status"] = "active"; st.success(f"✅ '{file_info['original_filename']}' is ready.")
                        elif api_file.state.name == "FAILED": file_info["status"] = "failed"; st.error(f"❌ Processing failed for '{file_info['original_filename']}'.")
                        else: all_files_ready = False; st.info(f"⏳ '{file_info['original_filename']}' is still processing...")

            if all_files_ready:
                with st.spinner("All files ready! Generating individual and final reports..."):
                    try:
                        individual_summaries, active_files = [], [f for f in st.session_state[session_state_key]["files"] if f["status"] == 'active']
                        
                        # Set up the models once
                        flash_model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
                        pro_model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

                        for file_info in active_files:
                            original_filename = file_info["original_filename"]
                            kpis = st.session_state[session_state_key]["kpis"].get(original_filename, {})
                            kpi_text = ", ".join([f"{k}: {v}" for k, v in kpis.items() if v])
                            
                            prompt = create_individual_analysis_prompt(original_filename, kpi_text)
                            api_file = genai.get_file(name=file_info["api_file_name"])
                            
                            # --- USE THE ROBUST CALLER ---
                            response = generate_with_retry(flash_model, [prompt, api_file])
                            individual_summaries.append(f"**Video: {original_filename}**\n{response.text}\n\n")

                        if individual_summaries:
                            synthesis_prompt = create_campaign_synthesis_prompt("".join(individual_summaries), funnel_stage)
                            
                            # --- USE THE ROBUST CALLER FOR THE FINAL REPORT ---
                            final_response = generate_with_retry(pro_model, synthesis_prompt)
                            
                            st.session_state[session_state_key]["final_report"] = final_response.text
                            st.session_state[session_state_key]["status"] = "complete"
                            
                            # Cleanup files
                            for file_info in st.session_state[session_state_key]["files"]:
                                try: genai.delete_file(name=file_info["api_file_name"])
                                except Exception: pass
                            st.rerun()
                    except Exception as e:
                        # This will catch the error if generate_with_retry finally fails
                        st.error("Failed to generate the final report after multiple attempts. Please try again later.")
                        # Optionally, reset the state to allow the user to try again
                        st.session_state[session_state_key]["status"] = "processing" # Go back to the check status page

    elif st.session_state[session_state_key]["status"] == "complete":
        parse_report_and_display(st.session_state[session_state_key].get("final_report", "Report not found."), st.session_state[session_state_key].get("kpis", {}))
        if st.button(f"↩️ Start New {funnel_stage} Analysis", use_container_width=True, key=f"reset_button_{funnel_stage.lower()}"):
            st.session_state[session_state_key] = {"status": "not_started", "files": [], "kpis": {}, "manual_kpis": {}}; st.rerun()

# --- Create the Tabs and Render Content ---
tab1, tab2, tab3 = st.tabs(["**Awareness**", "**Traffic**", "**Conversion**"])
with tab1: render_campaign_tab("Awareness")
with tab2: render_campaign_tab("Traffic")
with tab3: render_campaign_tab("Conversion")
