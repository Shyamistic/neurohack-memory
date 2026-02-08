
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
import os
import time
import json
import pandas as pd
from typing import List, Optional, Dict, Any

from neurohack_memory import MemorySystem
from neurohack_memory.utils import load_yaml

# -----------------------------------------------------------------------------
# SETUP
# -----------------------------------------------------------------------------
app = FastAPI(title="NeuroHack Memory Backend", version="2.0.0")

# Singleton System
sys: Optional[MemorySystem] = None

def get_system():
    global sys
    if sys is None:
        print("⚡ Initializing Memory System...")
        cfg = load_yaml("config.yaml")
        
        # Ensure artifacts directory
        if not os.path.exists("artifacts"):
            os.makedirs("artifacts")
            
        # Respect config.yaml storage path if present, else default
        if "storage" not in cfg:
            cfg["storage"] = {}
        if "path" not in cfg["storage"]:
            cfg["storage"]["path"] = "artifacts/memory.sqlite"
        
        sys = MemorySystem(cfg)
        print("✅ Memory System Online")
    return sys

# -----------------------------------------------------------------------------
# MODELS
# -----------------------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str

class InjectRequest(BaseModel):
    text: str

class SeedRequest(BaseModel):
    texts: List[str]

# -----------------------------------------------------------------------------
# ENDPOINTS
# -----------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    get_system()

@app.get("/")
def read_root():
    return {"status": "online", "system": "NeuroHack Memory Console v2.0"}

@app.post("/query")
async def query_memory(req: QueryRequest):
    try:
        t_start = time.perf_counter()
        s = get_system()
        res = s.retrieve(req.query)
        
        # Serialize for transport
        if res and "retrieved" in res:
            # We need to break circular refs or complex objects if any
            # The MemoryCell object might not be JSON serializable directly
            # Let's construct a clean response
            serialized_hits = []
            for hit in res["retrieved"]:
                serialized_hits.append({
                    "score": hit.score,
                    "memory": {
                        "value": hit.memory.value,
                        "key": hit.memory.key,
                        "confidence": hit.memory.confidence,
                        "type": hit.memory.type.value,
                        "source_turn": hit.memory.source_turn,
                        "id": hit.memory.memory_id
                    }
                })
            
            dur_ms = (time.perf_counter() - t_start) * 1000
            print(f"🚀 Query Processed in {dur_ms:.2f}ms")
            
            return {
                "retrieved": serialized_hits,
                "context": res.get("context", "")
            }
        return {"retrieved": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inject")
async def inject_memory(req: InjectRequest):
    try:
        s = get_system()
        # sys.process_turn is async
        await s.process_turn(req.text)
        return {"status": "committed", "text": req.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/seed")
async def seed_data(req: SeedRequest):
    try:
        s = get_system()
        for text in req.texts:
            await s.process_turn(text)
        return {"status": "seeded", "count": len(req.texts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/clear")
def clear_db():
    try:
        s = get_system()
        s.store.conn.execute("DELETE FROM memories")
        s.store.conn.commit()
        s._memory_cache.clear()
        s.turn = 0
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def get_stats():
    try:
        s = get_system()
        conn = s.store.conn
        
        # Counts
        type_dist_query = "SELECT type, COUNT(*) as count FROM memories GROUP BY type"
        df_types = pd.read_sql_query(type_dist_query, conn)
        total = df_types["count"].sum() if not df_types.empty else 0
        
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM memories WHERE use_count > 0")
        resolved = cur.fetchone()[0]
        
        # Live Distribution
        df_live = pd.read_sql_query("SELECT confidence, type FROM memories", conn)
        live_stats = df_live.to_dict(orient="records")
        
        return {
            "total_memories": int(total),
            "conflicts_resolved": int(resolved),
            "type_distribution": df_types.to_dict(orient="records"),
            "live_stats": live_stats 
        }
    except Exception as e:
        # Return empty safe stats if DB locked or empty
        return {
             "total_memories": 0,
             "conflicts_resolved": 0,
             "type_distribution": [],
             "live_stats": []
        }

@app.get("/history/evolution")
def get_evolution(key: Optional[str] = None):
    try:
        s = get_system()
        conn = s.store.conn
        query = "SELECT memory_id, type, key, value, confidence, source_turn FROM memories ORDER BY source_turn DESC"
        df = pd.read_sql_query(query, conn)
        
        if key:
            df = df[df["key"] == key]
        
        return df.to_dict(orient="records")
    except Exception as e:
        return []

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
    # Trigger Reload
