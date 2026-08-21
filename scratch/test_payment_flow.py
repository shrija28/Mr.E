import urllib.request
import json
import sys
from dotenv import load_dotenv

load_dotenv('backend/.env')
sys.path.insert(0, 'backend')
sys.stdout.reconfigure(encoding='utf-8')

from smartkcet.auth.tokens import issue_token

# Issue student token
token, _, _, _ = issue_token(
    sub="KCET0007",
    role="student",
    student_subtype="direct_subscriber"
)

cookie_header = f"smartkcet_session={token}"

# Step 1: Fetch plans
req_plans = urllib.request.Request(
    "http://127.0.0.1:8000/api/payments/plans/student",
    headers={"Cookie": cookie_header}
)
resp_p = urllib.request.urlopen(req_plans)
plans_data = json.loads(resp_p.read().decode('utf-8'))
print(f"[OK] Available Plans: {len(plans_data.get('plans', []))}")

pro_monthly_plan = None
for p in plans_data.get('plans', []):
    if p.get('name') == 'Pro Monthly':
        pro_monthly_plan = p
        break

if not pro_monthly_plan:
    pro_monthly_plan = plans_data['plans'][0]

print(f"[OK] Testing Order Creation for Plan: {pro_monthly_plan['name']} (ID: {pro_monthly_plan['id']})")

# Step 2: Create payment order
create_order_body = json.dumps({
    "plan_id": pro_monthly_plan['id']
}).encode('utf-8')

req_create = urllib.request.Request(
    "http://127.0.0.1:8000/api/payments/create-order",
    data=create_order_body,
    headers={
        "Content-Type": "application/json",
        "Cookie": cookie_header
    }
)

resp_co = urllib.request.urlopen(req_create)
order_data = json.loads(resp_co.read().decode('utf-8'))

print("\n--- CREATE ORDER RESPONSE ---")
print(f"Order ID: {order_data.get('order_id')}")
print(f"Amount: {order_data.get('amount')}")
print(f"Currency: {order_data.get('currency')}")
print(f"Mock Flag: {order_data.get('_mock')}")

order_id = order_data.get('order_id')

# Step 3: Verify payment with dummy credentials payload
verify_body = json.dumps({
    "razorpay_order_id": order_id,
    "razorpay_payment_id": f"pay_mock_{order_id[:8]}",
    "razorpay_signature": "mock_sig",
    "plan_id": pro_monthly_plan['id']
}).encode('utf-8')

req_verify = urllib.request.Request(
    "http://127.0.0.1:8000/api/payments/verify",
    data=verify_body,
    headers={
        "Content-Type": "application/json",
        "Cookie": cookie_header
    }
)

resp_ver = urllib.request.urlopen(req_verify)
verify_data = json.loads(resp_ver.read().decode('utf-8'))

print("\n--- VERIFICATION RESPONSE ---")
print(f"Verified: {verify_data.get('verified')}")
print(f"Plan ID: {verify_data.get('plan_id')}")
print(f"Order ID: {verify_data.get('order_id')}")

assert verify_data.get('verified') is True, "Payment verification failed!"

print("\n[SUCCESS] REALISTIC DUMMY CREDENTIAL PAYMENT FLOW VERIFIED!")
