
import asyncio
import time
import statistics
import matplotlib.pyplot as plt
from neurohack_memory import MemorySystem
from neurohack_memory.utils import load_yaml
import os

async def benchmark(cfg, n_turns):
    print(f"Benchmarking {n_turns} turns...")
    sys = MemorySystem(cfg)
    
    # Pre-populate dummy memories to simulate scale
    # We do this directly to avoid the overhead of full processing for the setup phase
    # But for accuracy, let's use process_turn on a subset or just inject
    
    # Actually, let's just inject raw memories to save time
    from neurohack_memory.types import MemoryEntry, MemoryType
    
    dummy_memories = []
    for i in range(n_turns):
        dummy_memories.append(MemoryEntry(
            memory_id=f"bench_{i}",
            type=MemoryType.preference,
            key=f"key_{i}",
            value=f"value_{i}",
            source_turn=i,
            confidence=0.9,
            source_text="benchmark"
        ))
    
    sys.store.upsert_many(dummy_memories)
    sys.vindex.add_or_update(dummy_memories)
    sys.turn = n_turns
    
    # Now measure retrieval latency
    # We'll run 50 queries
    latencies = []
    queries = ["what is my key_10 preference?", "find key_500", "update specifically key_900"]
    
    for _ in range(50):
        q = queries[_ % len(queries)]
        t0 = time.time()
        sys.retrieve(q)
        latencies.append((time.time() - t0) * 1000) # ms
        
    p95 = statistics.quantiles(latencies, n=20)[18] # 95th percentile
    print(f"-> {n_turns} turns: p95 = {p95:.2f} ms")
    sys.close()
    return p95

async def main():
    cfg = load_yaml("config.yaml")
    
    # Disable console logging if any to keep output clean
    
    scales = [100, 500, 1000, 2000, 5000]
    results = []
    
    print("\n" + "="*60)
    print("LATENCY AT SCALE BENCHMARK")
    print("="*60)
    
    for n in scales:
        lat = await benchmark(cfg, n)
        results.append(lat)
        
    # Generate Graph Data
    print("\n" + "="*60)
    print("RESULTS FOR README")
    print("="*60)
    print("Turns\tLatency (ms)")
    for n, lat in zip(scales, results):
        print(f"{n}\t{lat:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
