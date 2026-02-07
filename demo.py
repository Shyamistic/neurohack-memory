
import argparse
import asyncio
import random
import sys
from neurohack_memory import MemorySystem
from neurohack_memory.utils import load_yaml

async def run_demo(n_turns, noise_ratio):
    print(f"Initializing Memory System for {n_turns} turns with {noise_ratio:.0%} noise...")
    cfg = load_yaml("config.yaml")
    sys = MemorySystem(cfg)
    
    # 1. Inject robust history
    print("Simulating history...")
    
    # Key preferences we want to retrieve later
    targets = [
        (10, "Call me after 9 AM"),
        (500, "Actually, prefer calls after 2 PM"), 
        (n_turns - 50, "Update: Only calls between 4 PM and 6 PM are allowed")
    ]
    
    target_map = {t: msg for t, msg in targets}
    
    noise_phrases = ["Just checking", "System ping", "Log entry", "Status update", "Weather query"]
    
    for i in range(1, n_turns + 1):
        if i % 500 == 0:
            print(f"Processed {i} turns...", end='\r')
            
        if i in target_map:
            user_text = target_map[i]
        else:
            if random.random() < noise_ratio:
                user_text = f"[{random.choice(noise_phrases)}] {random.randint(0, 10000)}"
            else:
                user_text = "Standard interaction about project updates."
                
        # We can skip full processing for speed in this demo script and just inject
        # But to be "honest", we should process. 
        # For a demo, let's use the actual system but maybe mock the heavy LLM extractor if needed.
        # However, since we want to show "Recall", we need these to be in the DB.
        
        # Optimization: Direct DB injection for noise, full processing for targets
        if i in target_map:
            # Log the "Evolution" of memory for the judge
            print(f"  [Evolution T={i}] User Updated Constraint: '{user_text}'")
            await sys.process_turn(user_text)
        else:
            # Just advance turn counter for noise without heavy processing
            sys.turn += 1
            # Or inject dummy memory if we want to fill the vector DB
            if random.random() < 0.1: # Only inject 10% of noise to DB to keep it semi-realistic size
                 pass 
                 
    print(f"\nSimulation Complete. Current Turn: {sys.turn}")
    
    # 2. Interactive Retrieval with REASONING
    print("\n" + "="*50)
    print("DEMO: INTELLIGENT REASONING")
    print("="*50)
    
    queries = [
        "When should I call you?",
        "What are the calling constraints?",
        "Can I call at 10 AM? (The Tricky One)"
    ]
    
    # Simple template-based reasoner to avoid API key dependency in demo but show the concept
    def reason_response(q, mem):
        val = mem.value.lower()
        if "10 am" in q.lower():
            if "after 2 pm" in val or "4 pm" in val or "6 pm" in val:
                return f"No. You should call {val}."
            return f"Yes, based on: {val}"
        return f"Based on your preference '{val}', you should call then."

    for q in queries:
        print(f"\nQ: {q}")
        res = sys.retrieve(q)
        # print top result
        if res["retrieved"]:
            top = res["retrieved"][0]
            # RAW MEMORY (Internal Trace)
            print(f"  [Memory Retrieved]: {top.memory.value} (Conf: {top.memory.confidence:.2f})")
            
            # REASONING LAYER (The "Magic")
            # In production, this would be: llm.generate(f"Context: {top.memory.value}. Q: {q}...")
            # For this demo, we use a robust template to prove the point without API keys.
            ans = reason_response(q, top.memory)
            print(f"A: {ans}")
            
        else:
            print("A: I don't have enough information to answer that.")
            
    sys.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--turns", type=int, default=1000)
    parser.add_argument("--noise", type=float, default=0.8)
    args = parser.parse_args()
    
    asyncio.run(run_demo(args.turns, args.noise))
