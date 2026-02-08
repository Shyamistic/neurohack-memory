# NeuroHack Memory System 🧠

## Overview
NeuroHack Memory is a high-performance, async-optimized memory system designed for real-time AI agents. It features:
- **Hybrid Storage**: SQLite (Structured) + FAISS (Semantic Vector Search).
- **Latency-Critical Architecture**: <50ms query time using Async I/O offloading and WAL mode.
- **Robustness**: Smart Circuit Breaker that fails over to Regex extraction (<1ms) if LLM APIs throttle.
- **Conflict Resolution**: Deterministic handling of contradictory memories (e.g., "Call me at 9am" vs "Actually 10am").

## 📂 Project Structure
- `src/`: Core logic (`system.py`, `extractors.py`, etc.)
- `docs/`: Detailed documentation and architecture diagrams.
- `artifacts/`: Database and metrics storage (auto-generated).
- `app.py`: Streamlit Dashboard (Frontend).
- `server.py`: FastAPI Backend.
- `demo.py`: Terminal-based testing script (Generates data).

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.9+
- OpenAI API Key (or Groq/xAI Key) for extraction (Optional - system falls back to regex).

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` file (or rename `.env.example`):
```ini
GROQ_API_KEY=your_key_here
XAI_API_KEY=your_key_here
```
*Note: If no keys are provided, the system runs in "Fast Regex Mode" automatically.*

---

## 🧪 How to Test (Terminal)
To verify the system's core logic and data ingestion without the UI:

1. **Run the Demo Script**:
   This script ingests conversation data from `data/synth_1200.json` and performs queries.
   ```bash
   python demo.py
   ```
2. **Verify Output**:
   - Watch for `Ingesting...` progress.
   - See "Latency: XXms" output.
   - Confirm retrieval answers match expectations.

---

## 🖥️ How to Run (Live Dashboard)
To experience the full Real-Time UI with Glassmorphism:

1. **Start the Production Stack**:
   Double-click `run_prod.bat` OR run:
   ```bash
   run_prod.bat
   ```
   *This launches both the Backend (Port 8000) and Frontend (Port 8501).*

2. **Open Dashboard**:
   - Go to `http://localhost:8501`.
   - **Status Indicator**: Should say "● ONLINE • PRODUCTION BACKEND CONNECTED".

3. **Live Interaction**:
   - **Tab 1 (Live Interaction)**: Type "Can I call at 10 am?".
     - See **< 50ms** latency.
     - See "YES. According to your preferences..." response.
   - **Tab 2 (Metrics)**: View Recall/Precision graphs.
   - **Tab 3 (Internals)**: View raw database rows and memory evolution.

---

## 📖 Documentation
- [Deployment Guide (Detailed)](docs/deployment.md)
- [System Overview](docs/system_overview.md)
- [Architecture Diagram](docs/architecture.md)
- [Walkthrough & Verification](docs/walkthrough.md)
