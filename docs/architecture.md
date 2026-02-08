# NeuroHack Memory System Architecture

```mermaid
graph TD
    subgraph "Frontend Layer"
        UI[Streamlit Dashboard]
        User[User]
        User -- "Queries / Updates" --> UI
        UI -- "Live Metrics" --> UI
    end

    subgraph "Service Layer (FastAPI)"
        API[Server (server.py)]
        UI -- "HTTP/JSON" --> API
        
        System[MemorySystem (system.py)]
        API -- "Process Turn" --> System
        API -- "Retrieve" --> System
    end

    subgraph "Core Logic Layer"
        Extractor[Extractor (extractors.py)]
        System -- "Async Extraction" --> Extractor
        
        Circuit[Circuit Breaker]
        Extractor -- "Check Health" --> Circuit
        Circuit -- "Open (Fast Fallback)" --> Regex[Regex Extractor]
        Circuit -- "Closed (Normal)" --> LLM[Groq/Grok API]
        
        VIndex[Vector Index (vector_index.py)]
        System -- "Semantic Search" --> VIndex
        
        Store[SQLite Store (store_sqlite.py)]
        System -- "Persist / Load" --> Store
    end

    subgraph "Data Layer"
        SQLite[(SQLite DB)]
        Store -- "WAL Mode" --> SQLite
        
        FAISS[(FAISS Index)]
        VIndex -- "Vector Ops" --> FAISS
    end

    subgraph "Optimization layer"
        Async[AsyncIO Thread Pool]
        System -- "Offload Write" --> Async
        Async --> Store
        Async --> VIndex
    end
```

## Description
1.  **User Interaction**: The user interacts with the **Streamlit Dashboard**, which sends requests to the **FastAPI Server**.
2.  **Async Processing**: The `MemorySystem` orchestrates the flow. Heavy write operations (Ingestion) are offloaded to a background thread pool to prevent blocking the read path (Retrieval).
3.  **Circuit Breaker**: The extraction layer uses a **Latent Circuit Breaker**. If the LLM API fails or throttles, it instantly switches to a **Regex** fallback, ensuring <50ms latency.
4.  **Hybrid Storage**:
    *   **SQLite (WAL Mode)**: Stores structured memory objects with high concurrency.
    *   **FAISS/VectorIndex**: Handles semantic similarity search. We removed the O(N) loop here to use pure vector search.
