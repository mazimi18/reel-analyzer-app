# ==============================================================================
# FINAL v3 app.py CODE - This version manually creates the required directory
# ==============================================================================
import os
import re
import shutil
import google.generativeai as genai
import streamlit as st
import instaloader
import time

# --- Configuration (Unchanged) ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    INSTA_USER = st.secrets["INSTAGRAM_USER"]
    INSTA_PASSWORD = st.secrets.get("INSTAGRAM_PASSWORD")
    INSTA_SESSION_CONTENT = st.secrets.get("INSTA_SESSION_CONTENT")
except (TypeError, KeyError) as e:
    st.error(f"🚨 A required secret is missing! Please check your secrets. Error: {e}")
    st.stop()


# --- Instagram Downloader Function (DEFINITIVE FIX) ---
@st.cache_data(show_spinner="Downloading Reel...")
def download_from_instagram(url):
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
        L.stream_log = lambda *args: None

        # --- THIS IS THE CRITICAL LOGIN LOGIC WITH THE DEFINITIVE FIX ---
        if INSTA_SESSION_CONTENT:
            # Define the exact directory path instaloader is looking for, based on the error.
            session_dir = "/tmp/.instaloader-appuser/"
            
            # Define the full path to the session file inside that directory.
            session_filepath = os.path.join(session_dir, f"session-{INSTA_USER}")
            
            # THE FIX: Manually create the directory structure. It's okay if it already exists.
            os.makedirs(session_dir, exist_ok=True)
            
            # Write the session content from secrets to the file at the correct location.
            with open(session_filepath, 'w') as session_file:
                session_file.write(INSTA_SESSION_CONTENT)
            
            # Now, when we load the session, instaloader will find the file in its default path.
            L.load_session_from_file(INSTA_USER)
            print("Login successful using session file in manually-created default path.")
        elif INSTA_PASSWORD:
            print("Session secret not found, falling back to password login.")
            L.login(INSTA_USER, INSTA_PASSWORD)
        else:
            st.error("No valid Instagram login method found in secrets (session or password).")
            return None
        # --- END OF DEFINITIVE FIX ---

        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=temp_dir)

        for filename in os.listdir(temp_dir):
            if filename.endswith(".mp4"):
                return os.path.join(temp_dir, filename)
        st.error("Could not find the downloaded video file.")
        return None

    except Exception as e:
        st.error(f"An error occurred while downloading the Reel: {e}")
        return None

# --- AI and UI Sections (All unchanged from before) ---
# ... (The rest of the file is identical) ...
METRIC_DEFINITIONS = {
    "Awareness": {"Impressions": "e.g., 5,000,000", "Cost Per Thousand (CPM)": "e.g., $2.50"},
    "Traffic": {"Click-Through Rate (CTR)": "e.g., 2.5%", "Cost Per Click (CPC)": "e.g., $0.50", "Landing Page Views": "e.g., 25,000", "Cost Per Landing Page View": "e.g., $0.80"},
    "Conversion": {"Purchases / Leads": "e.g., 500", "Purchase Volume ($)": "e.g., $25,000", "Return On Ad Spend (ROAS)": "e.g., 4.5x", "Cost Per Acquisition (CPA)": "e.g., $50.00"}
}

def create_analysis_prompt(funnel_stage, metrics):
    return f"""
    You are an expert digital marketing and viral video analyst...
    (The rest of this prompt is identical to previous versions)
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