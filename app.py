import os
import google.generativeai as genai
import streamlit as st
import time

# --- Configuration ---
# Streamlit secrets management for the API key
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except (TypeError, KeyError):
    st.error("🚨 Google API key not found. Please add it to your Streamlit secrets (`.streamlit/secrets.toml`).")
    st.stop()

# --- Data Structure for Funnel Stages and KPIs ---
# This dictionary drives the dynamic UI. Add or change items here to update the app.
METRIC_DEFINITIONS = {
    "Awareness": {
        "Impressions": "e.g., 5,000,000",
        "Cost Per Thousand (CPM)": "e.g., $2.50"
    },
    "Traffic": {
        "Click-Through Rate (CTR)": "e.g., 2.5%",
        "Cost Per Click (CPC)": "e.g., $0.50",
        "Landing Page Views": "e.g., 25,000",
        "Cost Per Landing Page View": "e.g., $0.80"
    },
    "Conversion": {
        "Purchases / Leads": "e.g., 500",
        "Purchase Volume ($)": "e.g., $25,000",
        "Return On Ad Spend (ROAS)": "e.g., 4.5x",
        "Cost Per Acquisition (CPA)": "e.g., $50.00"
    }
}

# --- AI Prompt Generation ---
def create_analysis_prompt(funnel_stage, metrics):
    """Creates a more advanced, business-focused prompt for the Gemini model."""
    return f"""
    You are an expert digital marketing and viral video analyst. Your task is to analyze the provided Instagram Reel and its performance metrics to identify how the creative elements contribute to its success for a specific marketing objective.

    **Marketing Objective / Funnel Stage:** {funnel_stage}

    **Key Performance Indicators (KPIs):**
    {metrics}

    **Analysis Task:**
    Based on the video content and the provided KPIs, provide a detailed breakdown in the following structure. Be critical, specific, and connect creative choices directly to business outcomes.

    **1. Hook Analysis (First 3 Seconds):**
    - **Description:** Describe the visual and auditory elements of the first three seconds.
    - **Hook Type:** Does it use a pain point, a surprising statement, a question, or a visually captivating shot?
    - **Effectiveness for {funnel_stage} (1-10):** Rate the hook's effectiveness *specifically for the goal of {funnel_stage}* and explain why. (e.g., "A hook for Awareness might be visually shocking, while a hook for Conversion might state a clear product benefit.")

    **2. Video Structure and Pacing:**
    - **Sections:** Identify the main sections (e.g., intro, problem, solution, CTA).
    - **Pacing:** Describe the pacing. Is it fast with quick cuts, or slower? How does this pacing serve the {funnel_stage} goal?
    - **Branding/Product Placement:** Where and how are branding or products shown? Is it effective and non-intrusive?

    **3. Content & Creative Analysis:**
    - **Core Message:** What is the core message? How does it align with the {funnel_stage} objective?
    - **Value Proposition:** Does it clearly communicate value (educational, entertaining, problem-solving)?
    - **Creative Strategy:** Analyze the storytelling, visuals, and audio. Why did these specific creative choices lead to the provided KPIs? (e.g., "The quick cuts and trending audio likely drove high Impressions and a low CPM for Awareness.")

    **4. Engagement & Conversion Triggers:**
    - **Call to Action (CTA):** Is there a clear CTA? Is it verbal, text-based, or visual? Is it appropriate for the {funnel_stage} goal? (e.g., a "link in bio" CTA is for Traffic/Conversion, while "Follow for more" is for Awareness).
    - **Audience Prompts:** Are there any questions or prompts to the audience?
    - **Emotional Response:** What emotions does the content evoke (e.g., trust, urgency, FOMO, humor)? How do these emotions drive the desired user action?

    **5. Overall Performance Score & Recommendations:**
    - **Score for Objective (1-10):** Based on your complete analysis, score how well this video's creative is optimized for its {funnel_stage} goal.
    - **Top 3 Reasons for Score:** Summarize the top 3 creative elements that most impacted the provided KPIs.
    - **Actionable Recommendation:** Provide one key recommendation for how to improve the next video for this same objective.
    """

# --- Core Gemini Analysis Function (No changes needed here) ---
def analyze_reel(video_path, funnel_stage, metrics, progress_bar):
    """Uploads the video and gets the analysis from Gemini."""
    progress_bar.progress(10, text="Uploading video file...")
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

# --- Streamlit App UI ---
st.set_page_config(page_title="Reel KPI Analyzer", layout="wide")

st.title("🚀 Instagram Reel KPI Analyzer")
st.markdown("Analyze how a Reel's creative drives specific marketing funnel KPIs.")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Upload Your Reel")
    uploaded_file = st.file_uploader("Choose a video file (.mp4, .mov)", type=["mp4", "mov"])

    st.header("2. Provide Performance Metrics")
    
    # --- DYNAMIC UI SECTION ---
    funnel_stage = st.selectbox(
        "Select the primary goal (funnel stage) of this Reel:",
        options=list(METRIC_DEFINITIONS.keys())
    )

    st.markdown("---") # Visual separator

    # Store the user's KPI inputs in a dictionary
    kpi_inputs = {}
    if funnel_stage:
        # Get the list of KPIs for the selected stage
        kpis_for_stage = METRIC_DEFINITIONS[funnel_stage]
        st.subheader(f"{funnel_stage} KPIs:")
        for kpi, placeholder in kpis_for_stage.items():
            kpi_inputs[kpi] = st.text_input(label=kpi, placeholder=placeholder)
    
    analyze_button = st.button("Analyze Reel Performance", type="primary", use_container_width=True)

with col2:
    st.header("3. AI-Generated Performance Analysis")
    if analyze_button and uploaded_file:
        # Save the uploaded file temporarily
        with open("temp_video.mp4", "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Format the collected KPIs into a clean string for the prompt
        metrics_text = "\n".join([f"- {kpi}: {val}" for kpi, val in kpi_inputs.items() if val])
        
        if not metrics_text:
            st.warning("Please enter at least one KPI value.")
        else:
            progress_bar = st.progress(0, text="Starting analysis...")
            try:
                with st.spinner('AI is thinking... This may take a minute.'):
                    analysis_result = analyze_reel("temp_video.mp4", funnel_stage, metrics_text, progress_bar)
                st.markdown(analysis_result)
            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                # Clean up the temporary file
                if os.path.exists("temp_video.mp4"):
                    os.remove("temp_video.mp4")

    elif analyze_button and not uploaded_file:
        st.warning("Please upload a video file first.")
    else:
        st.info("Your performance analysis will appear here.")