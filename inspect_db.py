
import sqlite3
conn = sqlite3.connect("artifacts/memory.sqlite")
cur = conn.cursor()
rows = cur.execute("SELECT max(source_turn) FROM memories").fetchall()
print(f"Max Turn: {rows[0][0]}")
conn.close()
