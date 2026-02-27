# 🚀 Quick Setup Guide - Auto News Intelligence

## Prerequisites
- Python 3.8 or higher
- Git
- Internet connection (for first-time setup)

---

## 📥 Step 1: Clone the Repository

```bash
git clone https://github.com/dark-scientist/autonews.git
cd autonews
```

---

## 🔧 Step 2: Setup Virtual Environment & Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
cd auto_news_intelligence
pip install -r requirements.txt
```

**Note**: First installation will download ML models (~90MB). This is one-time only.

---

## ⚙️ Step 3: Configure API Key (Optional)

Only needed if you want AI summaries (currently disabled to save costs).

```bash
# Create .env file
nano .env
```

Add this line (replace with your OpenAI API key):
```
OPENAI_API_KEY=your-api-key-here
```

Save and exit (Ctrl+X, then Y, then Enter)

---

## 🎯 Step 4: Run the Admin UI

```bash
# Make sure you're in auto_news_intelligence directory
streamlit run app_upload.py
```

The UI will open in your browser at: http://localhost:8501

---

## 📋 How to Use the Admin UI

### Upload URLs:
1. Click "Browse files" in Section 1
2. Upload your .txt file with URLs (one URL per line)
3. Review the preview (shows which URLs are new)
4. Click "✅ Confirm & Add to master"

### Run Pipeline:
1. Go to Section 2
2. Click "▶ Run Full Pipeline"
3. Watch the live logs (takes 2-3 minutes for 1000 articles)
4. Wait for "✓ Complete" message

### Export Results:
1. Go to Section 3
2. Review the summary metrics
3. Click "⬇ Download results.json" to save locally
4. OR click "📋 Copy to streamlit-app/" to prepare for deployment

---

## 🌐 Step 5: Update the Live Dashboard

After the pipeline completes:

```bash
# Copy results to streamlit-app
cp output/results.json ../streamlit-app/results.json

# Go to streamlit-app directory
cd ../streamlit-app

# Add git remote (first time only)
git init
git remote add origin https://github.com/dark-scientist/auto-news-dashboard.git

# Push to GitHub
git add results.json
git commit -m "Update: $(date +%Y-%m-%d)"
git push origin main
```

**Wait 1-2 minutes** - Streamlit Cloud will auto-deploy the updates.

---

## 🔄 Daily Workflow (After Initial Setup)

```bash
# 1. Activate environment
cd autonews/auto_news_intelligence
source venv/bin/activate

# 2. Start admin UI
streamlit run app_upload.py

# 3. In the browser:
#    - Upload new URLs
#    - Run pipeline
#    - Download results.json

# 4. Update dashboard
cp output/results.json ../streamlit-app/results.json
cd ../streamlit-app
git add results.json
git commit -m "Update: $(date +%Y-%m-%d)"
git push origin main
```

---

## 🆘 Troubleshooting

### "Command not found: python3"
Try: `python` instead of `python3`

### "Command not found: streamlit"
Make sure virtual environment is activated:
```bash
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### "No space left on device"
Free up disk space (need ~2GB free)

### Pipeline takes too long
Normal for 1000+ articles. Takes 2-3 minutes.

### "Module not found" errors
Reinstall dependencies:
```bash
pip install -r requirements.txt
```

---

## 📊 What Gets Generated

After running the pipeline, you'll get:

- **results.json** (in `output/` folder)
  - Contains all processed articles
  - Includes categories, deduplication, and metadata
  - Ready to deploy to dashboard

---

## 🎓 Understanding the Output

The results.json contains:
- **Total articles**: All articles processed
- **Auto-relevant**: Articles about automobiles
- **Categories**: 8 fixed categories (Industry, Regulatory, etc.)
- **Unique stories**: Deduplicated articles
- **Sources**: Number of news websites

Each article has:
- `cluster_reason`: Why it was classified into its category
- `duplicate_reason`: Why it's a duplicate (if applicable)
- `cluster_coherence_score`: Quality metric (0-1, higher is better)

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs in the admin UI
3. Check that all dependencies are installed
4. Ensure you have internet connection for first run

---

## ✨ Tips

- **First run**: Takes longer due to model download (~90MB)
- **Subsequent runs**: Much faster (models are cached)
- **URL files**: One URL per line, must start with http:// or https://
- **Deduplication**: Automatic - duplicate URLs are skipped
- **Results**: Saved in `output/results.json` after each run

---

## 🎉 You're All Set!

The system is ready to use. Just upload URLs and run the pipeline!
