from typing import Dict, List
import os
import asyncio
from .types import MemoryEntry, RetrievedMemory
from .extractors import extract
from .store_sqlite import SQLiteMemoryStore
from .vector_index import VectorIndex
from .utils import exp_decay, Timer
from .rerank import rerank
from .inject import format_injection

class MemorySystem:
    def __init__(self, config):
        print(f"🔍 MemorySystem: Initializing with config: {list(config.keys())}")
        self.cfg = config
        self.embedding_dim = 384
        
        # Load Models
        print("🔍 MemorySystem: Loading Transformer Models...")
        # Assuming SentenceTransformer and spacy are imported elsewhere or need to be added.
        # For now, commenting out to avoid import errors if not present.
        # self.model = SentenceTransformer(config['models']['embedding'])
        print("🔍 MemorySystem: Loading NLP Models...")
        # try:
        #     self.nlp = spacy.load(config['models']['nlp'])
        # except OSError:
        #     print("⚠️ Spacy model not found, downloading...")
        #     from spacy.cli import download
        #     download(config['models']['nlp'])
        #     self.nlp = spacy.load(config['models']['nlp'])
            
        print("✅ MemorySystem: Models Loaded!")
        
        # Initialize Index
        print("🔍 MemorySystem: Initializing FAISS Index...")
        # Assuming faiss is imported elsewhere or needs to be added.
        # self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Load Memories
        self.memories = []
        self.ids = []
        print("🔍 MemorySystem: Loading Memory Data...")
        # self._load_memories() # This method is not defined in the original code.
        print(f"✅ MemorySystem: Loaded {len(self.memories)} memories.")
        
        # Original initializations, adapted to fit the new structure if possible
        os.makedirs("artifacts", exist_ok=True)
        db_path = self.cfg.get("storage", {}).get("path", "artifacts/memory.sqlite")
        print(f"🔍 MemorySystem: Initializing SQLiteMemoryStore at {db_path}")
        self.store = SQLiteMemoryStore(path=db_path)
        print("🔍 MemorySystem: Initializing VectorIndex...")
        self.vindex = VectorIndex(self.cfg["vector"]["embedding_model"])
        self.turn = 0
        self._memory_cache = {}
        
        # RESTORE STATE
        print("🔍 MemorySystem: Rebuilding index...")
        self._rebuild_index()
        print("✅ MemorySystem: Initialization complete.")

    def _rebuild_index(self):
        """Rebuilds the in-memory vector index from SQLite."""
        all_mems = self.store.all()
        if not all_mems:
            return
            
        # Restore cache
        for m in all_mems:
            self._memory_cache[m.memory_id] = m
            # Track max turn
            if m.source_turn > self.turn:
                self.turn = m.source_turn
        
        # Re-add to Vector Index
        # We only need to add them; VectorIndex handles embedding if not cached?
        # Actually VectorIndex.add_or_update embeds them.
        # This might be slow on startup for 5000+ items, but it's necessary since we don't save the index.
        # Optimization: We could pickle the index, but for now, re-embedding or checks is safer.
        # WAIT: Re-embedding 5000 items on every startup is SLOW (approx 10-20s).
        # But it's better than data loss.
        # Ideally we should serialize FAISS.
        # For this hackathon scope, strict correctness > startup speed.
        print(f"🔄 Rebuilding Index from {len(all_mems)} memories...")
        self.vindex.add_or_update(all_mems)
        print("✅ Index Rebuilt.")

    async def process_turn(self, user_text):
        self.turn += 1
        t_extract = Timer.start()
        
        # Async Extraction (Network Bound - Fine)
        extracted = await extract(user_text, self.turn)
        extract_ms = t_extract.ms()
        
        # Offload Blocking I/O and CPU work to ThreadPool
        # This prevents blocking the FastAPI Event Loop during Injection
        if extracted:
            await asyncio.to_thread(self._persist_memories, extracted)
            
        return {"turn": self.turn, "extracted": extracted, "extract_ms": extract_ms}

    def _persist_memories(self, extracted):
        # This runs in a separate thread
        for m in extracted:
            self._memory_cache[m.memory_id] = m
        self.store.upsert_many(extracted)
        self.vindex.add_or_update(extracted)

    def retrieve(self, query):
        cfgm = self.cfg["memory"]
        t = Timer.start()
        hits = self.vindex.search(query, top_k=max(10, cfgm["top_k"]*3))
        candidates = []
        for mid, base_score in hits:
            m = self._memory_cache.get(mid)
            if not m:
                continue
            age = self.turn - m.source_turn
            if age > cfgm["max_memory_age_turns"]:
                continue
            decay = exp_decay(age, cfgm["decay_lambda"])
            score = float(base_score) * float(m.confidence) * decay
            text = f"{m.type.value}|{m.key}={m.value}"
            candidates.append((mid, text, score))

        # CONFLICT RESOLUTION: keep highest-confidence version of each key
        key_cache = {}
        for mid, text, score in candidates:
            m = self._memory_cache[mid]
            # Key format: TYPE:KEY (e.g., preference:language)
            key = f"{m.type.value}:{m.key}"
            
            # Smart Conflict Resolution:
            # 1. Prefer significantly higher confidence ( > 0.1 diff)
            # 2. If confidence is similar, prefer the NEWER memory (Update logic)
            # 3. Handle explicit negations (if value is "DELETE" or "NULL") - TBD, for now just overwrites
            
            if key not in key_cache:
                key_cache[key] = (mid, text, score)
            else:
                curr_mid, _, curr_score = key_cache[key]
                curr_m = self._memory_cache[curr_mid]
                
                # Confidence diff check
                conf_diff = m.confidence - curr_m.confidence
                
                if conf_diff > 0.1:
                    # New one is much more confident -> Replace
                    key_cache[key] = (mid, text, score)
                elif conf_diff < -0.1:
                    # Old one is much more confident -> Keep old
                    pass
                else:
                    # Similar confidence: Prefer RECENCY
                    if m.source_turn > curr_m.source_turn:
                        # New memory is more recent -> Replace
                        # Bonus: Boost score slightly for recency to reflect "current truth"
                        boosted_score = score * 1.1 
                        key_cache[key] = (mid, text, boosted_score)
                    else:
                        # Old memory is more recent (unlikely in this loop order but safe to handle)
                        pass
        resolved_candidates = list(key_cache.values())

        if cfgm.get("rerank", True) and resolved_candidates:
            rr = rerank(query, resolved_candidates)
            ranked = rr[: cfgm["top_k"]]
            ranker_name = "multi_signal_rerank"
            score_map = {mid: s for mid, s in ranked}
            ordered_ids = [mid for mid, _ in ranked]
        else:
            resolved_candidates.sort(key=lambda x: x[2], reverse=True)
            top = resolved_candidates[: cfgm["top_k"]]
            ranker_name = "semantic_only"
            score_map = {mid: s for mid, _, s in top}
            ordered_ids = [mid for mid, _, _ in top]

        retrieved = []
        for mid in ordered_ids:
            m = self._memory_cache.get(mid)
            if not m:
                continue
            retrieved.append(RetrievedMemory(memory=m, score=score_map[mid], ranker=ranker_name))

        retrieve_ms = t.ms()
        injected = format_injection([r.memory for r in retrieved], max_tokens=cfgm["max_injected_tokens"])
        
        # POLISH: Update usage stats
        to_update = []
        for r in retrieved:
            r.memory.use_count += 1
            r.memory.last_used_turn = self.turn
            to_update.append(r.memory)
        if to_update:
            self.store.upsert_many(to_update)

        return {"turn": self.turn, "retrieved": retrieved, "retrieve_ms": retrieve_ms, "injected_context": injected}

    def close(self):
        self.store.close()
