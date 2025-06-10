# ==============================================================================
# FINAL v6 app.py CODE - Advanced UI, Deeper Analysis & Conversational Chatbot
# ==============================================================================
import os
import google.generativeai as genai
import streamlit as st
import time
import tempfile

# --- Configuration & Page Setup ---
st.set_page_ video.
        *   Writing 2 sample captions.
        *   Proposing an A/B test.

3.  **Follow-up Chatbot:**
    *   After the initial analysis is complete, a new chat interface will appear.
    *   This chatbot will "remember" the video and its analysis, allowing you to ask specific follow-up questions like, "Can you elaborate on the CTA suggestion?" or "What kind of music would be better?".

This requires a significant update to the code to manage state (the app's memory) and a more sophisticated UI layout.

---

### Final, Enhanced `app.py` (v6 - UI/UX, More AI, Chatbot)

**Instructions:**
This is the new, final code. Replace the entire content of your `app.py` on GitHub with this code.

```python
# ===================================================================================
# FINAL v6 app.py - Enhanced UI/UX, Bonus AI Features, and Conversational Chatbot
# ===================================================================================
import os
import google.generativeai as genai
import streamlit as st
import time
import tempfile

# --- Configuration and Page Setup ---
st.set_page_config(page_title="Viral Video Analyst", layout="wide", initial_sidebar_state="collapsed")

# --- Authentication ---
# We only need the Gemini API key.
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except (TypeError, KeyError):
    st.error("🚨 A required GOOGLE_API_KEY secret is missing! Please check your secrets.")config(
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
# This is crucial for storing the chat history and the analysis context.
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
    # [ENHANCED] Now dynamically adds requests for deeper analysis to the prompt.
    prompt = f"""
    You are an expert digital marketing and viral video analyst. Your task is to analyze a video and explain how its creative elements contribute to its reported Key Performance Indicators (KPIs).

    **Funnel Stage & KPIs to Analyze:**
    - Funnel Stage: {funnel_stage}
    - Reported Metrics: {metrics}

    **Your Analysis Must Include:**
    1.  **Opening Hook Analysis:** (First 3 seconds) How did it grab attention?
    2.  **Core Content Breakdown:** What
    st.stop()

# --- Session State Initialization ---
# This is crucial for storing data across reruns (e.g., chat history, analysis results)
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
    st.session_state.initial_analysis = techniques maintained engagement (e.g., quick cuts, text overlays, audio)?
    3.  **Call to Action (CTA) Evaluation:** Was the CTA clear and effective for the funnel stage?
    4.  **Creative-to-KPI Connection (Most Important):** Explicitly link creative elements to the reported metrics.
    5.  **Suggestions for Improvement:** Provide 2-3 actionable recommendations to improve the KPIs.
    """

    if "hooks" in deeper_ ""
    st.session_state.chat_history = []
    st.session_state.video_path = None


# --- AI and Helper Functions ---
METRIC_DEFINITIONS = {
    "Awareness": {"Impressions": "e.g., 5,000,000", "Cost Per Thousand (CPM)": "e.g., $2.50"},
    "Traffic": {"Click-Through Rate (CTR)": "e.g., 2.5%", "Cost Per Click (CPC)": "e.g., $0.50", "Landing Page Views": "e.g., 25,000", "Cost Per Landing Page View": "e.g., $0.80"},
analysis_options:
        prompt += "\n\n**6. Alternative Hooks:** Suggest 3 new, creative opening hooks for this video, explaining the strategy behind each."
    if "audience" in deeper_analysis_options:    "Conversion": {"Purchases / Leads": "e.g., 500", "Purchase Volume ($)": "e.g., $25,000", "Return On Ad Spend (ROAS)
        prompt += "\n\n**7. Target Audience Persona:** Based on the video's content and style, describe": "e.g., 4.5x", "Cost Per Acquisition (CPA)": "e. a detailed persona of the ideal target viewer (e.g., age, interests, pain points)."

    prompt += "\n\g., $50.00"}
}

def create_initial_analysis_prompt(funnel_nStructure your entire response using clear headings and markdown for readability."
    return prompt

def main_analysis_andstage, metrics, bonus_features):
    # This prompt now includes a section for the selected bonus features.
    bonus_prompt_section = ""
    if bonus_features:
        bonus_prompt_section = "\n\n**Bonus_chat_setup(video_path, funnel_stage, metrics, deeper_analysis_options, progress_bar):
 Analysis Tasks:**\nIn addition to the main analysis, please provide the following:\n"
        for feature in bonus    progress_bar.progress(10, text="Uploading video file to AI...")
    video_file = genai_features:
            bonus_prompt_section += f"- {feature}\n"

    return f"""
.upload_file(path=video_path)
    
    progress_bar.progress(30,    You are an expert digital marketing and viral video analyst. Your task is to analyze a video and explain how its creative elements contribute text="File uploaded. Waiting for processing...")
    while video_file.state.name == "PROCESSING":
        time. to its reported Key Performance Indicators (KPIs) for a specific marketing funnel stage.

    **Funnel Stage &sleep(2)
        video_file = genai.get_file(video_file.name)
    if video KPIs to Analyze:**
    - Funnel Stage: {funnel_stage}
    - Reported Metrics:
_file.state.name == "FAILED":
        raise ValueError("Video processing failed.")
    
    st    {metrics}

    **Your Analysis Must Include:**
    1.  **Opening Hook Analysis:** How did.session_state.video_file_name = video_file.name # Store for cleanup
    
    progress_bar the first 3 seconds grab attention?
    2.  **Core Content Breakdown:** What techniques did the video use.progress(60, text="Video processed. Generating initial analysis...")
    model = genai.GenerativeModel(model to maintain engagement? (e.g., quick cuts, text overlays, trending audio, storytelling).
    3.  **Call_name="gemini-1.5-pro-latest")
    
    # [NEW] Start a to Action (CTA) Evaluation:** Was there a clear CTA? How effective is it for the reported KPIs?
     chat session that includes the video context for follow-ups
    st.session_state.chat = model.start_chat4.  **Creative-to-KPI Connection (Most Important):** Explicitly link specific visual or audio elements to([
        {"role": "user", "parts": [video_file, "Analyze this video based on my the reported metrics.
    5.  **Suggestions for Improvement:** Provide 2-3 actionable recommendations to improve the next instructions."]},
        {"role": "model", "parts": ["I have received the video. I am ready creative.

    Structure your response using clear headings and bullet points.{bonus_prompt_section}
    """

def for your analysis instructions."]}
    ])

    initial_prompt = create_initial_prompt(funnel_stage analyze_video(video_path, prompt):
    # This is a more generic analysis function.
    model, metrics, deeper_analysis_options)
    response = st.session_state.chat.send_message(initial = genai.GenerativeModel(model_name="gemini-1.5-flash")
    st.write("Uploading video file to AI...")
    video_file = genai.upload_file(path=video__prompt)
    
    progress_bar.progress(100, text="Analysis complete!")
    returnpath)
    
    st.write("Waiting for video processing...")
    while video_file.state. response.text

# --- Streamlit UI ---
st.title("🤖 AI Video Strategist")
st.markdownname == "PROCESSING":
        time.sleep(5)
        video_file = genai.get_file(video_file.name)
    
    if video_file.state.name == "FAILED":
        raise("Upload a video, provide its KPIs, and get a deep strategic analysis followed by a Q&A session with an ValueError("AI video processing failed.")
    
    st.write("Video processed. Generating analysis...")
    response = AI expert.")

# --- UI Column 1: Inputs and Controls ---
col1, col2 = st.columns([ model.generate_content([prompt, video_file])
    
    # We will not delete the file yet0.4, 0.6])
with col1:
    st.header("1. Upload &, so the chatbot can reference it.
    return response.text, video_file.name


# --- Stream Configure")

    uploaded_file = st.file_uploader(
        "Upload your video file",
        type=["lit UI ---
st.title("🤖 Viral Video Analyst Pro")
st.markdown("From analysis to conversation, getmp4", "mov", "avi", "m4v"]
    )
    
    if uploaded_ deep insights into your video's performance.")

tab1, tab2 = st.tabs(["📊 Initial Analysis", "💬file:
        st.video(uploaded_file) # [UI ENHANCEMENT] Show the uploaded video

    with Chat & Explore"])

# --- TAB 1: Initial Analysis ---
with tab1:
    col1, col2 st.expander("📈 Enter Performance KPIs", expanded=True): # [UI ENHANCEMENT] KPIs in a collapsible = st.columns(2)
    with col1:
        st.header("1️⃣ Upload & Configure section
        funnel_stage = st.selectbox("Primary Goal (Funnel Stage):", options=list(METRIC_")
        uploaded_file = st.file_uploader(
            "Choose a video file...", 
            typeDEFINITIONS.keys()))
        kpi_inputs = {}
        if funnel_stage:
            for kpi, placeholder=["mp4", "mov", "avi", "m4v"]
        )
        
        if uploaded_file: in METRIC_DEFINITIONS[funnel_stage].items():
                kpi_inputs[kpi] = st.text_input(label=kpi, placeholder=placeholder)

    with st.expander("🧠
            st.video(uploaded_file)

        with st.expander("Enter Performance Metrics", expanded=True):
 Add Deeper Analysis", expanded=False): # [NEW FEATURE]
        deeper_analysis_options = st            funnel_stage = st.selectbox("Primary Goal (Funnel Stage):", options=list(METRIC_DEFINITIONS.keys()))
            kpi_inputs = {}
            if funnel_stage:
                kpis.multiselect(
            "Select additional analysis points:",
            options={
                "hooks": "Suggest_for_stage = METRIC_DEFINITIONS[funnel_stage]
                for kpi, placeholder in Alternative Hooks",
                "audience": "Define Target Audience Persona"
            },
            format_func=lambda x kpis_for_stage.items():
                    kpi_inputs[kpi] = st.text_: {
                "hooks": "Suggest Alternative Hooks",
                "audience": "Define Target Audience Persona"
            input(label=kpi, placeholder=placeholder)
        
        with st.expander("Select Bonus AI Features"):
            bonus_features = st.multiselect(
                "Choose additional AI-powered tasks:",
                [
                    }.get(x)
        )

    analyze_button = st.button("✨ Analyze Video", type="primary","Suggest 3 alternative viral hooks for this video.",
                    "Write 2 sample captions for this video optimized for engagement.",
 use_container_width=True)


# --- UI Column 2: Analysis and Chat Output ---
with col2:
    st.header("2. AI Analysis & Chat")

    # Main logic block
    if analyze                    "Propose a simple A/B test to improve a key metric.",
                    "Identify the likely target audience demographic_button and uploaded_file:
        metrics_text = "\n".join([f"- {kpi}: {val for this content."
                ]
            )

        analyze_button = st.button("🚀 Analyze Video",}" for kpi, val in kpi_inputs.items() if val])
        if not metrics_text type="primary", use_container_width=True)

    with col2:
        st.header(":
            st.warning("Please enter at least one KPI value for a meaningful analysis.")
        else:
📈 AI-Generated Report")
        if analyze_button and uploaded_file:
            metrics_text = "\            try:
                # Save to a temporary file for stable processing by the API
                with tempfile.NamedTemporaryFile(n".join([f"- {kpi}: {val}" for kpi, val in kpi_inputs.delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_fileitems() if val])
            if not metrics_text:
                st.warning("Please enter at least one KPI value:
                    tmp_file.write(uploaded_file.getvalue())
                    video_path = tmp_file for a meaningful analysis.")
            else:
                with st.spinner("Performing deep analysis... This may take a moment.name
                
                # Run the main analysis
                progress_bar = st.progress(0, text."):
                    try:
                        # Save uploaded file to a temporary location
                        with tempfile.NamedTemporary="Starting...")
                initial_analysis = main_analysis_and_chat_setup(video_path, funnelFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_stage, metrics_text, deeper_analysis_options, progress_bar)
                
                # Set flags_file:
                            tmp_file.write(uploaded_file.getvalue())
                            st.session_state and store the first message
                st.session_state.analysis_complete = True
                st.session_.video_path = tmp_file.name
                        
                        # Generate the prompt and run analysis
                        initial_prompt = create_initial_analysis_prompt(funnel_stage, metrics_text, bonus_features)
                        analysis_state.messages.append({"role": "assistant", "content": initial_analysis})
                
                # Clean up the temp file
                os.remove(video_path)
                st.rerun() # Rerun to displayresult, video_file_name = analyze_video(st.session_state.video_path, initial_prompt)
                        
                        # Store results in session state
                        st.session_state.initial_analysis = analysis the chat interface immediately

            except Exception as e:
                st.error(f"An error occurred: {e}")

_result
                        st.session_state.analysis_complete = True
                        st.session_state.chat    # Display chat history if analysis is done
    if st.session_state.analysis_complete:
        _history = [] # Reset chat history for new analysis
                        st.session_state.video_file_name = videofor message in st.session_state.messages:
            with st.chat_message(name=message["role_file_name # Store the AI's reference to the file

                        st.success("Analysis complete! View"]):
                st.markdown(message["content"])

    # [NEW FEATURE] Chat input box
    if prompt the report below and head to the 'Chat & Explore' tab.")

                    except Exception as e:
                        st.error := st.chat_input("Ask a follow-up question...", disabled=not st.session_state.analysis_complete):(f"An error occurred: {e}")
        
        if st.session_state.analysis_complete:
            
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.st.markdown(st.session_state.initial_analysis)


# --- TAB 2: Chat & Explore ---
withchat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant tab2:
    if not st.session_state.analysis_complete:
        st.info("Please"):
            with st.spinner("Thinking..."):
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
        
        st.session_state.messages upload a video and run the initial analysis on the first tab to activate the chatbot.")
    else:
        st.header.append({"role": "assistant", "content": response.text})

    elif not st.session_state.analysis("💬 Ask Follow-Up Questions")
        st.markdown("The AI remembers your initial analysis. Ask anything about the video_complete:
        st.info("Your analysis and chat will appear here after you upload a video and click ', its performance, or the suggestions.")
        
        with st.expander("Show Initial Analysis"):
             st.markdownAnalyze'.")


# Cleanup function for the uploaded video file on Gemini servers when the session ends
# Note: This is a(st.session_state.initial_analysis)

        # Display chat history
        for author, text in st.session best-effort cleanup. Streamlit doesn't have a guaranteed "on_session_end" hook.
if_state.chat_history:
            with st.chat_message(author):
                st.markdown(text st.session_state.video_file_name:
    # This part is a bit tricky in Streamlit. For)

        # Chat input box
        if prompt := st.chat_input("e.g., Can you elaborate on the simplicity, we'll rely on Gemini's 48-hour auto-delete.
    # For a A/B test idea?"):
            st.session_state.chat_history.append(("user", prompt)) production app, a more robust cleanup mechanism (e.g., a button) would be needed.
    pass

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat```

### What's New and How to Use It:

1.  **Cleaner Interface:**
    *   The_message("assistant"):
                with st.spinner("Thinking..."):
                    # Get the uploaded video file object from the AI service
                    video_file = genai.get_file(name=st.session_state.video KPI inputs are now neatly tucked into an expander called "📈 Enter Performance KPIs".
    *   When you upload a video_file_name)
                    
                    # Create a new prompt that includes context
                    chatbot_prompt = f""", you'll see it right there on the screen.

2.  **Deeper Analysis:**
    *   
                    You are a helpful assistant continuing a conversation about a video analysis.
                    **Original Analysis Summary:**\n{stThere's a new expander: "🧠 Add Deeper Analysis".
    *   Before you click "Analyze Video.session_state.initial_analysis}\n\n
                    **Conversation History:**\n{st.session_state.", you can check the boxes for "Suggest Alternative Hooks" and "Define Target Audience Persona". The AI's initial reportchat_history}\n\n
                    **User's New Question:** {prompt}\n\n
                    Please provide will include these sections.

3.  **The Chatbot:**
    *   After the initial analysis is generated a concise and helpful response based on the original analysis, the video file itself, and the conversation so far.
                    , the right-hand column will populate with the report.
    *   At the bottom, a chat box will appear,"""
                    
                    model = genai.GenerativeModel(model_name="gemini-1.5 saying "Ask a follow-up question...".
    *   You can now have a full conversation with the AI-flash")
                    response = model.generate_content([chatbot_prompt, video_file])
                    response_text = response.text
                    st.markdown(response_text)
            
            st.session_state. about the video. It will remember everything from the initial analysis.

No changes are needed for your `secrets.toml`chat_history.append(("assistant", response_text))

# --- Final Cleanup ---
# Note: We don't file. Just update your `app.py`, and your app will be transformed into a much more powerful and interactive tool.
