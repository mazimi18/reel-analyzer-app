# ===================================================================================
# FINAL v6.2 app.py - Enhanced UI/UX, Bonus AI Features, and Conversational Chatbot
# This version fixes the "start_chat() takes 1 positional argument" error.
# ===================================================================================
import os
import google.generativeai as genai
import streamlit as st
import time
import tempfile

# --- Configuration and Page Setup ---
st.set_page_config(
    page_title="AI Video Analyst",
    page_icon="🤖",
    layout="wide"
)

# --- Secret & API Configuration ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except (TypeError, KeyError):
    st.error("🚨 A required GOOGLE_API_KEY secret is missing! Please check your secrets.")
    st.stop()

# --- Session State Initialization ---
if "chat" not in st.session_state:
    st.session_state.chat = None
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "video_file_name" not in st.session_state:
    st.session_state.video_file_name = None

# --- AI and Helper Functions ---
METRIC_DEFINITIONS = {
    "Awareness": {"Impressions": "e.g., 5,000,000", "Cost Per Thousand (CPM)": "e.g., $2.50"},
    "Traffic": {"Click-Through Rate (CTR)": "e.g., 2.5%", "Cost Per Click (CPC)": "e.g., $0.50"},
    "Conversion": {"Purchases / Leads": "e.g., 500", "Return On Ad Spend (ROAS)": "e.g., 4.5x"}
}

def create_initial_prompt(funnel_stage, metrics, deeper_analysis_options):
    prompt = f"""
    You are an expert digital marketing and viral video analyst. Your task is to analyze a video and explain how its creative elements contribute to its reported Key Performance Indicators (KPIs).

    **Funnel Stage & KPIs to Analyze:**
    - Funnel Stage: {funnel_stage}
    - Reported Metrics: {metrics}

    **Your Analysis Must Include:**
    1.  **Opening Hook Analysis:** (First 3 seconds) How did it grab attention?
    2.  **Core Content Breakdown:** What techniques maintained engagement (e.g., quick cuts, text overlays, audio)?
    3.  **Call to Action (CTA) Evaluation:** Was the CTA clear and effective for the funnel stage?
    4.  **Creative-to-KPI Connection (Most Important):** Explicitly link creative elements to the reported metrics.
    5.  **Suggestions for Improvement:** Provide 2-3 actionable recommendations to improve the KPIs.
    """

    if "hooks" in deeper_analysis_options:
        prompt += "\n\n**6. Alternative Hooks:** Suggest 3 new, creative opening hooks for this video, explaining the strategy behind each."
    if "audience" in deeper_analysis_options:
        prompt += "\n\n**7. Target Audience Persona:** Based on the video's content and style, describe a detailed persona of the ideal target viewer (e.g., age, interests, pain points)."

    prompt += "\n\nStructure your entire response using clear headings and markdown for readability."
    return prompt

def main_analysis_and_chat_setup(video_path, funnel_stage, metrics, deeper_analysis_options, progress_bar):
    progress_bar.progress(10, text="Uploading video file to AI...")
    video_file = genai.upload_file(path=video_path)
    
    progress_bar.progress(30, text="File uploaded. Waiting for processing...")
    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = genai.get_file(video_file.name)
    if video_file.state.name == "FAILED":
        raise ValueError("Video processing failed.")
    
    st.session_state.video_file_name = video_file.name
    
    progress_bar.progress(60, text="Video processed. Generating initial analysis...")
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
    
    # [THE FIX IS HERE] Added the 'history=' keyword argument.
    st.session_state.chat = model.start_chat(history=[
        {"role": "user", "parts": [video_file, "Analyze this video based on my next instructions."]},
        {"role": "model", "parts": ["I have received the video. I am ready for your analysis instructions."]}
    ])

    initial_prompt = create_initial_prompt(funnel_stage, metrics, deeper_analysis_options)
    response = st.session_state.chat.send_message(initial_prompt)
    
    progress_bar.progress(100, text="Analysis complete!")
    return response.text

# --- Streamlit UI ---
st.title("🤖 AI Video Strategist")
st.markdown("Upload a video, provide its KPIs, and get a deep strategic analysis followed by a Q&A session with an AI expert.")

col1, col2 = st.columns([0.4, 0.6])

with col1:
    st.header("1. Upload & Configure")

    uploaded_file = st.file_uploader(
        "Upload your video file",
        type=["mp4", "mov", "avi", "m4v"]
    )
    
    if uploaded_file:
        st.video(uploaded_file)

    with st.expander("📈 Enter Performance KPIs", expanded=True):
        funnel_stage = st.selectbox("Primary Goal (Funnel Stage):", options=list(METRIC_DEFINITIONS.keys()))
        kpi_inputs = {}
        if funnel_stage:
            for kpi, placeholder in METRIC_DEFINITIONS[funnel_stage].items():
                kpi_inputs[kpi] = st.text_input(label=kpi, placeholder=placeholder)

    with st.expander("🧠 Add Deeper Analysis", expanded=False):
        deeper_analysis_options = st.multiselect(
            "Select additional analysis points:",
            options={
                "hooks": "Suggest Alternative Hooks",
                "audience": "Define Target Audience Persona"
            },
            format_func=lambda x: {
                "hooks": "Suggest Alternative Hooks",
                "audience": "Define Target Audience Persona"
            }.get(x)
        )

    analyze_button = st.button("✨ Analyze Video", type="primary", use_container_width=True)

with col2:
    st.header("2. AI Analysis & Chat")

    if analyze_button and uploaded_file:
        metrics_text = "\n".join([f"- {kpi}: {val}" for kpi, val in kpi_inputs.items() if val])
        if not metrics_text:
            st.warning("Please enter at least one KPI value for a meaningful analysis.")
        else:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    video_path = tmp_file.name
                
                progress_bar = st.progress(0, text="Starting...")
                initial_analysis = main_analysis_and_chat_setup(video_path, funnel_stage, metrics_text, deeper_analysis_options, progress_bar)
                
                st.session_state.analysis_complete = True
                st.session_state.messages.append({"role": "assistant", "content": initial_analysis})
                
                os.remove(video_path)
                st.rerun()

            except Exception as e:
                st.error(f"An error occurred: {e}")

    if st.session_state.analysis_complete:
        for message in st.session_state.messages:
            with st.chat_message(name=message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ask a follow-up question...", disabled=not st.session_state.analysis_complete):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    elif not st.session_state.analysis_complete:
        st.info("Your analysis and chat will appear here after you upload a video and click 'Analyze'.")
