# ==============================================================================
# FINAL app.py CODE - Copy and paste this entire file
# ==============================================================================
import os
import re
import shutil
import google.generativeai as genai
import streamlit as st
import instaloader
import time

# --- Configuration ---
# Load all secrets from Streamlit's secrets management
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    INSTA_USER = st.secrets["INSTAGRAM_USER"]
    # We get password and session content but prioritize session content
    INSTA_PASSWORD = st.secrets.get("INSTAGRAM_PASSWORD")
    INSTA_SESSION_CONTENT = st.secrets.get("INSTA_SESSION_CONTENT")
except (TypeError, KeyError) as e:
    st.error(f"🚨 A required secret is missing! Please check your .streamlit/secrets.toml file. Error: {e}")
    st.stop()


# --- Instagram Downloader Function (Uses Session File) ---
@st.cache_data(show_spinner="Downloading Reel...")
def download_from_instagram(url):
    """
    Downloads a video from an Instagram Reel URL using a session file for stable login.
    """
    temp_dir = "temp_downloads"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    match = re.search(r"/(reels?|p)/([^/]+)", url)
    if not match:
        st.error("Invalid Instagram URL. Please use a valid Reel link.")
        return None
    shortcode = match.group(2)

    try:
        L = instaloader.Instaloader(download_videos=True, download_comments=False, save_metadata=False, download_pictures=False)
        # Suppress verbose terminal output on the server
        L.stream_log = lambda *args: None

        # --- THIS IS THE CRITICAL LOGIN LOGIC ---
        if INSTA_SESSION_CONTENT:
            # If session content exists in secrets, create a temporary file with it
            session_filepath = f"./{INSTA_USER}"
            with open(session_filepath, 'w') as session_file:
                session_file.write(INSTA_SESSION_CONTENT)
            
            # Load the session from the file we just created
            L.load_session_from_file(INSTA_USER)
            print("Login successful using secure session file.")
        elif INSTA_PASSWORD:
            # Fallback to password login only if session secret is not found
            print("Session secret not found, falling back to password login.")
            L.login(INSTA_USER, INSTA_PASSWORD)
        else:
            st.error("No valid Instagram login method found in secrets (session or password).")
            return None
        # --- END OF CRITICAL LOGIN LOGIC ---

        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=temp_dir)

        # Find the downloaded video file
        for filename in os.listdir(temp_dir):
            if filename.endswith(".mp4"):
                return os.path.join(temp_dir, filename)
        st.error("Could not find the downloaded video file.")
        return None

    except Exception as e:
        st.error(f"An error occurred while downloading the Reel: {e}")
        return None

# --- AI Prompt Generation and Analysis Functions (Unchanged) ---
METRIC_DEFINITIONS = {
    "Awareness": {"Impressions": "e.g., 5,000,000", "Cost Per Thousand (CPM)": "e.g., $2.50"},
    "Traffic": {"Click-Through Rate (CTR)": "e.g., 2.5%", "Cost Per Click (CPC)": "e.g., $0.50", "Landing Page Views": "e.g., 25,000", "Cost Per Landing Page View": "e.g., $0.80"},
    "Conversion": {"Purchases / Leads": "e.g., 500", "Purchase Volume ($)": "e.g., $25,000", "Return On Ad Spend (ROAS)": "e.g., 4.5x", "Cost Per Acquisition (CPA)": "e.g., $50.00"}
}

def create_analysis_prompt(funnel_stage, metrics):
    # This function is unchanged. You can expand or collapse it in your editor.
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

def analyze_reel(video_path, funnel_stage, metrics, progress_bar):
    # This function is unchanged.
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

# --- Streamlit App UI (Unchanged) ---
st.set_page_config(page_title="Reel KPI Analyzer", layout="wide")
st.title("🚀 Instagram Reel KPI Analyzer")
st.markdown("Analyze how a Reel's creative drives specific marketing funnel KPIs.")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Enter Instagram Reel Link")
    reel_url = st.text_input("Paste the URL of the Instagram Reel here:")

    st.header("2. Provide Performance Metrics")
    funnel_stage = st.selectbox("Select the primary goal (funnel stage) of this Reel:", options=list(METRIC_DEFINITIONS.keys()))
    st.markdown("---")
    kpi_inputs = {}
    if funnel_stage:
        kpis_for_stage = METRIC_DEFINITIONS[funnel_stage]
        st.subheader(f"{funnel_stage} KPIs:")
        for kpi, placeholder in kpis_for_stage.items():
            kpi_inputs[kpi] = st.text_input(label=kpi, placeholder=placeholder)
    
    analyze_button = st.button("Analyze Reel Performance", type="primary", use_container_width=True)

with col2:
    st.header("3. AI-Generated Performance Analysis")
    if analyze_button and reel_url:
        video_path = None
        try:
            video_path = download_from_instagram(reel_url)
            if video_path:
                metrics_text = "\n".join([f"- {kpi}: {val}" for kpi, val in kpi_inputs.items() if val])
                if not metrics_text:
                    st.warning("Please enter at least one KPI value.")
                else:
                    progress_bar = st.progress(0, text="Starting analysis...")
                    analysis_result = analyze_reel(video_path, funnel_stage, metrics_text, progress_bar)
                    st.markdown(analysis_result)
        except Exception as e:
            st.error(f"An error occurred during the main process: {e}")
        finally:
            if video_path and os.path.exists("temp_downloads"):
                shutil.rmtree("temp_downloads")
    elif analyze_button and not reel_url:
        st.warning("Please enter an Instagram Reel URL first.")
    else:
        st.info("Your performance analysis will appear here.")