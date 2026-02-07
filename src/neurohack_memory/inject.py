from typing import List
from .types import MemoryEntry

def format_injection(memories, max_tokens=320):
    if not memories:
        return ""
    lines = [f"- [{m.type.value}] {m.key}={m.value} (turn {m.source_turn}, c={m.confidence:.2f})" for m in memories]
    txt = "\n".join(lines)
    max_words = int(max_tokens * 0.75)
    words = txt.split()
    return " ".join(words[:max_words]) if len(words) > max_words else txt
