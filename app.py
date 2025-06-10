# ===================================================================================
# FINAL v8.0 app.py - Tab-Based Multi-Video Campaign Strategist
# This version uses a tabbed interface for each funnel stage, with specific KPIs.
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

# --- Reusable Function to Render a Campaign Analysis Tab ---
def render_campaign_tab(funnel_stage, kpi_definitions):
    """
    Creates the entire UI and logic for a single tab.
    - funnel_stage: The name of the stage (e.g., "Awareness")
    - kpi_definitions: The dictionary of KPIs for that stage.
    """
    st.header(f"Analyze Your {funnel_stage} Campaign")

    # Each uploader needs a UNIQUE key to be treated independently by Streamlit
    uploaded_files = st.file_uploader(
        f"Upload all {funnel_stage} campaign videos",
        type=["mp4", "mov", "avi", "m4v"],
        accept_multiple_files=True,
        key=f"uploader_{funnel_stage.lower()}"
    )

    if uploaded_files:
        kpi_input_data = {}
        st.subheader("Enter KPIs for Each Video")

        for file in uploaded_files:
            with st.expander(f"Metrics for: **{file.name}**"):
                # Dynamically create input fields based on the tab's kpi_definitions
                kpi_input_data[file.name] = {
                    kpi: st.text_input(kpi, placeholder=placeholder, key=f"{kpi}_{file.name}_{funnel_stage}")
                    for kpi, placeholder in kpi_definitions.items()
                }
        
        # Each button also needs a UNIQUE key
        analyze_button = st.button(f"🚀 Analyze {funnel_stage} Campaign", type="primary", key=f"button_{funnel_stage.lower()}")

        if analyze_button:
            campaign_videos = []
            for file in uploaded_files:
                kpis = {k: v for k, v in kpi_input_data[file.name].items() if v}
                if not kpis:
                    st.warning(f"Skipping '{file.name}' as no KPIs were provided.")
                    continue
                campaign_videos.append({"file_object": file, "kpis": kpis})

            if campaign_videos:
                individual_summaries = []
                total_videos = len(campaign_videos)
                progress_bar = st.progress(0, text="Starting campaign analysis...")

                # Step 1: Micro-Analysis Loop
                for i, video_data in enumerate(campaign_videos):
                    file = video_data["file_object"]
                    kpi_text = ", ".join([f"{k}: {v}" for k, v in video_data["kpis"].items()])
                    progress_text = f"Analyzing video {i+1}/{total_videos}: {file.name}"
                    progress_bar.progress((i / total_videos), text=progress_text)
                    
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp_file:
                            tmp_file.write(file.getvalue())
                            video_path = tmp_file.name
                        
                        model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
                        prompt = create_individual_analysis_prompt(file.name, kpi_text)
                        video_file_for_api = genai.upload_file(path=video_path)
                        response = model.generate_content([prompt, video_file_for_api])
                        
                        summary = f"**Video: {file.name}**\n{response.text}\n\n"
                        individual_summaries.append(summary)
                        
                        os.remove(video_path)
                        genai.delete_file(video_file_for_api.name)
                    except Exception as e:
                        st.error(f"Error analyzing '{file.name}': {e}")
                        individual_summaries.append(f"**Video: {file.name}**\nAnalysis failed.\n\n")

                # Step 2: Macro-Synthesis
                if individual_summaries:
                    progress_bar.progress(0.9, text="Synthesizing campaign-level insights...")
                    all_summaries_text = "".join(individual_summaries)
                    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
                    synthesis_prompt = create_campaign_synthesis_prompt(all_summaries_text)
                    final_response = model.generate_content(synthesis_prompt)
                    
                    progress_bar.progress(1.0, text="Campaign analysis complete!")
                    st.subheader(f"🏆 Your {funnel_stage} Campaign Strategy Report")
                    st.markdown(final_response.text)

# --- Create the Tabs and Render Content ---
tab1, tab2, tab3 = st.tabs(["Awareness Campaigns", "Traffic Campaigns", "Conversion Campaigns"])

with tab1:
    render_campaign_tab("Awareness", CAMPAIGN_METRICS["Awareness"])

with tab2:
    render_campaign_tab("Traffic", CAMPAIGN_METRICS["Traffic"])

with tab3:
    render_campaign_tab("Conversion", CAMPAIGN_METRICS["Conversion"])
