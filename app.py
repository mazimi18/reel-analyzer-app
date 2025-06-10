# ===================================================================================
# FINAL v18.0 app.py - Strategic Scaling Logic & Video Previews
# This version enhances the AI's core logic to understand the value of "scaling"
# and re-introduces video previews for a better user experience.
# ===================================================================================
import os
import io
import re
import json
import google.generativeai as genai
import streamlit as st
import pandas as pd
import tempfile
import time

# --- 1. PAGE CONFIG & STYLING (MUST BE FIRST) ---
st.set_page_config(
    page_title="AI Campaign Strategist",
    page_icon="🎬",
    layout="wide"
)

# Custom CSS for YouTube dark theme
def apply_youtube_style():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
            html, body, [class*="st-"] { font-family: 'Roboto', sans-serif; }
            .stApp { background-color: #0f0f0f; color: #f1f1f1; }
            h1, h2, h3 { color: #ffffff !important; }
            .st-emotion-cache-1r6slb0, .st-emotion-cache-1bp2ih8 {
                background-color: #181818; border: 1px solid #383838; border-radius: 12px; padding: 1rem;
            }
            .stButton > button {
                background-color: #c00; color: white; border-radius: 18px; border: 1px solid #c00;
                padding: 8px 16px; font-weight: 500;
            }
            .stButton > button:hover { background-color: #990000; border-color: #990000; color: white; }
            .st-emotion-cache-1gulkj5 button[aria-selected="true"] { background-color: #ffffff; color: #0f0f0f; }
        </style>
    """, unsafe_allow_html=True)

apply_youtube_style()

# --- 2. THE REST OF YOUR APP STARTS HERE ---
st.title("🎬 AI Campaign Strategist")
st.markdown("##### Upload your campaign videos and metrics to get an expert-level report on what creative works... and *why*.")

# --- Secret & API Configuration ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except (TypeError, KeyError):
    st.error("🚨 A required GOOGLE_API_KEY secret is missing!", icon="❗")
    st.stop()

# --- AI PROMPT ENGINEERING 5.0 (Scaling Logic) ---
def create_comprehensive_analysis_prompt(all_kpi_data, funnel_stage):
    priority_metrics = {
        "Awareness": "impressions, high Video View Rate, and low CPM",
        "Traffic": "high Click-Through Rate (CTR) and low Cost Per Click (CPC)",
        "Conversion": "high Return On Ad Spend (ROAS), high number of Purchases/Leads, and low Cost Per Acquisition (CPA)"
    }
    video_data_string = ""
    for filename, kpis in all_kpi_data.items():
        kpi_string = ", ".join([f"{k}: {v}" for k, v in kpis.items()])
        video_data_string += f"- **Video File:** `{filename}`\n  - **Performance Metrics:** {kpi_string}\n\n"

    return f"""
    You are a world-class digital marketing and creative strategist. Your analysis must be nuanced and reflect real-world performance marketing principles.

    **Primary Goal:** Analyze the provided video files and performance metrics for a '{funnel_stage}' campaign to identify winning creative strategies.

    **Nuanced Performance Analysis (VERY IMPORTANT):**
    You must understand the concept of **"scaling."** A video that achieves a high spend and high volume of desired actions (like clicks or purchases) has proven its ability to scale.
    - **Do not automatically penalize a video for a slightly higher efficiency metric (like CPC or CPA) if it has significantly higher spend and volume.**
    - For example, a video with $5,000 spend and a $1.50 CPC is often **more valuable** than a video with $50 spend and a $1.00 CPC, because the former has proven it works with a large budget.
    - Mention this "ability to scale" in your ranking justification when relevant.

    **Campaign Data:**
    ---
    {video_data_string}
    ---

    **Your Comprehensive Task:**
    Generate a final strategic report with FIVE sections.

    **IMPORTANT FORMATTING INSTRUCTION:**
    For Section 1, "Campaign Performance Scorecard," you MUST provide the output as a single, valid JSON array of objects. Each object needs three keys: "rank" (integer), "video_name" (string), and "justification" (string). Enclose the entire JSON block in ```json ... ```.

    For all other sections, use standard H3 markdown headers (e.g., ### 2. Section Name).

    **SECTION 1: CAMPAIGN PERFORMANCE SCORECARD (JSON ARRAY)**
    ```json
    [
      {{"rank": 1, "video_name": "example_video_1.mp4", "justification": "This video ranked first due to its outstanding ROAS of 7.2, directly aligning with the conversion goal. The clear product shot in the first 3 seconds likely drove this performance."}},
      {{"rank": 2, "video_name": "example_video_2.mp4", "justification": "While having a slightly higher CPA, this ad proved its ability to scale by handling over $5,000 in spend while maintaining a strong 4.5 ROAS. This makes it a highly valuable creative."}}
    ]
    ```

    ### 2. Common Themes in Top Performers
    (Your analysis here...)

    ### 3. Actionable Recommendations
    (Your analysis here...)

    ### 4. New Creative Ideas (Ad Scripts)
    (Your analysis here...)

    ### 5. Suggested Ad Copy
    (Your analysis here...)
    """

def create_chatbot_prompt(report_text):
    return f"""You are a helpful AI assistant. Your ONLY job is to answer questions about the following marketing report. Do not answer questions outside the scope of this report. Be concise and helpful.
    **THE REPORT:**
    ---
    {report_text}
    ---
    """

# --- UI HELPER FUNCTIONS ---
def parse_report_and_display(report_text, all_kpis):
    # This robust JSON-based parser is unchanged
    st.subheader("🏆 Strategic Campaign Report", anchor=False)
    try:
        json_match = re.search(r"```json\s*\n([\s\S]*?)\n```", report_text)
        if json_match:
            json_string = json_match.group(1)
            scorecard_data = json.loads(json_string)
            scorecard_df = pd.DataFrame(scorecard_data)
            scorecard_df.rename(columns={'rank': 'Rank', 'video_name': 'Video Name', 'justification': 'Ranking Justification'}, inplace=True)
            
            top_video_name = scorecard_df['Video Name'].iloc[0]
            top_kpis = all_kpis.get(top_video_name, {})
            
            st.subheader(f"🥇 Top Performer: {top_video_name}")
            if top_kpis:
                 with st.container(border=True):
                    cols = st.columns(len(top_kpis) if len(top_kpis) <= 4 else 4)
                    for i, (k, v) in enumerate(top_kpis.items()):
                        if i < 4: cols[i].metric(label=k, value=v)

            with st.expander("**Campaign Performance Scorecard**", expanded=True):
                st.dataframe(scorecard_df, use_container_width=True, hide_index=True)
        else:
            raise ValueError("No JSON block found for the scorecard.")
    except Exception as e:
        st.error(f"Could not parse top performer data or scorecard. Error: {e}", icon="🚨")
        scorecard_raw_match = re.search(r"### 1\..*Scorecard\s*\n*(.*?)(\n###|$)", report_text, re.DOTALL | re.IGNORECASE)
        if scorecard_raw_match:
            st.text(scorecard_raw_match.group(1).strip())

    report_sections = re.findall(r"### (2|3|4|5)\. (.*?)\n(.*?)(?=\n### |\Z)", report_text, re.DOTALL)
    for num, title, content in report_sections:
        with st.expander(f"**{num}. {title.strip()}**"):
            st.markdown(content.strip())

# --- MAIN APP LOGIC ---
def render_campaign_tab(funnel_stage):
    session_state_key = f"analysis_state_{funnel_stage}"
    if session_state_key not in st.session_state:
        st.session_state[session_state_key] = {
            "status": "not_started", "files": [], "kpis": {}, "manual_kpis": {}, "chat_messages": []
        }
    
    # State 1: Upload
    if st.session_state[session_state_key]["status"] == "not_started":
        with st.container(border=True):
            st.subheader("Step 1: Upload Assets", anchor=False)
            col1, col2 = st.columns(2)
            with col1: uploaded_files = st.file_uploader("Upload campaign videos", type=["mp4", "mov", "avi", "m4v"], accept_multiple_files=True, key=f"uploader_{funnel_stage.lower()}")
            with col2: kpi_csv_file = st.file_uploader("Upload a CSV with metrics (Optional)", type="csv", key=f"csv_uploader_{funnel_stage.lower()}", help="Must have a 'filename' column.")
        if uploaded_files:
            parsed_kpis_from_csv = {}
            if kpi_csv_file:
                try:
                    df = pd.read_csv(kpi_csv_file).astype(str)
                    if 'filename' not in df.columns: st.error("CSV Error: Missing 'filename' column.", icon="❌")
                    else: parsed_kpis_from_csv = df.set_index('filename').to_dict('index'); st.success("✅ Metrics CSV loaded!", icon="🎉")
                except Exception as e: st.error(f"Error reading CSV file: {e}", icon="❌")
            
            with st.container(border=True):
                st.subheader("Step 2: Verify Metrics & Preview Videos", anchor=False)
                kpi_input_data = {}
                for file in uploaded_files:
                    with st.expander(f"Metrics for: **{file.name}**"):
                        # --- NEW: VIDEO PREVIEW PANE ---
                        st.video(file)
                        st.markdown("---") # Visual separator
                        
                        basename, _ = os.path.splitext(file.name)
                        file_kpis_from_csv = parsed_kpis_from_csv.get(file.name) or parsed_kpis_from_csv.get(basename)
                        if file_kpis_from_csv:
                            temp_kpis = {}
                            cols = st.columns(3)
                            for i, (k, v) in enumerate(file_kpis_from_csv.items()):
                                with cols[i % 3]: temp_kpis[k] = st.text_input(f"**{k}**", value=v, key=f"csv_{k}_{file.name}_{funnel_stage}")
                            kpi_input_data[file.name] = temp_kpis
                        else:
                            # ... manual entry logic is unchanged ...
                            st.info("No CSV data for this file. Add metrics manually.", icon="✍️")
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
                # ... This logic is unchanged and robust for paid tier ...
                st.session_state[session_state_key]["kpis"] = kpi_input_data
                files_to_process = [f for f in uploaded_files if any(kpi_input_data.get(f.name, {}).values())]
                if not files_to_process:
                    st.error("No videos with KPIs found to analyze.")
                else:
                    with st.spinner("Uploading videos to secure storage..."):
                        for file in files_to_process:
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
                                    tmp.write(file.getvalue())
                                video_file_for_api = genai.upload_file(path=tmp.name)
                                st.session_state[session_state_key]["files"].append({"original_filename": file.name, "api_file_name": video_file_for_api.name, "status": "processing"})
                                os.remove(tmp.name)
                            except Exception as e: st.error(f"Failed to upload '{file.name}': {e}")
                    st.session_state[session_state_key]["status"] = "processing"; st.rerun()

    # State 2: Processing
    elif st.session_state[session_state_key]["status"] == "processing":
        # ... This logic is unchanged and robust for paid tier ...
        st.info("🔄 Videos are being processed... Click below when ready.", icon="⏳")
        if st.button("Check Status & Generate Report", use_container_width=True, key=f"check_button_{funnel_stage.lower()}"):
            all_files_ready = True
            with st.spinner("Checking file statuses..."):
                for file_info in st.session_state[session_state_key]["files"]:
                    if file_info["status"] == "processing":
                        api_file = genai.get_file(name=file_info["api_file_name"])
                        if api_file.state.name == "ACTIVE": file_info["status"] = "active"; st.success(f"✅ '{file_info['original_filename']}' is ready.")
                        elif api_file.state.name == "FAILED": file_info["status"] = "failed"; st.error(f"❌ Processing failed for '{file_info['original_filename']}'.")
                        else: all_files_ready = False; st.info(f"⏳ '{file_info['original_filename']}' is still processing...")
            if all_files_ready:
                with st.spinner("All files ready! Sending campaign to AI for comprehensive analysis... This may take several minutes."):
                    try:
                        active_files_info = [f for f in st.session_state[session_state_key]["files"] if f["status"] == 'active']
                        kpis_for_prompt = {info['original_filename']: st.session_state[session_state_key]['kpis'][info['original_filename']] for info in active_files_info}
                        synthesis_prompt = create_comprehensive_analysis_prompt(kpis_for_prompt, funnel_stage)
                        prompt_parts = [synthesis_prompt]
                        for file_info in active_files_info:
                            prompt_parts.append(genai.get_file(name=file_info["api_file_name"]))
                        model = genai.GenerativeModel(model_name="gemini-1.5-pro")
                        final_response = model.generate_content(prompt_parts)
                        st.session_state[session_state_key]["final_report"] = final_response.text
                        st.session_state[session_state_key]["status"] = "complete"
                        for file_info in st.session_state[session_state_key]["files"]:
                            try: genai.delete_file(name=file_info["api_file_name"])
                            except Exception: pass
                        st.rerun()
                    except Exception as e:
                        st.error(f"An error occurred during analysis: {e}")
                        st.session_state[session_state_key]["status"] = "processing"

    # State 3: Complete (Report & Chatbot)
    elif st.session_state[session_state_key]["status"] == "complete":
        main_col, chat_col = st.columns([2, 1])
        with main_col:
            parse_report_and_display(st.session_state[session_state_key].get("final_report", ""), st.session_state[session_state_key].get("kpis", {}))
        with chat_col:
            with st.container(border=True):
                st.subheader("💬 Chat with your Report")
                for message in st.session_state[session_state_key]["chat_messages"]:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
                if prompt := st.chat_input("E.g., 'Which video had the best CTR?'"):
                    st.session_state[session_state_key]["chat_messages"].append({"role": "user", "content": prompt})
                    with st.chat_message("user"): st.markdown(prompt)
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            try:
                                chatbot_model = genai.GenerativeModel(model_name="gemini-1.5-pro")
                                chat = chatbot_model.start_chat(history=[
                                    {'role': 'user', 'parts': [create_chatbot_prompt(st.session_state[session_state_key]["final_report"])]},
                                    {'role': 'model', 'parts': ["Understood. I will only answer questions about the provided report."]}
                                ])
                                response = chat.send_message(prompt)
                                st.markdown(response.text)
                                st.session_state[session_state_key]["chat_messages"].append({"role": "assistant", "content": response.text})
                            except Exception as e: st.error(f"Sorry, I couldn't process that. Error: {e}")
        if st.button("↩️ Start New Analysis", use_container_width=True, key=f"reset_button_{funnel_stage.lower()}"):
            st.session_state[session_state_key] = {"status": "not_started", "files": [], "kpis": {}, "manual_kpis": {}, "chat_messages": []}; st.rerun()

# --- Create the Main App Layout ---
tab1, tab2, tab3 = st.tabs(["**Awareness**", "**Traffic**", "**Conversion**"])
with tab1: render_campaign_tab("Awareness")
with tab2: render_campaign_tab("Traffic")
with tab3: render_campaign_tab("Conversion")
    
