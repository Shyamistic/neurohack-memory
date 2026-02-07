from pydantic import BaseModel, Field
from enum import Enum
from typing import Any, Dict, List, Optional

class MemoryType(str, Enum):
    preference = "preference"
    fact = "fact"
    entity = "entity"
    constraint = "constraint"
    commitment = "commitment"
    instruction = "instruction"

class MemoryEntry(BaseModel):
    memory_id: str
    type: MemoryType
    key: str
    value: str
    source_turn: int
    confidence: float = Field(ge=0.0, le=1.0)
    source_text: str = ""
    last_used_turn: Optional[int] = None
    use_count: int = 0
    meta: Dict[str, Any] = Field(default_factory=dict)

class RetrievedMemory(BaseModel):
    memory: MemoryEntry
    score: float
    ranker: str
