
import argparse
import asyncio
import json
import random
import requests
import time
import sys
import os

# Try importing local system for offline fallback
try:
    from neurohack_memory import MemorySystem
    from neurohack_memory.utils import load_yaml
    HAS_LOCAL = True
except ImportError:
    HAS_LOCAL = False

API_URL = "http://localhost:8000"

def get_backend_status():
    try:
        res = requests.get(f"{API_URL}/", timeout=1)
        return res.status_code == 200
    except:
        return False

async def run_demo(n_turns, noise_ratio):
    print(f"🚀 Initializing NeuroHack Data Generator for {n_turns} turns...")
    
    use_api = get_backend_status()
    sys = None
    
    if use_api:
        print("✅ Backend Detected: Seeding via API (Live Updates)")
    else:
        print("⚠️ Backend Offline: Seeding via Direct DB Access (Restart Backend after this!)")
        if HAS_LOCAL:
            cfg = load_yaml("config.yaml")
            sys = MemorySystem(cfg)
        else:
            print("❌ Error: Cannot run offline (neurohack_memory not found). Run `run_prod.bat` first.")
            return

    # 1. LOAD DATASET
    # 1. LOAD DATASET
    print("📂 Loading Datasets...")
    dataset = []
    
    # Try loading synth_1200.json first (User Preference)
    if os.path.exists("data/synth_1200.json"):
        try:
            with open("data/synth_1200.json", "r") as f:
                d = json.load(f)
                dataset.extend(d)
                print(f"   Loaded {len(d)} turns from 'data/synth_1200.json'.")
        except Exception as e:
            print(f"   ❌ Failed to load synth_1200.json: {e}")

    # Also load adversarial if available
    if os.path.exists("data/adversarial_dataset.json"):
        try:
            with open("data/adversarial_dataset.json", "r") as f:
                d = json.load(f)
                dataset.extend(d)
                print(f"   Loaded {len(d)} turns from 'data/adversarial_dataset.json'.")
        except Exception as e:
            print(f"   ❌ Failed to load adversarial_dataset.json: {e}")
            
    if not dataset:
        print("   ⚠️ No datasets loaded. Falling back to synthetic stream.")

    # 2. PREPARE STREAM
    # We want facts, constraints, and preferences.
    # We will overlay targets.
    
    targets = {
        10: "Preference: Call me after 9 AM",
        500: "Preference: Actually, prefer calls after 2 PM", 
        int(n_turns * 0.9): "Preference: Update: Only calls between 4 PM and 6 PM are allowed"
    }
    
    # Pre-generate all text to ensure we use valid JSON data
    stream = []
    
    print(f"📦 Generating stream for {n_turns} turns...")
    for i in range(1, n_turns + 1):
        if i in targets:
            text = targets[i]
        else:
            # Use dataset if available, wrapping around
            if dataset:
                item = dataset[(i-1) % len(dataset)]
                text = item.get("user", "")
            else:
                # Fallback synthetic
                text = f"System log entry {i}"
        stream.append(text)

    # 3. INJECT
    start_time = time.time()
    batch_size = 100 # Batch size for API
    
    if use_api:
        # Batch Injection
        for i in range(0, len(stream), batch_size):
            batch = stream[i : i + batch_size]
            try:
                # Use the bulk seed endpoint
                res = requests.post(f"{API_URL}/admin/seed", json={"texts": batch})
                if res.status_code != 200:
                    print(f"\n❌ Batch failed: {res.text}")
                
                # Progress
                current = min(i + batch_size, n_turns)
                pct = (current / n_turns) * 100
                print(f"  Processed {current}/{n_turns} ({pct:.1f}%)", end='\r')
            except Exception as e:
                print(f"\n❌ Network Error: {e}")
                break
    else:
        # Offline Injection
        for i, text in enumerate(stream):
            await sys.process_turn(text)
            if (i+1) % 100 == 0:
                print(f"  Processed {i+1}/{n_turns}...", end='\r')

    duration = time.time() - start_time
    print(f"\n✅ Seeding Complete in {duration:.2f}s")
    
    if not use_api and sys:
        sys.close()
        print("⚠️  REMINDER: Restart `server.py` (or run_prod.bat) to load these new memories!")

    # 2. VERIFICATION QUERY
    print("\n" + "="*50)
    print("VERIFICATION: RETRIEVAL TEST")
    print("="*50)
    
    q = "When can I call?"
    print(f"Q: {q}")
    
    if use_api:
        try:
            res = requests.post(f"{API_URL}/query", json={"query": q}).json()
            if res.get("retrieved"):
                top = res["retrieved"][0]["memory"]["value"]
                print(f"A: [API] {top}")
            else:
                print("A: [API] No match found.")
        except Exception as e:
             print(f"Error querying API: {e}")
    else:
        # Offline query check 
        print("(Skipping query check - requires restart)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--turns", type=int, default=1000)
    parser.add_argument("--noise", type=float, default=0.8)
    args = parser.parse_args()
    
    asyncio.run(run_demo(args.turns, args.noise))
