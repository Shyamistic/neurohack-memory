
from typing import List, Tuple
from rapidfuzz import fuzz

def rerank(query, candidates):
    """Multi-signal reranking: fuzzy + term overlap + type coherence"""
    scored = []
    query_terms = set(query.lower().split())
    
    for mid, text, base in candidates:
        # Signal 1: Fuzzy keyword matching
        f = fuzz.token_set_ratio(query.lower(), text.lower()) / 100.0
        
        # Signal 2: Term overlap
        text_terms = set(text.lower().split())
        overlap = len(query_terms & text_terms) / max(len(query_terms), 1.0)
        
        # Signal 3: Type coherence (constraints > preferences > facts)
        type_scores = {"constraint": 0.95, "preference": 0.90, "fact": 0.85, "commitment": 0.80}
        type_score = 0.5
        for t, s in type_scores.items():
            if f"|{t}|" in text.lower():
                type_score = s
                break
        
        # Weighted combination
        combined = (
            0.50 * base +           # semantic foundation (strongest signal)
            0.25 * f +              # fuzzy keyword match
            0.15 * overlap +        # term overlap
            0.10 * type_score       # memory type reliability
        )
        
        scored.append((mid, combined))
    
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored
