import argparse, json, os, asyncio
from neurohack_memory import MemorySystem
from neurohack_memory.utils import load_yaml

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conv", required=True)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--extractor", default="grok")
    args = ap.parse_args()
    os.environ["EXTRACTOR_PROVIDER"] = args.extractor
    cfg = load_yaml(args.config)
    sys = MemorySystem(cfg)
    with open(args.conv) as f:
        conv = json.load(f)
    checkpoints = set(cfg["evaluation"]["checkpoints"])
    print(f"\n{'='*100}\nDEMO: {len(conv)} turns, extractor={args.extractor}\nCheckpoints: {sorted(checkpoints)}\n{'='*100}\n")
    for item in conv:
        user = item["user"]
        res = await sys.process_turn(user)
        r = sys.retrieve(user)
        if res["turn"] in checkpoints:
            print(f"\n{'─'*100}\nCHECKPOINT TURN {res['turn']}\n{'─'*100}")
            print(f"User: {user[:120]}\nExtraction ({len(res['extracted'])} memories, {res['extract_ms']:.1f}ms):")
            for m in res['extracted'][:6]:
                print(f"  • {m.type.value:12} | {m.key:20}={m.value:30} conf={m.confidence:.2f} [turn {m.source_turn}]")
            print(f"\nRetrieval ({len(r['retrieved'])} hits, {r['retrieve_ms']:.1f}ms):")
            for i, rm in enumerate(r['retrieved'][:6], 1):
                m = rm.memory
                print(f"  {i}. score={rm.score:.3f} {m.type.value:12} | {m.key:20}={m.value:30} [turn {m.source_turn}]")
            print(f"\nInjected Context:\n  {r['injected_context'][:400]}")
    print(f"\n{'='*100}\nDemo complete.\n{'='*100}\n")
    sys.close()

if __name__ == "__main__":
    asyncio.run(main())
