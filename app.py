# ===================================================================================
# CORRECTED and more ROBUST render_campaign_tab function
# ===================================================================================
def render_campaign_tab(funnel_stage):
    """Main function to render a tab's UI and logic."""

    # Initialize session state for the tab
    session_state_key = f"analysis_state_{funnel_stage}"
    if session_state_key not in st.session_state:
        st.session_state[session_state_key] = {
            "status": "not_started",
            "files": [],
            "kpis": {},
            "manual_kpis": {} # Store manually added KPIs here
        }

    # --- UI for Step 1: Uploading Files & KPIs ---
    if st.session_state[session_state_key]["status"] == "not_started":
        with st.container(border=True):
            st.subheader("Step 1: Upload Assets", anchor=False, help="Upload your videos and an optional CSV with performance metrics.")
            col1, col2 = st.columns(2)
            with col1:
                uploaded_files = st.file_uploader("Upload campaign videos", type=["mp4", "mov", "avi", "m4v"], accept_multiple_files=True, key=f"uploader_{funnel_stage.lower()}")
            with col2:
                kpi_csv_file = st.file_uploader("Upload a CSV with your metrics (Optional)", type="csv", key=f"csv_uploader_{funnel_stage.lower()}", help="Must have a 'filename' column. The filename can be with or without the extension (e.g., .mp4).")

        if uploaded_files:
            parsed_kpis_from_csv = {}
            if kpi_csv_file:
                try:
                    df = pd.read_csv(kpi_csv_file).astype(str)
                    if 'filename' not in df.columns:
                        st.error("CSV Error: Your file is missing the required 'filename' column.", icon="❌")
                    else:
                        parsed_kpis_from_csv = df.set_index('filename').to_dict('index')
                        st.success("✅ Metrics CSV loaded successfully!", icon="🎉")
                except Exception as e:
                    st.error(f"Error reading CSV file: {e}", icon="❌")

            with st.container(border=True):
                st.subheader("Step 2: Enter or Verify Metrics", anchor=False)
                kpi_input_data = {}

                for file in uploaded_files:
                    with st.expander(f"Metrics for: **{file.name}**"):
                        # <-- THE FIX IS HERE: Check for filename with and without extension
                        basename, _ = os.path.splitext(file.name)
                        file_kpis_from_csv = parsed_kpis_from_csv.get(file.name) or parsed_kpis_from_csv.get(basename)

                        if file_kpis_from_csv:
                            st.markdown("###### Metrics from CSV (editable)")
                            temp_kpis = {}
                            cols = st.columns(3)
                            for i, (k, v) in enumerate(file_kpis_from_csv.items()):
                                with cols[i % 3]:
                                    temp_kpis[k] = st.text_input(f"**{k}**", value=v, key=f"csv_{k}_{file.name}_{funnel_stage}")
                            kpi_input_data[file.name] = temp_kpis
                        else: # --- Manual KPI Entry (unchanged) ---
                            st.info("No metrics found for this file in CSV. Add them manually below.", icon="✍️")
                            if file.name not in st.session_state[session_state_key]["manual_kpis"]:
                                st.session_state[session_state_key]["manual_kpis"][file.name] = []
                            
                            temp_manual_kpis = {}
                            for i, item in enumerate(st.session_state[session_state_key]["manual_kpis"][file.name]):
                                c1, c2 = st.columns([2, 2])
                                with c1:
                                    name = st.text_input("Metric Name", value=item.get("name", ""), key=f"manual_name_{i}_{file.name}_{funnel_stage}")
                                with c2:
                                    value = st.text_input("Metric Value", value=item.get("value", ""), key=f"manual_value_{i}_{file.name}_{funnel_stage}")
                                if name and value: temp_manual_kpis[name] = value
                            
                            kpi_input_data[file.name] = temp_manual_kpis
                            if st.button("Add Metric", key=f"add_kpi_{file.name}_{funnel_stage}"):
                                st.session_state[session_state_key]["manual_kpis"][file.name].append({"name": "", "value": ""})
                                st.rerun()

            # --- Start Analysis Button (logic is unchanged) ---
            if st.button(f"🚀 Analyze {funnel_stage} Campaign", type="primary", use_container_width=True, key=f"start_button_{funnel_stage.lower()}"):
                st.session_state[session_state_key]["kpis"] = kpi_input_data
                files_to_process = [f for f in uploaded_files if any(kpi_input_data.get(f.name, {}).values())]
                if not files_to_process:
                    st.error("No videos with KPIs found. Please enter metrics to begin analysis.")
                else:
                    with st.spinner("Uploading and starting video processing... The app will NOT freeze."):
                        for file in files_to_process:
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
                                    tmp.write(file.getvalue())
                                video_file_for_api = genai.upload_file(path=tmp.name)
                                st.session_state[session_state_key]["files"].append({
                                    "original_filename": file.name, "api_file_name": video_file_for_api.name, "status": "processing"
                                })
                                os.remove(tmp.name)
                            except Exception as e:
                                st.error(f"Failed to upload '{file.name}': {e}")
                    st.session_state[session_state_key]["status"] = "processing"
                    st.rerun()
                    
    # The rest of the function for "processing" and "complete" states remains the same...
    elif st.session_state[session_state_key]["status"] == "processing":
        st.info("🔄 Videos are being processed by Google...", icon="⏳")
        st.write("Click the button below to check the status. Once all videos are ready, the report will be generated.")
        if st.button("Check Status & Generate Report", use_container_width=True, key=f"check_button_{funnel_stage.lower()}"):
            all_files_ready = True
            with st.spinner("Checking file statuses..."):
                for file_info in st.session_state[session_state_key]["files"]:
                    if file_info["status"] == "processing":
                        api_file = genai.get_file(name=file_info["api_file_name"])
                        if api_file.state.name == "ACTIVE": file_info["status"] = "active"; st.success(f"✅ '{file_info['original_filename']}' is ready.")
                        elif api_file.state.name == "FAILED": file_info["status"] = "failed"; st.error(f"❌ Processing failed for '{file_info['original_filename']}'.")
                        else: all_files_ready = False; st.info(f"⏳ '{file_info['original_filename']}' is still processing...")
            if all_files_ready:
                with st.spinner("All files ready! Generating individual and final reports..."):
                    individual_summaries, active_files = [], [f for f in st.session_state[session_state_key]["files"] if f["status"] == 'active']
                    for file_info in active_files:
                        original_filename = file_info["original_filename"]
                        kpis = st.session_state[session_state_key]["kpis"].get(original_filename, {})
                        kpi_text = ", ".join([f"{k}: {v}" for k, v in kpis.items() if v])
                        prompt = create_individual_analysis_prompt(original_filename, kpi_text)
                        api_file = genai.get_file(name=file_info["api_file_name"])
                        response = genai.GenerativeModel(model_name="gemini-1.5-flash-latest").generate_content([prompt, api_file])
                        individual_summaries.append(f"**Video: {original_filename}**\n{response.text}\n\n")
                    if individual_summaries:
                        synthesis_prompt = create_campaign_synthesis_prompt("".join(individual_summaries), funnel_stage)
                        final_response = genai.GenerativeModel(model_name="gemini-1.5-pro-latest").generate_content(synthesis_prompt)
                        st.session_state[session_state_key]["final_report"] = final_response.text
                        st.session_state[session_state_key]["status"] = "complete"
                        for file_info in st.session_state[session_state_key]["files"]:
                            try: genai.delete_file(name=file_info["api_file_name"])
                            except Exception: pass
                        st.rerun()

    elif st.session_state[session_state_key]["status"] == "complete":
        parse_report_and_display(st.session_state[session_state_key].get("final_report", "Report not found."), st.session_state[session_state_key].get("kpis", {}))
        if st.button(f"↩️ Start New {funnel_stage} Analysis", use_container_width=True, key=f"reset_button_{funnel_stage.lower()}"):
            st.session_state[session_state_key] = {"status": "not_started", "files": [], "kpis": {}, "manual_kpis": {}}
            st.rerun()
            
