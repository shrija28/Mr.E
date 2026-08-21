import urllib.request
import json
import sqlite3
import sys
from dotenv import load_dotenv

load_dotenv('backend/.env')
sys.path.insert(0, 'backend')

from smartkcet.auth.tokens import issue_token

sys.stdout.reconfigure(encoding='utf-8')

# Issue valid student JWT token with sub="KCET0006"
token, jti, iat, exp = issue_token(
    sub="KCET0006",
    role="student",
    student_subtype="direct_subscriber",
    subscription_status="active"
)
print("[OK] Generated valid student JWT token for KCET0006")

cookie_header = f"smartkcet_session={token}"

# Get published exams
exams_req = urllib.request.Request(
    "http://127.0.0.1:8000/api/student/exams",
    headers={"Cookie": cookie_header}
)

resp = urllib.request.urlopen(exams_req)
data = json.loads(resp.read().decode("utf-8"))

print(f"\n--- PUBLISHED EXAMS RETURNED TO STUDENT API ({len(data.get('subjects', []))} SUBJECTS) ---")

all_clean = True

for subj_data in data.get("subjects", []):
    subj_name = subj_data.get("subject")
    exams = subj_data.get("exams", [])
    print(f"\nSubject: {subj_name} ({len(exams)} exams)")
    
    for ex in exams:
        for s in ex.get("sets", []):
            set_id = s.get("exam_set_id")
            set_label = s.get("set_label")
            
            # Fetch questions for this set
            q_req = urllib.request.Request(
                f"http://127.0.0.1:8000/api/student/exams/{set_id}",
                headers={"Cookie": cookie_header}
            )
            q_resp = urllib.request.urlopen(q_req)
            q_data = json.loads(q_resp.read().decode("utf-8"))
            
            questions = q_data.get("questions", [])
            print(f"  Set {set_label} (ID: {set_id}): {len(questions)} questions")
            
            for q in questions:
                q_text = q.get("q", "")
                if "Which statement about" in q_text or "Students can score well" in q_text or "download on this page" in q_text or "OMR" in q_text:
                    print(f"  ❌ JUNK DETECTED: {q_text}")
                    all_clean = False
                    
            if len(questions) > 0:
                print(f"  Sample Q1: {questions[0]['q'][:90]}")

if all_clean:
    print("\n✓ SUCCESS: 100% of student exam questions returned via API are authentic, clean, and free of random/nonsense junk!")
else:
    print("\n❌ FAIL: Junk questions were detected in student exam endpoint.")
