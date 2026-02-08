from typing import List, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from .types import MemoryEntry

class VectorIndex:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dim)
        self.ids = []
        self._mem_cache = []

    def _embed(self, texts):
        emb = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return emb.astype("float32")

    def add_or_update(self, memories: List[MemoryEntry]):
        # Optimization: Incrementally add new memories instead of full rebuild
        # This allows duplicates in the index, but retrieval deduplicates by ID.
        self._mem_cache.extend(memories)
        
        # Keep track of IDs for later retrieval/BM25
        self.ids.extend([m.memory_id for m in memories])
        
        new_texts = [f"{m.type.value}|{m.key}={m.value}" for m in memories]
        if new_texts:
            emb = self._embed(new_texts)
            self.index.add(emb)

    def search(self, query, top_k=10):
        if not self.ids:
            return []
            
        # Semantic search (FAISS is O(log N) or O(1) mostly)
        q = self._embed([query])
        
        # Search for slightly more candidates to give reranker variety
        k_search = min(top_k * 5, len(self.ids)) 
        scores, idxs = self.index.search(q, k_search)
        
        # Return tuples (mid, score)
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx >= 0:
                results.append((self.ids[int(idx)], float(score)))
                
        return results
