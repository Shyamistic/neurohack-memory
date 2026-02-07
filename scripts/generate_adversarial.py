import argparse
import json
import random
import os
import copy

def introduce_typo(text, probability=0.1):
    """Randomly swaps characters or drops vowels."""
    if random.random() > probability:
        return text
    
    words = text.split()
    new_words = []
    for word in words:
        if len(word) > 3 and random.random() < 0.3:
            # Swap chars
            idx = random.randint(0, len(word)-2)
            word = word[:idx] + word[idx+1] + word[idx] + word[idx+2:]
        elif random.random() < 0.1:
            # Drop vowel
            word = "".join([c for c in word if c.lower() not in "aeiou"])
        new_words.append(word)
    return " ".join(new_words)

def generate_adversarial(base_path, out_path, noise_ratio=0.5):
    with open(base_path, "r") as f:
        base_conv = json.load(f)
    
    adv_conv = []
    
    # 1. Inject Noise (Irrelevant turns)
    noise_phrases = [
        "Just checking in.", "Did you see that movie?", "Weather is nice.", 
        "Walking the dog.", "Lunch time.", "Ignore this.", "System check.",
        "Ping.", "Pong.", "Any updates on the football game?"
    ]
    
    # 2. Inject Constraints & Updates (Conflicts)
    # We will simulate a user changing their mind about the "call time"
    # Original was "after 11 AM". 
    # We will verify if the system respects the LATEST update.
    
    updates = [
        (200, "Actually, change my call time preference to after 2 PM."),
        (400, "On second thought, make it after 4 PM."),
        (800, "No, let's stick to calling after 1 PM essentially.")  # "essentially" is filler
    ]
    
    # 3. Inject Negations
    negations = [
        (600, "I was going to say email me, but actually don't email me on weekends.")
    ]
    
    msg_map = {t: msg for t, msg in updates + negations}
    
    for item in base_conv:
        turn = item["turn"]
        user_msg = item["user"]
        
        # Inject typo
        user_msg = introduce_typo(user_msg, probability=0.3)
        
        # Override specific turns with our conflict logic if defined
        if turn in msg_map:
            user_msg = msg_map[turn]
        
        adv_conv.append({"turn": turn, "user": user_msg})
        
        # Insert random noise turns in between (shifting turn numbers effectively in a real stream, 
        # but here we just append them to the list to simulate 'volume')
        # Note: In a real stream, turn numbers would increment. 
        # For this dataset, we are just creating a list of interactions.
        # To reuse the existing runner which expects 'turn' keys, we might need to rely on the list order 
        # or re-indexing. Let's re-index at the end.
        
        if random.random() < noise_ratio:
            adv_conv.append({
                "turn": -1, # Placeholder
                "user": random.choice(noise_phrases)
            })

    # Re-index
    for i, item in enumerate(adv_conv):
        item["turn"] = i + 1
        
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(adv_conv, f, indent=2)
    
    print(f"Generated Adversarial Dataset: {len(adv_conv)} turns (Original: {len(base_conv)})")
    print(f"Path: {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="data/synth_1200.json")
    parser.add_argument("--out", default="data/adversarial_dataset.json")
    args = parser.parse_args()
    
    # Ensure base exists
    if not os.path.exists(args.base):
        print(f"Base file {args.base} not found. generating it...")
        from generate_synth import generate
        data = generate()
        with open(args.base, "w") as f:
            json.dump(data, f)
            
    generate_adversarial(args.base, args.out)
