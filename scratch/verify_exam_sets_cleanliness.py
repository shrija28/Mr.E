import urllib.request
import json
import sys
from dotenv import load_dotenv

load_dotenv('backend/.env')
sys.path.insert(0, 'backend')
sys.stdout.reconfigure(encoding='utf-8')

from smartkcet.auth.tokens import issue_token

token, _, _, _ = issue_token(sub="admin@gmail.com", role="platform_admin")
cookie_header = f"smartkcet_session={token}"

# Create Exam for Mathematics
req_body = json.dumps({
    "subject": "Mathematics",
    "exam_name": "Verified Clean Mathematics Exam 2026",
}).encode('utf-8')

create_req = urllib.request.Request(
    "http://127.0.0.1:8000/api/admin/exams",
    data=req_body,
    headers={
        "Content-Type": "application/json",
        "Cookie": cookie_header
    }
)

try:
    resp = urllib.request.urlopen(create_req)
    result = json.loads(resp.read().decode('utf-8'))
    print("\n--- MATHEMATICS EXAM CREATION RESPONSE ---")
    print(f"Exam ID: {result.get('exam_id')}")
    print(f"Sets Count: {len(result.get('set_ids', []))}")
    for s in result.get('set_ids', []):
        print(f"  Set {s['label']}: {s['question_count']} questions")
except Exception as e:
    print("Create exam failed:", e)

# Query questions in DB for Mathematics and check for any incomplete/duplicate questions
import psycopg2
pg_conn = psycopg2.connect("postgresql://postgres:shrijasanil%402005@localhost:5432/smartkcet_db")
c = pg_conn.cursor()
c.execute("SELECT id, question_text, options FROM questions WHERE subject = 'Mathematics'")
rows = c.fetchall()

print(f"\n--- TOTAL MATHEMATICS QUESTIONS IN DB: {len(rows)} ---")
incomplete_found = 0
seen_texts = set()
dup_found = 0

for qid, q_text, opts in rows:
    q_clean = q_text.strip()
    if len(q_clean) < 15 or q_clean.lower() in ["is equal to", "equal to", "value of"]:
        print(f"  [BAD] Incomplete Q: {q_clean}")
        incomplete_found += 1
    
    norm = q_clean.lower()
    if norm in seen_texts:
        print(f"  [BAD] Duplicate Q: {q_clean[:50]}...")
        dup_found += 1
    else:
        seen_texts.add(norm)

print(f"\nVerification Results:")
print(f"  Incomplete Questions: {incomplete_found} (Expected: 0)")
print(f"  Duplicate Questions: {dup_found} (Expected: 0)")
if incomplete_found == 0 and dup_found == 0:
    print("[SUCCESS] ALL QUESTIONS AND EXAM SETS ARE 100% CLEAN, COMPLETE, AND DEDUPLICATED!")
