# ⚡ Quick Start - Copy & Paste These Commands

## First Time Setup (Do Once)

```bash
# 1. Clone repo
git clone https://github.com/dark-scientist/autonews.git
cd autonews/auto_news_intelligence

# 2. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Start the admin UI
streamlit run app_upload.py
```

Browser opens at http://localhost:8501

---

## Daily Use (Every Time)

```bash
# 1. Go to project and activate environment
cd autonews/auto_news_intelligence
source venv/bin/activate

# 2. Start admin UI
streamlit run app_upload.py
```

### In the Browser:
1. **Section 1**: Upload your URLs.txt file → Click "Confirm & Add"
2. **Section 2**: Click "▶ Run Full Pipeline" → Wait 2-3 minutes
3. **Section 3**: Click "📋 Copy to streamlit-app/"

---

## Update Live Dashboard

```bash
# From auto_news_intelligence directory
cd ../streamlit-app
git add results.json
git commit -m "Update: $(date +%Y-%m-%d)"
git push origin main
```

Wait 1-2 minutes for Streamlit Cloud to deploy.

---

## That's It! 🎉

**3 commands to start:**
1. `cd autonews/auto_news_intelligence`
2. `source venv/bin/activate`
3. `streamlit run app_upload.py`

**Then use the browser UI for everything else!**
