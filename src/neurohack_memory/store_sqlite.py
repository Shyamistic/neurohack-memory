import sqlite3, os
from typing import Iterable, List, Optional
from .types import MemoryEntry, MemoryType

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
  memory_id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  source_turn INTEGER NOT NULL,
  confidence REAL NOT NULL,
  source_text TEXT,
  last_used_turn INTEGER,
  use_count INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_memories_type_key ON memories(type, key);
"""

class SQLiteMemoryStore:
    def __init__(self, path="artifacts/memory.sqlite"):
        os.makedirs("artifacts", exist_ok=True)
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def upsert_many(self, memories: Iterable[MemoryEntry]):
        cur = self.conn.cursor()
        for m in memories:
            cur.execute("""
            INSERT INTO memories(memory_id, type, key, value, source_turn, confidence, source_text, last_used_turn, use_count)
            VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(memory_id) DO UPDATE SET value=excluded.value
            """, (m.memory_id, m.type.value, m.key, m.value, m.source_turn, float(m.confidence), m.source_text, m.last_used_turn, m.use_count))
        self.conn.commit()

    def all(self):
        cur = self.conn.cursor()
        rows = cur.execute("SELECT memory_id, type, key, value, source_turn, confidence, source_text, last_used_turn, use_count FROM memories").fetchall()
        return [MemoryEntry(memory_id=r[0], type=MemoryType(r[1]), key=r[2], value=r[3], source_turn=r[4], confidence=r[5], source_text=r[6] or "", last_used_turn=r[7], use_count=r[8] or 0) for r in rows]

    def close(self):
        self.conn.close()
