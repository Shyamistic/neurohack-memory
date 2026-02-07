import os, time, yaml, math, re
from dataclasses import dataclass
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def env(key, default=""):
    return os.getenv(key, default)

@dataclass
class Timer:
    t0: float
    @classmethod
    def start(cls):
        return cls(time.perf_counter())
    def ms(self):
        return (time.perf_counter() - self.t0) * 1000.0

def exp_decay(age_turns, lam):
    return math.exp(-lam * max(age_turns, 0))

def extract_json(text):
    import json
    text = text.strip()
    try:
        return json.loads(text)
    except:
        pass
    text = re.sub(r"```.*?\n", "", text, flags=re.DOTALL)
    text = re.sub(r"```", "", text)
    try:
        return json.loads(text)
    except:
        pass
    match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    return None
