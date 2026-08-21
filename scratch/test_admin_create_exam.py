import urllib.request
import json
import sys
from dotenv import load_dotenv

load_dotenv('backend/.env')
sys.path.insert(0, 'backend')
sys.stdout.reconfigure(encoding='utf-8')

from smartkcet.auth.tokens import issue_token

# Issue admin token
token, jti, iat, exp = issue_token(
    sub="admin@gmail.com",
    role="platform_admin"
)

cookie_header = f"smartkcet_session={token}"

# Test create exam for Physics with source='question_paper'
req_body = json.dumps({
    "subject": "Physics",
    "exam_name": "KCET Physics Test Exam 2026",
    "source": "question_paper"
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
    print("\n--- CREATE EXAM RESPONSE (Physics) ---")
    print(json.dumps(result, indent=2))
except Exception as e:
    print("Create exam failed:", e)

# Test create exam for Biology
req_body_bio = json.dumps({
    "subject": "Biology",
    "exam_name": "KCET Biology Test Exam 2026"
}).encode('utf-8')

create_req_bio = urllib.request.Request(
    "http://127.0.0.1:8000/api/admin/exams",
    data=req_body_bio,
    headers={
        "Content-Type": "application/json",
        "Cookie": cookie_header
    }
)

try:
    resp = urllib.request.urlopen(create_req_bio)
    result = json.loads(resp.read().decode('utf-8'))
    print("\n--- CREATE EXAM RESPONSE (Biology) ---")
    print(json.dumps(result, indent=2))
except Exception as e:
    print("Create exam (Biology) failed:", e)
