# ===================================================================================
# FINAL v8.1 app.py - Tab-Based Multi-Video Campaign Strategist
# CORRECTED AND MORE ROBUST RENDER FUNCTION
# ===================================================================================

# --- Add this constant near the top of your file ---
POLLING_INTERVAL_SECONDS = 10 # How often to check the file status
PROCESSING_TIMEOUT_SECONDS = 300 # Max time to wait for a single file (5 minutes)


# --- Replace the entire old render_campaign_tab function with this one ---
def render_campaign_tab(funnel_stage, kpi_definitions):
    """
    Creates the entire UI and logic for a single tab.
    - funnel_stage: The name of the stage (e.g., "Awareness")
    - kpi_definitions: The dictionary of KPIs for that stage.
    """
    st.header(f"Analyze Your {funnel_stage} Campaign")

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
                kpi_input_data[file.name] = {
                    kpi: st.text_input(kpi, placeholder=placeholder, key=f"{kpi}_{file.name}_{funnel_stage}")
                    for kpi, placeholder in kpi_definitions.items()
                }

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

                for i, video_data in enumerate(campaign_videos):
                    file = video_data["file_object"]
                    kpi_text = ", ".join([f"{k}: {v}" for k, v in video_data["kpis"].items()])
                    progress_text = f"Analyzing video {i+1}/{total_videos}: {file.name}"
                    progress_bar.progress((i / total_videos), text=progress_text)

                    video_path = None
                    video_file_for_api = None
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp_file:
                            tmp_file.write(file.getvalue())
                            video_path = tmp_file.name

                        st.info(f"⬆️ Uploading '{file.name}' to Google...")
                        video_file_for_api = genai.upload_file(path=video_path)
                        st.info(f"⏳ Processing '{file.name}'... This may take a few minutes.")

                        # *** ROBUST POLLING WITH TIMEOUT ***
                        start_time = time.time()
                        while True:
                            # Check for timeout
                            if time.time() - start_time > PROCESSING_TIMEOUT_SECONDS:
                                raise TimeoutError(f"File processing for '{file.name}' timed out after {PROCESSING_TIMEOUT_SECONDS} seconds.")

                            # Get the latest file status
                            video_file_for_api = genai.get_file(name=video_file_for_api.name)
                            
                            # If it's done processing, break the loop
                            if video_file_for_api.state.name != "PROCESSING":
                                break
                            
                            # Otherwise, wait before checking again
                            time.sleep(POLLING_INTERVAL_SECONDS)

                        if video_file_for_api.state.name != "ACTIVE":
                            st.error(f"Processing failed for '{file.name}'. Final state: {video_file_for_api.state.name}")
                            individual_summaries.append(f"**Video: {file.name}**\nAnalysis failed due to file processing error.\n\n")
                            continue

                        st.success(f"✅ '{file.name}' is ready! Generating insights...")
                        model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
                        prompt = create_individual_analysis_prompt(file.name, kpi_text)
                        response = model.generate_content([prompt, video_file_for_api])

                        summary = f"**Video: {file.name}**\n{response.text}\n\n"
                        individual_summaries.append(summary)

                    except Exception as e:
                        st.error(f"An error occurred while analyzing '{file.name}': {e}")
                        individual_summaries.append(f"**Video: {file.name}**\nAnalysis failed.\n\n")

                    finally:
                        # This cleanup runs no matter what happens in the try block
                        if video_path and os.path.exists(video_path):
                            os.remove(video_path)
                        if video_file_for_api:
                            # We check if the object exists before trying to delete
                            try:
                                genai.delete_file(video_file_for_api.name)
                            except Exception as e:
                                st.warning(f"Could not delete file '{video_file_for_api.name}' from Google Cloud. You may need to delete it manually. Error: {e}")


                # Step 2: Macro-Synthesis
                if individual_summaries:
                    progress_bar.progress(0.9, text="Synthesizing campaign-level insights...")
                    all_summaries_text = "".join(individual_summaries)
                    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
                    synthesis_prompt = create_campaign_synthesis_prompt(all_summaries_text)
                    final_response = model.generate_content(synthesis_prompt)

                    progress_bar.progress(1.0, text="Campaign analysis complete!")
                    st.subheader(f"🏆 Your {funnel_stage} Campaign Strategy Report")
                    st.markdown(final_response.text)
