
from neurohack_memory.extractors import fallback_extract

test_cases = [
    "Call me after 9 AM",
    "Actually, prefer calls after 2 PM",
    "Please schedule calls after 11 AM",
    "Update: Only calls between 4 PM and 6 PM are allowed",
    "My preferred language is Kannada",
    "Never call on Sundays"
]

print("Testing Extraction Logic:")
for t in test_cases:
    print(f"\nInput: '{t}'")
    mems = fallback_extract(t, 1)
    if mems:
        print(f"  ✅ Extracted: {[m.key + '=' + m.value for m in mems]}")
    else:
        print(f"  ❌ FAILED")
