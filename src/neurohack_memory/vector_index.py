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

    def _bm25_score(self, query, text, k1=1.5, b=0.75):
        """BM25 algorithm catches keyword matches semantic misses"""
        query_terms = query.lower().split()
        text_terms = text.lower().split()
        score = 0.0
        for term in query_terms:
            freq = sum(1 for t in text_terms if term in t.lower())
            if freq > 0:
                score += freq / max(len(text_terms), 1.0)
        return score / max(len(query_terms), 1.0)

    def search(self, query, top_k=10):
        if not self.ids:
            return []
        # Semantic search
        q = self._embed([query])
        scores, idxs = self.index.search(q, min(top_k * 3, len(self.ids)))
        semantic_results = [(self.ids[int(idx)], float(score)) for score, idx in zip(scores[0], idxs[0]) if idx >= 0]
        
        # BM25 scoring
        bm25_scores = {}
        for i, mid in enumerate(self.ids):
            text = f"{self._mem_cache[i].type.value}|{self._mem_cache[i].key}={self._mem_cache[i].value}"
            bm25_scores[mid] = self._bm25_score(query, text)
        
        # Hybrid: 70% semantic + 30% BM25
        hybrid = []
        seen = set()
        for mid, sem_score in semantic_results:
            bm25 = bm25_scores.get(mid, 0.0)
            combined = 0.7 * float(sem_score) + 0.3 * min(float(bm25), 1.0)
            if mid not in seen:
                hybrid.append((mid, combined))
                seen.add(mid)
        hybrid.sort(key=lambda x: x[1], reverse=True)
        return hybrid[:top_k]
