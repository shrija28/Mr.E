import urllib.request
import json
import sys
import uuid
from dotenv import load_dotenv

load_dotenv('backend/.env')
sys.path.insert(0, 'backend')
sys.stdout.reconfigure(encoding='utf-8')

from smartkcet.auth.tokens import issue_token

# Issue student token
token, jti, iat, exp = issue_token(
    sub="KCET0007",
    role="student",
    student_subtype="direct_subscriber"
)

cookie_header = f"smartkcet_session={token}"

target_set_id = "ea1919ec-0ec3-4968-b233-263f9c0e04f1"
print(f"[OK] Target Exam Set ID: {target_set_id}")

# Step 1: Fetch exam set questions
req_questions = urllib.request.Request(
    f"http://127.0.0.1:8000/api/student/exams/{target_set_id}",
    headers={"Cookie": cookie_header}
)
resp_q = urllib.request.urlopen(req_questions)
exam_questions_data = json.loads(resp_q.read().decode('utf-8'))

questions_list = exam_questions_data.get('questions', [])
print(f"[OK] Loaded {len(questions_list)} questions for set.")

# Build 100% correct answers dictionary + dummy question_times
answers_payload = {}
q_times_payload = {}
for idx, q in enumerate(questions_list):
    answers_payload[str(idx)] = q.get('ans')
    q_times_payload[str(idx)] = 15 + (idx * 2)  # e.g., 15s, 17s, 19s...

# Step 2: Submit paper with per-question times
submit_body = json.dumps({
    "exam_set_id": target_set_id,
    "answers": answers_payload,
    "time_taken_sec": sum(q_times_payload.values()),
    "idempotency_key": f"test-e2e-{uuid.uuid4()}",
    "question_times": q_times_payload
}).encode('utf-8')

req_submit = urllib.request.Request(
    "http://127.0.0.1:8000/api/student/submit",
    data=submit_body,
    headers={
        "Content-Type": "application/json",
        "Cookie": cookie_header
    }
)

resp_sub = urllib.request.urlopen(req_submit)
sub_result = json.loads(resp_sub.read().decode('utf-8'))

print("\n--- SUBMISSION RESPONSE ---")
sub_id = sub_result.get('id') or sub_result.get('submission_id')
print(f"Submission ID: {sub_id}")
print(f"Score Pct: {sub_result.get('score_pct') or sub_result.get('result', {}).get('percentage')}%")

# Step 3: Fetch detailed submission review
req_review = urllib.request.Request(
    f"http://127.0.0.1:8000/api/student/submissions/{sub_id}",
    headers={"Cookie": cookie_header}
)

resp_rev = urllib.request.urlopen(req_review)
rev_result = json.loads(resp_rev.read().decode('utf-8'))

print("\n--- SUBMISSION REVIEW DETAIL RESPONSE ---")
print(f"Total Questions in Review: {len(rev_result.get('questions', []))}")
print(f"Is Premium Subscriber: {rev_result.get('is_premium_subscriber')}")

first_q = rev_result.get('questions', [])[0]
print(f"First Question Time Taken: {first_q.get('time_taken_sec')}s")
print(f"First Question Correct Option: {first_q.get('correctAns')}")
print(f"First Question Status: {first_q.get('status')}")

assert rev_result.get('is_premium_subscriber') is True, "Expected is_premium_subscriber True for Pro student!"
assert first_q.get('time_taken_sec') is not None, "Expected per-question time_taken_sec!"

print("\n[SUCCESS] PREMIUM SUBMISSION REVIEW & PER-QUESTION TIME ANALYSIS VERIFIED!")
