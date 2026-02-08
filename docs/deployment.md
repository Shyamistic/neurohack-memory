# 🚀 Deployment Guide

This guide explains how to deploy the NeuroHack Memory System "Live" for demonstration and production use.

## Option 1: One-Click Production Launch (Recommended)
This is the fastest method to demonstrate the system to judges.

1.  **Navigate to the project folder**:
    ```bash
    cd neurohack-memory
    ```
2.  **Run the Production Script**:
    *   **Windows**: Double-click `run_prod.bat` or run:
        ```cmd
        run_prod.bat
        ```
    *   **Linux/Mac**: Run:
        ```bash
        ./run_demo.sh
        ```
3.  **What happens?**
    *   The **Backend Server** launches on `http://127.0.0.1:8000` (FastAPI).
    *   The **Frontend Dashboard** automatically opens in your browser at `http://localhost:8501`.
    *   *Note: Wait ~5 seconds for the backend to initialize before querying.*

---

## Option 2: Manual "Terminal-by-Terminal" Deployment
If you want granular control or need to debug specific components.

### Step 1: Start the Backend (The Brain)
Open a new terminal and run:
```bash
# Activate Virtual Environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Start FastAPI Server (Production Mode)
uvicorn server:app --host 127.0.0.1 --port 8000 --workers 1
```
*You should see: `✅ Memory System Online`*

### Step 2: Start the Frontend (The Interface)
Open a **second** terminal and run:
```bash
# Activate Virtual Environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Run Streamlit App
streamlit run app.py
```

---

## ☁️ Option 3: Free Cloud Deployment (e.g., Render/Railway)
This project is fully Dockerized for 1-click cloud deployment.

1.  **Push your code to GitHub/GitLab**.
2.  **Create a New Web Service** on [Render.com](https://render.com) or [Railway.app](https://railway.app).
3.  **Connect your Repository**.
4.  **Configuration**:
    *   **Runtime**: Docker
    *   **Environment Variables**:
        *   `GROQ_API_KEY`: (Optional) Your key.
        *   `PORT`: 8501 (Streamlit default).
5.  **Deploy**:
    *   The system will build `Dockerfile`.
    *   It will start `entrypoint.sh` which launches BOTH Backend and Frontend.
    *   **Access**: Visit your Render/Railway URL (e.g., `https://neurohack-memory.onrender.com`).

---

## 🔧 Troubleshooting

**"Backend Disconnected" on Dashboard:**
- Ensure the backend terminal is running and shows `Uvicorn running on http://127.0.0.1:8000`.
- If using a different port, update `API_URL` in `app.py`.

**Latency > 50ms:**
- Ensure you are using `127.0.0.1` and not `localhost` (Windows IPv6 issue).
- Check if `extractors.py` is falling back to Regex (Check logs for "Circuit Open").

**"Module Not Found":**
- Ensure you activated the `venv` before running commands.
