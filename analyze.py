import os
import google.generativeai as genai
import time

# --- Configuration ---
# IMPORTANT: Store your API key securely.
# For this script, we'll get it from an environment variable.
# In your terminal, run: export GOOGLE_API_KEY="YOUR_API_KEY_HERE"
# On Windows, use: set GOOGLE_API_KEY="YOUR_API_KEY_HERE"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# --- Helper Function to Create the Prompt ---
def create_analysis_prompt(metrics):
    """Creates the detailed prompt for the Gemini model."""
    return f"""
    You are an expert viral video analyst for Instagram. Your task is to analyze the provided Instagram Reel and its performance metrics to identify the key elements contributing to its success.

    **Video Performance Metrics:**
    {metrics}

    **Analysis Task:**
    Based on the video content and the provided metrics, provide a detailed breakdown in the following structure. Be critical, specific, and provide actionable insights.

    **Hook Analysis (First 3 Seconds):**
    - **Description:** Describe the visual and auditory elements of the first three seconds.
    - **Hook Type:** Does it use a "pain point," a surprising statement, a question, or a visually captivating shot?
    - **Effectiveness (1-10):** Rate the hook's effectiveness and briefly explain your reasoning.

    **Video Structure and Pacing:**
    - **Sections:** Identify the main sections of the video (e.g., introduction, main content, climax, call to action).
    - **Pacing:** Describe the pacing. Is it fast-paced with quick cuts, or slower and more cinematic?
    - **Transitions/Effects:** Note any significant transitions or visual effects used.

    **Content Analysis:**
    - **Core Message/Value:** What is the core message or value proposition? (e.g., educational, entertaining, inspirational, relatable).
    - **Trends/Audio:** Identify any trends, challenges, or popular audio used.
    - **Storytelling:** Does the video tell a story or present information in a compelling way? Explain how.

    **Engagement Triggers:**
    - **Call to Action (CTA):** Is there a clear CTA? If so, what is it? (e.g., "follow for more," "comment below," "link in bio").
    - **Audience Prompts:** Are there any direct questions or prompts to the audience?
    - **Emotional Response:** What strong emotions does the content likely evoke? (e.g., humor, awe, sadness, motivation).

    **Overall "Virality" Score:**
    - **Score (1-10):** Based on your complete analysis, provide an overall score for how likely this reel is to go viral.
    - **Top 3 Reasons:** Summarize the top 3 most impactful reasons for this score.
    """

# --- Main Analysis Function ---
def analyze_reel(video_path, metrics):
    """Uploads the video and gets the analysis from Gemini."""
    print("Uploading file...")
    # The Gemini API requires you to upload the file first.
    video_file = genai.upload_file(path=video_path)
    print(f"Completed upload: {video_file.name}")

    # Wait for the file to be processed
    while video_file.state.name == "PROCESSING":
        print("Waiting for video processing...")
        time.sleep(10)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError("Video processing failed.")

    print("Making API call to Gemini...")
    # Select the vision model
    model = genai.GenerativeModel(model_name="gemini-1.5-flash") # Using 1.5-flash for speed and cost-effectiveness

    # Create the prompt
    prompt = create_analysis_prompt(metrics)

    # Send the prompt and video to the model
    response = model.generate_content([prompt, video_file])

    # Clean up the uploaded file
    genai.delete_file(video_file.name)
    print("Cleaned up uploaded file.")

    return response.text

# --- How to run the script ---
if __name__ == "__main__":
    # 1. Place your video file in the same folder and update the name here.
    video_file_name = "your_reel.mp4" 
    
    # 2. Update the metrics for your video.
    video_metrics = """
    - Views: 1 million in 24 hours
    - Likes: 100,000
    - Shares: 5,000
    - Comments: 2,500
    """

    # 3. Check if the file exists before running
    if not os.path.exists(video_file_name):
        print(f"Error: Video file '{video_file_name}' not found.")
        print("Please place the video in the same folder as the script and update the 'video_file_name' variable.")
    else:
        try:
            analysis_result = analyze_reel(video_file_name, video_metrics)
            print("\n--- REEL ANALYSIS RESULT ---")
            print(analysis_result)
        except Exception as e:
            print(f"An error occurred: {e}")
