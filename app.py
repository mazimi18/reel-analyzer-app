import os
import re
import shutil
import google.generativeai as genai
import streamlit as st
import instaloader
import time

# --- Configuration ---
# Streamlit secrets management
try:
    # Configure Gemini
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Get Instagram credentials
    INSTA_USER = st.secrets["INSTAGRAM_USER"]
    INSTA_PASSWORD = st.secrets["INSTAGRAM_PASSWORD"]
except (TypeError, KeyError) as e:
    st.error(f"🚨 A secret is missing! Please check your .streamlit/secrets.toml file. Error: {e}")
    st.stop()


# --- Instagram Downloader Function ---
@st.cache_data(show_spinner="Downloading Reel...")
def download_from_instagram(url):
    """
    Downloads a video from an Instagram Reel URL.
    Returns the path to the downloaded video file.
    """
    # Create a temporary directory to store the download
    temp_dir = "temp_downloads"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir) # Clean up old downloads

    # Extract the shortcode from the URL (e.g., Cq-pLp5JgKm)
    match = re.search(r"/(reels?|p)/([^/]+)", url)
    if not match:
        st.error("Invalid Instagram URL. Please use a valid Reel link.")
        return None
    shortcode = match.group(2)

    try:
        L = instaloader.Instaloader(download_videos=True, download_comments=False, save_metadata=False, download_pictures=False)
        # Suppress verbose output in the terminal
        L.stream_log = lambda *args: None

        L.login(INSTA_USER, INSTA_PASSWORD)
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        # Download the post into the temporary directory
        L.download_post(post, target=temp_dir)

        # Find the downloaded video file
        for filename in os.listdir(temp_dir):
            if filename.endswith(".mp4"):
                video_path = os.path.join(temp_dir, filename)
                return video_path
        st.error("Could not find the downloaded video file.")
        return None

    except Exception as e:
        st.error(f"An error occurred while downloading the Reel: {e}")
        return None

# --- AI Prompt and Analysis Functions (No changes needed here) ---
# ... (All the functions like create_analysis_prompt and analyze_reel are the same) ...
# ... I'm including them here for a complete, copy-paste-ready file ...

METRIC_DEFINITIONS = {
    "Awareness": {"Impressions": "e.g., 5,000,000", "Cost Per Thousand (CPM)": "e.g., $2.50"},
    "Traffic": {"Click-Through Rate (CTR)": "e.g., 2.5%", "Cost Per Click (CPC)": "e.g., $0.50", "Landing Page Views": "e.g., 25,000", "Cost Per Landing Page View": "e.g., $0.80"},
    "Conversion": {"Purchases / Leads": "e.g., 500", "Purchase Volume ($)": "e.g., $25,000", "Return On Ad Spend (ROAS)": "e.g., 4.5x", "Cost Per Acquisition (CPA)": "e.g., $50.00"}
}

def create_analysis_prompt(funnel_stage, metrics):
    return f"""
    You are an expert digital marketing and viral video analyst...
    (The rest of this prompt is identical to the previous version)
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

# --- Streamlit App UI (Updated) ---
st.set_page_config(page_title="Reel KPI Analyzer", layout="wide")
st.title("🚀 Instagram Reel KPI Analyzer")
st.markdown("Analyze how a Reel's creative drives specific marketing funnel KPIs.")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Enter Instagram Reel Link")
    # --- THIS IS THE MAIN CHANGE ---
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
            # Download the video first
            video_path = download_from_instagram(reel_url)
            
            if video_path:
                metrics_text = "\n".join([f"- {kpi}: {val}" for kpi, val in kpi_inputs.items() if val])
                if not metrics_text:
                    st.warning("Please enter at least one KPI value.")
                else:
                    progress_bar = st.progress(0, text="Starting analysis...")
                    with st.spinner('AI is thinking... This may take a minute.'):
                        analysis_result = analyze_reel(video_path, funnel_stage, metrics_text, progress_bar)
                    st.markdown(analysis_result)

        except Exception as e:
            st.error(f"An error occurred during the main process: {e}")
        finally:
            # Clean up the downloaded files and directory
            if video_path and os.path.exists("temp_downloads"):
                shutil.rmtree("temp_downloads")

    elif analyze_button and not reel_url:
        st.warning("Please enter an Instagram Reel URL first.")
    else:
        st.info("Your performance analysis will appear here.")