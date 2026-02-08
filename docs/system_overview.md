# System Overview & Status Report

## 🏗️ System Architecture

NeuroHack Memory is a **production-grade long-term memory system** designed for high-recall retrieval over 5,000+ conversation turns.

### Core Components
- **Backend (`server.py`)**: FastAPI server handling real-time requests.
    - Endpoints: `/query`, `/inject`, `/stats`, `/admin/seed`
    - **Fix**: Resolved 500 Error crash by fixing `memory_id` attribute access.
- **Memory Engine (`src/neurohack_memory/system.py`)**: 
    - Orchestrates extraction, storage, and retrieval.
    - **Polish**: Now tracks `use_count` and `last_used_turn` for dashboard metrics.
- **Extraction (`src/neurohack_memory/extractors.py`)**:
    - **Primary**: Groq API (`llama-3.3-70b-versatile`) for high-fidelity extraction.
    - **Secondary**: Regex fallback for sub-millisecond processing of known patterns.
    - **Fix**: Updated from decommissioned `llama3` model to supported `llama-3.3`.
- **Storage**:
    - **Metadata**: SQLite (`artifacts/memory_v2.sqlite`) for relational data.
    - **Vector**: FAISS (`IndexFlatIP`) for semantic search.
    - **Fix**: Switched to `memory_v2.sqlite` to resolve file locking issues.

## 🔄 Data Pipeline

1. **Ingestion**: `demo.py` loads `data/synth_1200.json` (prioritized) + `adversarial_dataset.json`.
2. **Processing**: User text -> Extraction (Groq) -> Embedding (SentenceTransformer) -> Storage.
3. **Retrieval**: 
    - Hybrid Search (Vector + Metadata filter)
    - Decay Scoring (Age + Confidence) -> **Tuned** for 5000 turns.
    - Conflict Resolution (Latest/Highest Confidence wins).
4. **Response**: JSON result with retrieved memories and injected context.

## ✅ Recent Upgrades & Fixes

1.  **Stable Data Ingestion**: Fixed `demo.py` to correctly load the synthetic dataset.
2.  **API Restoration**: Restored Groq extraction by updating the model name.
3.  **Crash Resolution**: Fixed the server-side crash during retrieval serialization.
4.  **Metrics Tracking**: Implemented usage counting for live dashboard statistics.

## 🚀 How to Run

### 1. Full Demo (5000 Turns)
```powershell
python demo.py --turns 5000
```
*Expect execution time to be longer than before due to active AI extraction.*

### 2. Evaluation (Metrics)
```powershell
python evaluation.py
```
*Generates `artifacts/metrics.json` with Recall/Precision scores.*

### 3. Smart Circuit Breaker & Graceful Degradation
To ensure production reliability, the system implements a **Latent Circuit Breaker** at the extraction layer:
- **Instant Failover**: If the LLM API (Groq/Grok) hits rate limits (429) or timeouts, the circuit opens immediately.
- **Zero-Latency Fallback**: The system instantly switches to **Regex Extraction** (<1ms), bypassing the API entirely for 60 seconds.
- **No User Impact**: The user experiences no latency spikes even during heavy load or API outages.
- **Auto-Recovery**: After the cooldown, the circuit enters a "half-open" state to test API health before fully recovering.

### 4. Incremental Indexing (FAISS)

### 5. Server (Manual Start)
```powershell
venv\Scripts\uvicorn server:app --host 0.0.0.0 --port 8000
```
