import argparse, json, random, os

def generate(n=1200, seed=42):
    random.seed(seed)
    conv = []
    conv.append({"turn": 1, "user": "Hi! My preferred language is Kannada. Please schedule calls after 11 AM. Also, never call on Sundays."})
    topics = ["project update", "invoice", "travel", "health", "shopping", "coding", "meeting"]
    fillers = ["Can you help me draft?", "What do you think?", "Explain this.", "Summarize.", "Help me decide."]
    for t in range(2, n+1):
        if t == 100:
            msg = "Remind me of my preferences again please."
        elif t == 500:
            msg = "What were my language and call time preferences?"
        elif t == 937:
            msg = "Can you call me tomorrow?"
        elif t == 1000:
            msg = "Before we schedule anything, remind me of my constraints."
        else:
            msg = f"[{random.choice(topics)}] {random.choice(fillers)}"
        conv.append({"turn": t, "user": msg})
    return conv

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=1200)
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    conv = generate(args.n)
    with open(args.out, "w") as f:
        json.dump(conv, f, indent=2)
    print(f"✓ Generated {len(conv)} turns → {args.out}")
