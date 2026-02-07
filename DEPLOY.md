# 🚀 Deploying NeuroHack Dashboard

You can host this dashboard for **free** on Streamlit Community Cloud. This gives judges a URL to click instead of running code.

## Option 1: The "Lazy" Way (Recommended)
1. Fork this repo to your own GitHub account.
2. Go to [share.streamlit.io](https://share.streamlit.io/).
3. Login with GitHub.
4. Click **"New App"**.
5. Select your `neurohack-memory` repo.
6. Set "Main file path" to `app.py`.
7. Click **Deploy**.

## Option 2: Run Locally (For Demo Video)
```bash
pip install streamlit
streamlit run app.py
```
This opens the dashboard in your browser at `localhost:8501`.

## Configuration
No special secrets are required for the demo mode as it uses the local SQLite/FAISS instance generated in memory.
