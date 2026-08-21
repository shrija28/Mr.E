"""Inspect and purge incomplete questions (e.g. 'is equal to', len < 15, blank/missing options)
and duplicate question texts from BOTH PostgreSQL (smartkcet_db) and SQLite (smartkcet.db).
"""

import json
import sqlite3
import psycopg2
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def is_incomplete_question(q_text: str, options) -> bool:
    if not q_text or not isinstance(q_text, str):
        return True
    
    q_clean = q_text.strip()
    if len(q_clean) < 15 or len(q_clean.split()) < 3:
        return True

    q_lower = q_clean.lower()
    
    # Reject incomplete fragment starters/enders
    bad_starts = [
        "is equal to", "equal to", "is given by", "value of", "the value of",
        "is:", "equals", "is ", "find the", "which of the following"
    ]
    if any(q_lower.startswith(b) for b in ["is equal to", "equal to", "is given by"]):
        return True
        
    if q_lower in ["is equal to", "equal to", "is given by", "value of", "the value of", "is:"]:
        return True

    # Validate options
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except Exception:
            return True
            
    if not isinstance(options, list) or len(options) != 4:
        return True
        
    for opt in options:
        if not opt or not isinstance(opt, str) or len(str(opt).strip()) == 0:
            return True

    # Check for duplicate options in same question
    opt_set = set(str(opt).strip().lower() for opt in options)
    if len(opt_set) < 4:
        return True

    return False

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
    c.execute("SELECT id, subject, question_text, options FROM questions")
    rows = c.fetchall()
    
    purged_ids = []
    seen_texts = set()
    dup_ids = []
    
    for row in rows:
        qid, subject, q_text, opts = row[0], row[1], row[2], row[3]
        
        # Check if incomplete
        if is_incomplete_question(q_text, opts):
            purged_ids.append((str(qid), q_text))
            continue
            
        # Check deduplication
        norm_text = (subject.lower() + "::" + q_text.strip().lower())
        if norm_text in seen_texts:
            dup_ids.append((str(qid), q_text))
        else:
            seen_texts.add(norm_text)
            
    print(f"\n[{db_name}] Total questions scanned: {len(rows)}")
    print(f"[{db_name}] Incomplete questions found: {len(purged_ids)}")
    for qid, qt in purged_ids[:10]:
        print(f"   - Invalid Q [{qid[:8]}]: {repr(qt)}")
        
    print(f"[{db_name}] Duplicate question texts found: {len(dup_ids)}")
    for qid, qt in dup_ids[:10]:
        print(f"   - Duplicate Q [{qid[:8]}]: {repr(qt[:60])}...")
        
    # Delete invalid & duplicate questions
    all_delete_ids = [q[0] for q in purged_ids] + [q[0] for q in dup_ids]
    if all_delete_ids:
        if db_name == "PostgreSQL":
            c.execute("DELETE FROM questions WHERE id::text = ANY(%s)", (all_delete_ids,))
        else:
            c.executemany("DELETE FROM questions WHERE id = ?", [(qid,) for qid in all_delete_ids])
        conn.commit()
        print(f"[{db_name}] Purged {len(all_delete_ids)} invalid/duplicate questions from DB.")

print("\n--- REMAINING CLEAN QUESTION COUNTS PER SUBJECT ---")
for db_name, conn in dbs:
    c = conn.cursor()
    c.execute("SELECT subject, COUNT(*) FROM questions GROUP BY subject")
    print(f"\n[{db_name}]:")
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]} questions")
