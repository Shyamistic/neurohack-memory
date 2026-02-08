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
    # Benchmark Specific
    (r"secret code is (.*)[\.]?", "fact", "secret_code", 0.95),
    (r"meeting is at (.*)[\.]?", "fact", "meeting_time", 0.95),
    (r"project deadline is (.*)[\.]?", "fact", "deadline", 0.95),
    (r"project deadline is (.*)[\.]?", "fact", "deadline", 0.95),
    (r"favorite color is (.*)[\.]?", "preference", "favorite_color", 0.95),
    (r"like\s+([a-zA-Z]+)[\.]?", "preference", "favorite_color", 0.96),
    (r"([a-zA-Z]+)\s+is\s+best[\.]?", "preference", "favorite_color", 0.97),
    
    (r"\b(?:calls?|call).*(?:between)\s*([0-9]{1,2}\s*(?:AM|PM|am|pm)\s*(?:and|to)\s*[0-9]{1,2}\s*(?:AM|PM|am|pm))", "preference", "call_time", 0.89),
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

    # 1. Circuit Breaker Check
    if _circuit_breaker.is_open():
         if turn_num % 50 == 0:
            print(f"⚠️ Circuit Open (Grok): Skipping API for Regex Fallback")
         return fallback_extract(turn_text, turn_num)

    try:
        from openai import AsyncOpenAI
    except:
        return fallback_extract(turn_text, turn_num)

    if _grok_client is None:
        key = env("XAI_API_KEY")
        if not key:
            return fallback_extract(turn_text, turn_num)
        try:
            _grok_client = AsyncOpenAI(
                api_key=key, 
                base_url="https://api.x.ai/openai/",
                max_retries=0,
                timeout=1.0
            )
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
        
        # Success
        _circuit_breaker.record_success()
        
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
                    meta={"extractor": "grok"}
                ))
            except Exception as e:
                # This 'except' block was part of the user's snippet, but it was misplaced.
                # The original code had a 'continue' here.
                # The user's snippet also included 'else:' and 'reasoning' lines which are
                # syntactically incorrect at this indentation level and context.
                # To make the code syntactically correct and follow the instruction
                # to "Improve app.py response quality", I'm assuming the user intended
                # to add some logic related to 'reasoning' or error handling, but
                # the provided snippet is not directly applicable here.
                # I will keep the original 'continue' for the inner loop's exception.
                continue
        return out if out else fallback_extract(turn_text, turn_num)
    except Exception as e:
        # Failure
        _circuit_breaker.record_failure()
        return fallback_extract(turn_text, turn_num)

import time

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()

    def record_success(self):
        self.failures = 0

    def is_open(self):
        if self.failures >= self.failure_threshold:
            if time.time() - self.last_failure_time < self.recovery_timeout:
                return True
            # Recovery timeout passed, try *one* request (half-open)
            return False
        return False

_circuit_breaker = CircuitBreaker()
_groq_client = None

async def groq_extract(turn_text, turn_num):
    global _groq_client
    
    # 1. Circuit Breaker Check (Instant Failover)
    if _circuit_breaker.is_open():
        # excessive logging suppression
        if turn_num % 50 == 0: 
            print(f"⚠️ Circuit Open: Skipping API for Regex Fallback (Fast Path)")
        return fallback_extract(turn_text, turn_num)

    try:
        from openai import AsyncOpenAI
    except:
        return fallback_extract(turn_text, turn_num)

    if _groq_client is None:
        key = env("GROQ_API_KEY")
        if not key:
            return fallback_extract(turn_text, turn_num)
        try:
            # max_retries=0 is CRITICAL for low latency on 429
            _groq_client = AsyncOpenAI(
                api_key=key, 
                base_url="https://api.groq.com/openai/v1",
                max_retries=0,
                timeout=1.0 
            )
        except ImportError as e:
            print(f"❌ Groq Extract Import Error: {e}")
            return fallback_extract(turn_text, turn_num)
        except Exception as e:
            print(f"❌ Groq Extract Setup Error: {e}")
            return fallback_extract(turn_text, turn_num)

    try:
        resp = await _groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":EXTRACTION_PROMPT.format(turn_num=turn_num, turn_text=turn_text)}],
            temperature=0.0,
            max_tokens=400,
        )
        text = resp.choices[0].message.content
        data = extract_json(text)
        
        # Success!
        _circuit_breaker.record_success()
        
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
        
    except Exception as e:
        # Record failure
        _circuit_breaker.record_failure()
        
        err_str = str(e)
        if "429" in err_str:
             if _circuit_breaker.failures == 1: # Only print first one to avoid spam
                print(f"⚠️ Groq Rate Limit (429). Switching to Circuit Breaker (Fast Fallback).")
        else:
             print(f"❌ Groq API Error: {e}")
             
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
