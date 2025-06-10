# ==============================================================================
# FINAL v5 app.py CODE - Direct Video Upload for Analysis
# This version completely removes Instaloader and relies on direct user uploads.
# ==============================================================================
import os
import google.generativeai as genai
import streamlit as st
import time
import tempfile

# --- Configuration ---
# We only need the Gemini API key now. All Instagram secrets are removed.
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except (TypeError, KeyError):
    st.error("🚨 A required GOOGLE_API_KEY secret is missing! Please check your secrets.")
    st.stop()

# --- AI and Helper Functions (Largely Unchanged) ---
METRIC_DEFINITIONS = {
    "Awareness": {"Impressions": "e.g., 5,000,000", "Cost Per Thousand (CPM)": "e.g., $2.50"},
    "Traffic": {"Click-Through Rate (CTR)": "e.g., 2.5%", "Cost Per Click (CPC)": "e.g., $0.50", "Landing Page Views": "e.g., 25,000", "Cost Per Landing Page View": "e.g., $0.80"},
    "Conversion": {"Purchases / Leads": "e.g., 500", "Purchase Volume ($)": "e.g., $25,000", "Return On Ad Spend (ROAS)": "e.g., 4.5x", "Cost Per Acquisition (CPA)": "e.g., $50.00"}
}

def create_analysis_prompt(funnel_stage, metrics):
    # This function is unchanged. It creates the detailed prompt for the Gemini API.
    return f"""
    You are an expert digital marketing and viral video analyst. Your task is to analyze a video and explain how its creative elements contribute to its reported Key Performance Indicators (KPIs) for a specific marketing funnel stage.

    **Funnel Stage & KPIs to Analyze:**
    - Funnel Stage: {funnel_stage}
    - Reported Metrics:
    {metrics}

    **Your Analysis Must Include:**
    1.  **Opening Hook Analysis:** How did the first 3 seconds grab attention? Did it use a visual surprise, a question, a bold statement, or something else?
    2.  **Core Content Breakdown:** What techniques did the video use to maintain engagement? (e.g., quick cuts, text overlays, trending audio, storytelling, humor, tutorial style). Explain *why* these techniques work for the target funnel stage.
    3.  **Call to Action (CTA) Evaluation:** Was there a clear CTA? Was it visual, verbal, or in the caption? How effectively does it drive the desired action for the reported KPIs? (e.g., for a 'Traffic' goal, does it encourage a link click?).
    4.  **Creative-to-KPI Connection (Most Important):** Explicitly link specific visual or audio elements from the video to the reported metrics. For example: "The high CTR of 2.5% is likely driven by the compelling text overlay at 0:10 that says 'You won't believe this hack,' which creates curiosity and encourages users to click the link in the bio to learn more."
    5.  **Suggestions for Improvement:** Provide 2-3 actionable recommendations on how the creative could be optimized to improve the reported KPIs even further.

    Structure your response using clear headings and bullet points for readability. Be specific, insightful, and concise.
    """

def analyze_reel(video_path, funnel_stage, metrics, progress_bar):
    progress_bar.progress(10, text="Uploading video file to AI...")
    video_file = genai.upload_file(path=video_path)
    progress_bar.progress(30, text=f"File uploaded. Waiting for processing...")
    while video_file.state.name == "PROCESSING":
        time.sleep(5)
        video_file = genai.get_file(video_file.name)
    if video_file.state.name == "FAILED":
        raise ValueError("Video processing failed.")
    progress_bar.progress(60, text="Video processed. Calling Gemini for analysis...")
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    prompt = create_analysis_prompt(funnel_stage, metrics)
    response = model.generate_content([prompt, video_file])
    progress_bar.progress(90, text="Analysis received. Cleaning up...")
    genai.delete_file(video_file.name)
    progress_bar.progress(100, text="Done!")
    return response.text

# --- Streamlit UI ---
st.set_page_config(page_title="Reel KPI Analyzer", layout="wide")
st.title("🚀 Video KPI Analyzer")
st.markdown("Analyze how a video's creative drives specific marketing funnel KPIs.")
col1, col2 = st.columns(2)

with col1:
    st.header("1. Upload Your Video File")
    # NEW: File uploader instead of URL input
    uploaded_file = st.file_uploader(
        "Choose a video file...", 
        type=["mp4", "mov", "avi", "m4v"]
    )

    st.header("2. Provide Performance Metrics")
    funnel_stage = st.selectbox("Select the primary goal (funnel stage) of this video:", options=list(METRIC_DEFINITIONS.keys()))
    st.markdown("---")
    kpi_inputs = {}
    if funnel_stage:
        kpis_for_stage = METRIC_DEFINITIONS[funnel_stage]
        st.subheader(f"{funnel_stage} KPIs:")
        for kpi, placeholder in kpis_for_stage.items():
            kpi_inputs[kpi] = st.text_input(label=kpi, placeholder=placeholder)
            
    analyze_button = st.button("Analyze Video Performance", type="primary", use_container_width=True)

with col2:
    st.header("3. AI-Generated Performance Analysis")
    
    # REWIRED: Main logic now checks for an uploaded_file instead of a reel_url
    if analyze_button and uploaded_file:
        metrics_text = "\n".join([f"- {kpi}: {val}" for kpi, val in kpi_inputs.items() if val])
        if not metrics_text:
            st.warning("Please enter at least one KPI value.")
        else:
            try:
                # Save uploaded file to a temporary file on disk for stable processing
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    video_path = tmp_file.name

                progress_bar = st.progress(0, text="Starting analysis...")
                analysis_result = analyze_reel(video_path, funnel_stage, metrics_text, progress_bar)
                st.markdown(analysis_result)

            except Exception as e:
                st.error(f"An error occurred during the analysis: {e}")
            finally:
                # Clean up the temporary file
                if 'video_path' in locals() and os.path.exists(video_path):
                    os.remove(video_path)

    elif analyze_button and not uploaded_file:
        st.warning("Please upload a video file first.")
    else:
        st.info("Your performance analysis will appear here.")
