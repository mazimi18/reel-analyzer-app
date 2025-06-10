# ===================================================================================
# FINAL v7.1 app.py - Multi-Video Campaign Strategist (Multi-upload verified)
# This version ensures the file uploader is correctly configured for multiple files.
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

# --- Secret & API Configuration ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except (TypeError, KeyError):
    st.error("🚨 A required GOOGLE_API_KEY secret is missing! Please check your secrets.")
    st.stop()

# --- AI Prompt Engineering ---
def create_individual_analysis_prompt(filename, kpi_data):
    """Creates a prompt for a CONCISE analysis of a SINGLE video."""
    return f"""
    Analyze the creative of the video '{filename}'.
    
    **Reported KPIs:**
    {kpi_data}
    
    **Your Task:**
    Provide a brief, one-paragraph summary (under 80 words). Identify the single most impactful creative element that likely drove these results and explain why. Focus on actionable insights.
    """

def create_campaign_synthesis_prompt(all_individual_summaries):
    """Creates the master prompt to analyze the entire campaign based on individual summaries."""
    return f"""
    You are a world-class digital marketing campaign strategist. I have provided you with concise summaries of every video in a recent campaign, including their performance drivers.

    **Individual Video Summaries:**
    ---
    {all_individual_summaries}
    ---

    **Your Task:**
    Analyze the entire campaign based *only* on the summaries provided. Produce a strategic report with the following three sections, using clear markdown headings:

    ### 1. Campaign Performance Scorecard
    Create a simple table that ranks the videos from best to worst performing based on their summaries. Include the video name and a "Key Takeaway" for each.

    ### 2. Common Themes in Top Performers
    Identify 2-3 common creative elements, patterns, or strategies that the top-performing videos shared. For each theme, explain *why* you believe it resonated with the audience. This is the most important section.

    ### 3. Actionable Recommendations
    Based on your analysis, provide three clear, actionable recommendations for the next campaign to maximize performance.
    """

# --- Main App Logic ---
st.title("🏆 AI Campaign Strategist")
st.markdown("Upload all the videos from a campaign, add their KPIs, and discover the creative themes that drive success.")

if 'campaign_videos' not in st.session_state:
    st.session_state.campaign_videos = []

# --- UI for File Upload and Metric Input ---
# THE FIX IS HERE: 'accept_multiple_files=True' is included.
uploaded_files = st.file_uploader(
    "1. Upload all campaign videos (.mp4, .mov)",
    type=["mp4", "mov", "avi", "m4v"],
    accept_multiple_files=True
)

if uploaded_files:
    kpi_input_data = {}
    st.subheader("2. Enter KPIs for Each Video")

    for file in uploaded_files:
        with st.expander(f"Metrics for: **{file.name}**"):
            ctr = st.text_input("CTR (%)", key=f"ctr_{file.name}")
            cpc = st.text_input("CPC ($)", key=f"cpc_{file.name}")
            roas = st.text_input("ROAS (x)", key=f"roas_{file.name}")
            kpi_input_data[file.name] = {"CTR": ctr, "CPC": cpc, "ROAS": roas}
    
    analyze_button = st.button("🚀 Analyze Entire Campaign", type="primary", use_container_width=True)

    if analyze_button:
        st.session_state.campaign_videos = []
        for file in uploaded_files:
            kpis = {k: v for k, v in kpi_input_data[file.name].items() if v}
            if not kpis:
                st.warning(f"Skipping '{file.name}' as no KPIs were provided.")
                continue
            st.session_state.campaign_videos.append({"file_object": file, "kpis": kpis})

        # --- Two-Step AI Analysis Execution ---
        if st.session_state.campaign_videos:
            individual_summaries = []
            total_videos = len(st.session_state.campaign_videos)
            progress_bar = st.progress(0, text="Starting campaign analysis...")

            for i, video_data in enumerate(st.session_state.campaign_videos):
                file = video_data["file_object"]
                kpi_text = "\n".join([f"- {k}: {v}" for k, v in video_data["kpis"].items()])
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

            if individual_summaries:
                progress_bar.progress(0.9, text="Synthesizing campaign-level insights...")
                all_summaries_text = "".join(individual_summaries)
                model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
                synthesis_prompt = create_campaign_synthesis_prompt(all_summaries_text)
                final_response = model.generate_content(synthesis_prompt)
                
                progress_bar.progress(1.0, text="Campaign analysis complete!")
                st.subheader("🏆 Your Campaign Strategy Report")
                st.markdown(final_response.text)
            else:
                st.error("No videos were analyzed. Please check your inputs.")
                progress_bar.empty()
