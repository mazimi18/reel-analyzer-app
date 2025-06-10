# ===================================================================================
# CORRECTED: render_campaign_tab function
# ===================================================================================
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

                    video_path = None
                    video_file_for_api = None
                    try:
                        # 1. Save video to a temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp_file:
                            tmp_file.write(file.getvalue())
                            video_path = tmp_file.name

                        # 2. Upload the file to the API
                        st.info(f"⬆️ Uploading '{file.name}' to Google...")
                        video_file_for_api = genai.upload_file(path=video_path)
                        st.info(f"⏳ Processing '{file.name}'... This may take a moment.")

                        # 3. *** NEW: Poll for ACTIVE state ***
                        while video_file_for_api.state.name == "PROCESSING":
                            time.sleep(5)  # Wait for 5 seconds before checking again
                            video_file_for_api = genai.get_file(name=video_file_for_api.name)

                        # Check if processing failed
                        if video_file_for_api.state.name != "ACTIVE":
                            st.error(f"Processing failed for '{file.name}'. State: {video_file_for_api.state.name}")
                            individual_summaries.append(f"**Video: {file.name}**\nAnalysis failed due to file processing error.\n\n")
                            continue # Skip to the next video

                        # 4. File is ACTIVE, now we can generate content
                        st.info(f"✅ '{file.name}' is ready! Generating insights...")
                        model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
                        prompt = create_individual_analysis_prompt(file.name, kpi_text)
                        response = model.generate_content([prompt, video_file_for_api])

                        summary = f"**Video: {file.name}**\n{response.text}\n\n"
                        individual_summaries.append(summary)

                    except Exception as e:
                        st.error(f"An error occurred while analyzing '{file.name}': {e}")
                        individual_summaries.append(f"**Video: {file.name}**\nAnalysis failed.\n\n")

                    finally:
                        # 5. Clean up files regardless of success or failure
                        if video_path and os.path.exists(video_path):
                            os.remove(video_path)
                        if video_file_for_api:
                            genai.delete_file(video_file_for_api.name)

                # Step 2: Macro-Synthesis (Unchanged)
                if individual_summaries:
                    progress_bar.progress(0.9, text="Synthesizing campaign-level insights...")
                    all_summaries_text = "".join(individual_summaries)
                    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
                    synthesis_prompt = create_campaign_synthesis_prompt(all_summaries_text)
                    final_response = model.generate_content(synthesis_prompt)

                    progress_bar.progress(1.0, text="Campaign analysis complete!")
                    st.subheader(f"🏆 Your {funnel_stage} Campaign Strategy Report")
                    st.markdown(final_response.text)
