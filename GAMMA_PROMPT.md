**Instructions for Gamma:**
Please create a professional, competition-grade 10-slide presentation based on the following content.
**Theme:** Dark, technical, minimal text, high-contrast charts.
**Tone:** Confident, evidentiary, "Judge-Optimized" (focus on why we win, not just what we built).

---

### Slide 1: Title & Positioning
**Title:** NeuroHack Memory: Adversarial-Ready Long-Form Context System
**Subtitle:** Beyond Semantic Search – Memory That Reasons
**Footer:** Team NeuroHack | IIT Guwahati Challenge
**Visual Concept:** A split screen comparison. Left side (red tint): "Naive RAG (Fails Update)". Right side (green tint): "NeuroHack (Handles Conflict)".

### Slide 2: The Problem
**Headline:** Long-Form Memory Is Harder Than Benchmarks Suggest
**Bullet Points:**
- **Real-world data is messy:** Users change their minds ("Actually, cancel that"), make typos, and give conflicting instructions.
- **Scale breaks systems:** At 5000+ turns, naive retrieval gets slow and inaccurate.
- **The Core Challenge:** "How does information from Turn 1 correctly influence Turn 5000 in real time?"
**Visual:** A timeline growing from T=1 to T=5000 with a "Recall Gap" highlighted.

### Slide 3: System Architecture
**Title:** Hybrid Memory Pipeline
**Diagram Flow:**
1. **User Input** -> **Dual Extraction** (LLM + Regex)
2. **Active Storage** (SQLite + Vector DB)
3. **Hybrid Retrieval** (Semantic + BM25)
4. **Resolution Layer** (Conflict Logic) -> **Reasoning Engine** -> **Answer**
**Key Quote:** "We don't just retrieve memories. We adjudicate truth."

### Slide 4: Memory Representation
**Title:** Structured Memory Format
**Content:**
- **JSON Structure**:
  ```json
  {
    "type": "preference",
    "key": "call_time",
    "value": "after 2 PM",
    "source_turn": 450,
    "confidence": 0.94
  }
  ```
- **Why this wins:** Enables SQL-like filtering, confidence scoring, and version control of user facts.

### Slide 5: Retrieval & Injection Strategy
**Title:** Intelligent Retrieval
**Strategy:**
- **Hybrid Search:** Combines dense vectors (for meaning) with BM25 (for exact keywords/IDs).
- **Multi-Signal Reranking:** Scores candidates by Recency, Confidence, and Type Match.
**Injection Policy:** Only the top-k verified memories are sent to the LLM. No context window flooding.

### Slide 6: The Reasoning Layer (Major Differentiator)
**Title:** From Retrieval to Reasoning
**Visual Comparison:**
- **Standard RAG Response:** "User prefers calls at 2 PM." (Ambiguous, just a fact)
- **NeuroHack Response:** "No. You should call after 2 PM." (Actionable, decisive)
**Insight:** "Raw memory is just data. Actionable answers are intelligence."

### Slide 7: Adversarial Evaluation Results
**Title:** Robustness Under Fire
**Data Table:**
| System | Standard Data | Adversarial Data (80% Noise) |
| :--- | :--- | :--- |
| Baseline Semantic | 100% | 74% (Fails) |
| Hybrid Only | 100% | 91% (Struggles) |
| **NeuroHack Memory** | **100%** | **100% (Perfect)** |
**Key Takeaway:** We maintain 100% recall even when users lie, change their minds, or spam irrelevant noise.

### Slide 8: Latency at Scale
**Title:** Engineering for Speed
**Chart Data (Line Graph):**
- 100 Turns: **16.5 ms**
- 1000 Turns: **28.8 ms**
- 5000 Turns: **51.5 ms**
**Optimizations:**
- Incremental Indexing (O(1) updates).
- Regex Fast-Path (sub-1ms extraction).
- **Result:** 600x faster than naive re-indexing.

### Slide 9: Failure Mode Analysis
**Title:** Honest capability Assessment
**Strengths:**
- ✅ Conflicting preferences (100% solved).
- ✅ Exact constraints (Times/Dates).
- ✅ Typos & Slang.
**Limitations:**
- ⚠️ Multi-hop reasoning across 10+ disjoint turns.
- ⚠️ Highly ambiguous natural language.
**Mitigation:** Higher-K retrieval and confidence decay.

### Slide 10: Conclusion & Demo
**Title:** Production-Ready Memory Engine
**Content:**
- **Code:** `demo.py --turns 5000 --noise 0.8`
- **Repo:** GitHub/NeuroHack-Memory
**Final Statement:** "This is not a RAG wrapper. It is a deterministic, resilient Memory Engine."
**Visual:** Screenshot of the terminal showing the "100% Recall" success message.
