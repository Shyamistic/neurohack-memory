import argparse, json, os, asyncio, statistics
from neurohack_memory import MemorySystem
from neurohack_memory.utils import load_yaml

def recall_check(retrieved, keywords):
    text = " ".join([f"{rm.memory.key} {rm.memory.value}".lower() for rm in retrieved])
    return all(kw.lower() in text for kw in keywords)

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conv", required=True)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", required=True)
    ap.add_argument("--extractor", default="grok")
    args = ap.parse_args()
    os.environ["EXTRACTOR_PROVIDER"] = args.extractor
    cfg = load_yaml(args.config)
    sys = MemorySystem(cfg)
    with open(args.conv) as f:
        conv = json.load(f)
    checkpoints = cfg["evaluation"]["checkpoints"]
    recall_k = cfg["evaluation"]["recall_k"]
    expected = {100: ["kannada", "11", "sundays"], 500: ["kannada", "11", "sundays"], 937: ["11"], 1000: ["kannada", "11", "sundays"], 1200: ["kannada", "11"]}
    retrieval_ms = []
    extract_ms = []
    recall_hits = 0
    recall_total = 0
    print(f"\nEvaluating {len(conv)} turns...")
    for i, item in enumerate(conv):
        if (i+1) % 200 == 0:
            print(f"  Turn {i+1}/{len(conv)}")
        user = item["user"]
        res = await sys.process_turn(user)
        extract_ms.append(res["extract_ms"])
        r = sys.retrieve(user)
        retrieval_ms.append(r["retrieve_ms"])
        if res["turn"] in checkpoints:
            retrieved = r["retrieved"][:recall_k]
            recall_total += 1
            if recall_check(retrieved, expected.get(res["turn"], [])):
                recall_hits += 1
                status = "✓"
            else:
                status = "✗"
            print(f"    Turn {res['turn']:4d}: recall check {status}")
    metrics = {
        "total_turns": len(conv),
        "extractor": args.extractor,
        "recall_at_checkpoints": recall_hits / max(1, recall_total),
        "extract_latency_ms": {"mean": statistics.mean(extract_ms), "p95": sorted(extract_ms)[int(0.95*len(extract_ms))-1] if len(extract_ms) >= 20 else max(extract_ms)},
        "retrieval_latency_ms": {"mean": statistics.mean(retrieval_ms), "p95": sorted(retrieval_ms)[int(0.95*len(retrieval_ms))-1] if len(retrieval_ms) >= 20 else max(retrieval_ms)},
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n{'='*80}\nRECAll @ checkpoints: {metrics['recall_at_checkpoints']:.1%}\nExtract latency (p95): {metrics['extract_latency_ms']['p95']:.1f}ms\nRetrieve latency (p95): {metrics['retrieval_latency_ms']['p95']:.1f}ms\nMetrics saved → {args.out}\n{'='*80}\n")
    sys.close()

if __name__ == "__main__":
    asyncio.run(main())
