from typing import List
import json, re, uuid, os
from .types import MemoryEntry, MemoryType
from .utils import env, extract_json

PATTERNS = [
    (r"\b(?:preferred language|language)\s*(?:is|:)\s*(?:[A-Za-z]+)\s*([A-Za-z]+)", "preference", "language", 0.92),
    (r"\b(?:language)\s*(?:is|:)\s*([A-Za-z]+)", "preference", "language", 0.92),
    # Handles "Call [me/us/...] after 9 AM"
    (r"\b(?:calls?|call)\s*(?:me|us|him|her)?\s*(?:after|before|at)\s*([0-9]{1,2}\s*(?:AM|PM|am|pm))", "preference", "call_time", 0.86),
    # Handles "between X and Y"
    (r"\b(?:calls?|call).*(?:between)\s*([0-9]{1,2}\s*(?:AM|PM|am|pm)\s*(?:and|to)\s*[0-9]{1,2}\s*(?:AM|PM|am|pm))", "preference", "call_time", 0.89),
    # Generic catch-all for "after X" if "call" appeared earlier
    (r"call.*(?:after|before|at)\s*([0-9]{1,2}\s*(?:AM|PM|am|pm))", "preference", "call_time", 0.80),
    (r"\b(?:no(?:thing)?|never|do not)\s*(?:call)?\s*on\s*sundays?", "constraint", "no_sundays", 0.88),
]

def fallback_extract(turn_text, turn_num):
    mems = []
    t = turn_text.strip().lower()
    for pattern, mtype, key, conf in PATTERNS:
        match = re.search(pattern, t, re.I)
        if match:
            value = match.group(1) if match.groups() else "true"
            mems.append(MemoryEntry(
                memory_id=str(uuid.uuid4()),
                type=MemoryType(mtype),
                key=key,
                value=value,
                source_turn=turn_num,
                confidence=conf,
                source_text=turn_text[:240],
                meta={"extractor": "fallback"}
            ))
    return mems

EXTRACTION_PROMPT = """You are extracting durable memories. Return ONLY JSON array. Turn {turn_num}: {turn_text}
Schema: [{{"type":"preference|fact|constraint|commitment","key":"name","value":"val","confidence":0.7}}]
Extract only if confidence >= 0.70."""

_grok_client = None

async def grok_extract(turn_text, turn_num):
    global _grok_client
    try:
        from openai import AsyncOpenAI
    except:
        return fallback_extract(turn_text, turn_num)

    if _grok_client is None:
        key = env("XAI_API_KEY")
        if not key:
            return fallback_extract(turn_text, turn_num)
        try:
            _grok_client = AsyncOpenAI(api_key=key, base_url="https://api.x.ai/openai/")
        except:
            return fallback_extract(turn_text, turn_num)

    try:
        resp = await _grok_client.chat.completions.create(
            model="grok-2",
            messages=[{"role":"user","content":EXTRACTION_PROMPT.format(turn_num=turn_num, turn_text=turn_text)}],
            temperature=0.0,
            max_tokens=400,
        )
        text = resp.choices[0].message.content
        data = extract_json(text)
        if not data:
            return fallback_extract(turn_text, turn_num)
        arr = data if isinstance(data, list) else [data]
        out = []
        for it in arr:
            try:
                conf = float(it.get("confidence", 0))
                if conf < 0.70:
                    continue
                out.append(MemoryEntry(
                    memory_id=str(uuid.uuid4()),
                    type=MemoryType(it["type"]),
                    key=str(it["key"]),
                    value=str(it["value"]),
                    source_turn=turn_num,
                    confidence=conf,
                    source_text=turn_text[:240],
                    meta={"extractor":"grok"}
                ))
            except:
                continue
        return out if out else fallback_extract(turn_text, turn_num)
    except:
        return fallback_extract(turn_text, turn_num)

_groq_client = None

async def groq_extract(turn_text, turn_num):
    global _groq_client
    try:
        from openai import AsyncOpenAI
    except:
        return fallback_extract(turn_text, turn_num)

    if _groq_client is None:
        key = env("GROQ_API_KEY")
        if not key:
            return fallback_extract(turn_text, turn_num)
        try:
            _groq_client = AsyncOpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
        except:
            return fallback_extract(turn_text, turn_num)

    try:
        resp = await _groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role":"user","content":EXTRACTION_PROMPT.format(turn_num=turn_num, turn_text=turn_text)}],
            temperature=0.0,
            max_tokens=400,
        )
        text = resp.choices[0].message.content
        data = extract_json(text)
        if not data:
            return fallback_extract(turn_text, turn_num)
        arr = data if isinstance(data, list) else [data]
        out = []
        for it in arr:
            try:
                conf = float(it.get("confidence", 0))
                if conf < 0.70:
                    continue
                out.append(MemoryEntry(
                    memory_id=str(uuid.uuid4()),
                    type=MemoryType(it["type"]),
                    key=str(it["key"]),
                    value=str(it["value"]),
                    source_turn=turn_num,
                    confidence=conf,
                    source_text=turn_text[:240],
                    meta={"extractor":"groq"}
                ))
            except:
                continue
        return out if out else fallback_extract(turn_text, turn_num)
    except:
        return fallback_extract(turn_text, turn_num)

CACHE_FILE = "artifacts/extraction_cache.json"
_EXT_CACHE = {}

def load_cache():
    global _EXT_CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                _EXT_CACHE = json.load(f)
        except:
            _EXT_CACHE = {}

def save_cache():
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(_EXT_CACHE, f)
    except:
        pass

load_cache()

async def extract(turn_text, turn_num, provider="grok"):
    # Check cache first
    cache_key = f"{turn_num}:{turn_text}"
    if cache_key in _EXT_CACHE:
        # Reconstruct MemoryEntry objects from cached data
        data = _EXT_CACHE[cache_key]
        return [MemoryEntry(
            memory_id=str(uuid.uuid4()), # New ID to avoid conflicts
            type=MemoryType(d["type"]),
            key=d["key"],
            value=d["value"],
            source_turn=d["source_turn"],
            confidence=d["confidence"],
            source_text=d["source_text"],
            meta=d.get("meta", {})
        ) for d in data]

    provider = env("EXTRACTOR_PROVIDER", provider).lower().strip()
    if provider == "grok":
        res = await grok_extract(turn_text, turn_num)
    elif provider == "groq":
        res = await groq_extract(turn_text, turn_num)
    else:
        res = fallback_extract(turn_text, turn_num)
    
    # Cache the result (serialize MemoryEntry objects)
    serialized = [{
        "type": m.type.value,
        "key": m.key,
        "value": m.value,
        "source_turn": m.source_turn,
        "confidence": m.confidence,
        "source_text": m.source_text,
        "meta": m.meta
    } for m in res]
    
    _EXT_CACHE[cache_key] = serialized
    if turn_num % 10 == 0: # Save periodically
        save_cache()
    
    return res
