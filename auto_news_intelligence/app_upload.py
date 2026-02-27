"""Streamlit Admin UI for Auto News Intelligence Pipeline"""
import streamlit as st
import json
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import os

# Import our modules
import url_manager
import pipeline_runner

load_dotenv()

st.set_page_config(
    page_title="Auto News Pipeline Admin",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Auto News Intelligence — Pipeline Admin")
st.markdown("---")

# Sidebar: View current config
with st.sidebar:
    st.header("⚙️ Current Configuration")
    st.caption("Loaded from .env file")
    
    config_items = {
        "Similarity Threshold": os.getenv('SIMILARITY_THRESHOLD', '0.85'),
        "Auto Filter Threshold": os.getenv('AUTO_FILTER_THRESHOLD', '0.40'),
        "Min Category Confidence": os.getenv('MIN_CATEGORY_CONFIDENCE', '0.20'),
        "Input Folder": os.getenv('INPUT_FOLDER', 'input/articles/articles'),
    }
    
    for key, value in config_items.items():
        st.text(f"{key}: {value}")

# Section 1: URL Upload
st.header("📤 Section 1: URL Upload")

uploaded_file = st.file_uploader(
    "Upload a .txt file with URLs (one per line)",
    type=['txt'],
    help="Upload files like 26_02_links.txt with one URL per line. Master list is stored in url_batches/all_links.txt"
)

if uploaded_file is not None:
    # Parse URLs
    content = uploaded_file.read().decode('utf-8')
    new_urls = url_manager.parse_urls_from_text(content)
    
    if new_urls:
        # Check against existing
        existing_urls = url_manager.load_master_urls()
        
        # Build preview table
        preview_data = []
        new_count = 0
        existing_count = 0
        
        for url in new_urls:
            if url in existing_urls:
                status = "Already exists"
                existing_count += 1
            else:
                status = "New"
                new_count += 1
            preview_data.append({"URL": url[:80] + "..." if len(url) > 80 else url, "Status": status})
        
        st.info(f"📊 Found {len(new_urls)} URLs: **{new_count} new**, {existing_count} already in master")
        
        # Show preview table
        st.dataframe(preview_data, width='stretch', height=300)
        
        # Confirm button
        if new_count > 0:
            if st.button("✅ Confirm & Add to master", type="primary"):
                added, skipped = url_manager.append_new_urls(new_urls)
                st.success(f"✓ Added {added} new URLs to all_links.txt (skipped {skipped} duplicates)")
                st.balloons()
        else:
            st.warning("All URLs already exist in master file")
    else:
        st.error("No valid URLs found in uploaded file")

st.markdown("---")

# Section 2: Run Pipeline
st.header("▶️ Section 2: Run Pipeline")

# Show current stats
col1, col2, col3 = st.columns(3)

master_file = Path('url_batches/all_links.txt')
if master_file.exists():
    with open(master_file, 'r') as f:
        total_urls = len([line for line in f if line.strip().startswith('http')])
    col1.metric("Total URLs in master", total_urls)
else:
    col1.metric("Total URLs in master", 0)

html_dir = Path('input/articles/articles')
if html_dir.exists():
    html_count = len(list(html_dir.glob('*.html')))
    col2.metric("HTML files downloaded", html_count)
else:
    col2.metric("HTML files downloaded", 0)

results_file = Path('output/results.json')
if results_file.exists():
    try:
        with open(results_file, 'r') as f:
            data = json.load(f)
            last_run = data.get('run_at', 'Unknown')
            if last_run != 'Unknown':
                last_run = datetime.fromisoformat(last_run).strftime('%Y-%m-%d %H:%M')
        col3.metric("Last run", last_run)
    except:
        col3.metric("Last run", "Unknown")
else:
    col3.metric("Last run", "Never")

st.markdown("")

# Run button
if st.button("▶ Run Full Pipeline", type="primary", use_container_width=False):
    st.info("🚀 Starting pipeline... This may take several minutes.")
    
    # Progress bar
    progress_bar = st.progress(0)
    progress_text = st.empty()
    
    # Log stream
    log_container = st.empty()
    log_lines = []
    
    # Run pipeline
    stage_progress = {
        '[DOWNLOAD]': 0.2,
        '[LOAD]': 0.3,
        '[FILTER]': 0.4,
        '[EMBED]': 0.5,
        '[CLASSIFY]': 0.6,
        '[DEDUP]': 0.8,
        '[DONE]': 1.0
    }
    
    current_progress = 0.0
    
    for log_line in pipeline_runner.stream_pipeline():
        log_lines.append(log_line)
        
        # Update progress based on stage
        for stage, prog in stage_progress.items():
            if stage in log_line and prog > current_progress:
                current_progress = prog
                progress_bar.progress(current_progress)
                progress_text.text(f"Stage: {stage}")
                break
        
        # Show last 30 lines
        display_lines = log_lines[-30:]
        log_container.code(''.join(display_lines), language='log')
    
    # Get final stats
    stats = pipeline_runner.stream_pipeline.__code__.co_consts
    
    progress_bar.progress(1.0)
    progress_text.text("✓ Complete")
    
    st.success("✅ Pipeline completed successfully!")

    # Auto-publish latest results to frontend dashboard if folder exists.
    streamlit_app_dir = Path('../streamlit-app')
    if streamlit_app_dir.exists():
        try:
            dest = streamlit_app_dir / 'results.json'
            shutil.copy(results_file, dest)
            st.success(f"📋 Auto-published results to {dest}")
        except Exception as e:
            st.warning(f"Pipeline finished but auto-publish failed: {e}")
    
    # Store completion flag
    st.session_state['pipeline_complete'] = True

st.markdown("---")

# Section 3: Output & Export
st.header("📊 Section 3: Output & Export")

if results_file.exists():
    try:
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        # Summary metrics
        st.subheader("Summary Metrics")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Articles", data['stats']['total_input'])
        col2.metric("Auto-relevant", data['stats']['total_automobile'])
        col3.metric("Categories", len(data['categories']))
        
        total_stories = sum(cat['unique_stories'] for cat in data['categories'].values())
        col4.metric("Unique Stories", total_stories)
        col5.metric("Sources", data['stats']['unique_sources'])
        
        # Category breakdown
        st.subheader("Category Breakdown")
        
        cat_table = []
        for cat_name, cat_data in data['categories'].items():
            cat_table.append({
                "Category": cat_name,
                "Articles": cat_data['total_articles'],
                "Unique Stories": cat_data['unique_stories']
            })
        
        st.dataframe(cat_table, width='stretch')
        
        # Preview results.json
        with st.expander("🔍 Preview results.json (first 50 lines)"):
            json_str = json.dumps(data, indent=2)
            lines = json_str.split('\n')[:50]
            st.code('\n'.join(lines), language='json')
        
        st.markdown("")
        
        # Download button
        json_bytes = json.dumps(data, indent=2).encode('utf-8')
        st.download_button(
            label="⬇ Download results.json",
            data=json_bytes,
            file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        st.markdown("")
        
        # Copy to streamlit-app
        streamlit_app_dir = Path('../streamlit-app')
        if streamlit_app_dir.exists():
            if st.button("📋 Copy to streamlit-app/", type="secondary"):
                try:
                    dest = streamlit_app_dir / 'results.json'
                    shutil.copy(results_file, dest)
                    st.success(f"✓ Copied to {dest}")
                    
                    # Show git instructions
                    st.info("📝 Next steps to deploy:")
                    git_commands = f"""cd ../streamlit-app
git add results.json
git commit -m "Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
git push origin main"""
                    st.code(git_commands, language='bash')
                    
                except Exception as e:
                    st.error(f"✗ Copy failed: {e}")
        else:
            st.warning("⚠ streamlit-app/ directory not found at ../streamlit-app")
    
    except Exception as e:
        st.error(f"Error loading results.json: {e}")
else:
    st.info("No results.json found. Run the pipeline first.")

st.markdown("---")
st.caption("Auto News Intelligence Pipeline Admin v1.0")
