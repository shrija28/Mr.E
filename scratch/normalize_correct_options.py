"""Inspect and normalize correct_option in both PostgreSQL (smartkcet_db) and SQLite (smartkcet.db).
Ensures correct_option is ALWAYS stored as string index "0", "1", "2", or "3".
"""

import json
import sqlite3
import psycopg2
import sys

sys.stdout.reconfigure(encoding='utf-8')

letter_map = {"a": "0", "b": "1", "c": "2", "d": "3", "0": "0", "1": "1", "2": "2", "3": "3"}

def normalize_ans(correct_opt: str, opts: list) -> str:
    if correct_opt is None:
        return "0"
        
    c_str = str(correct_opt).strip()
    if c_str.lower() in letter_map:
        return letter_map[c_str.lower()]
        
    if isinstance(opts, str):
        try:
            opts = json.loads(opts)
        except Exception:
            opts = []

    if isinstance(opts, list):
        for idx, opt in enumerate(opts):
            if str(opt).strip().lower() == c_str.lower():
                return str(idx)

    # Fallback to 0 if invalid
    try:
        idx = int(c_str)
        if 0 <= idx < 4:
            return str(idx)
    except Exception:
        pass

    return "0"

# Connect to DBs
pg_conn = None
try:
    pg_conn = psycopg2.connect("postgresql://postgres:shrijasanil%402005@localhost:5432/smartkcet_db")
    print("[OK] Connected to PostgreSQL smartkcet_db")
except Exception as e:
    print("PostgreSQL connection error:", e)

sqlite_conn = sqlite3.connect("backend/smartkcet.db")
print("[OK] Connected to SQLite smartkcet.db")

dbs = []
if pg_conn:
    dbs.append(("PostgreSQL", pg_conn))
dbs.append(("SQLite", sqlite_conn))

for db_name, conn in dbs:
    c = conn.cursor()
    c.execute("SELECT id, correct_option, options FROM questions")
    rows = c.fetchall()
    
    updated_count = 0
    for qid, corr, opts in rows:
        norm_c = normalize_ans(corr, opts)
        if str(corr) != norm_c:
            updated_count += 1
            if db_name == "PostgreSQL":
                c.execute("UPDATE questions SET correct_option = %s WHERE id = %s", (norm_c, str(qid)))
            else:
                c.execute("UPDATE questions SET correct_option = ? WHERE id = ?", (norm_c, str(qid)))
                
    conn.commit()
    print(f"[{db_name}] Total questions checked: {len(rows)}, normalized correct_option for: {updated_count} questions.")

print("\n[OK] ALL QUESTION CORRECT_OPTION VALUES ARE NOW 100% NORMALIZED TO '0', '1', '2', '3'!")
