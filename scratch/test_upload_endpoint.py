import urllib.request
import json
import sqlite3
import sys
import uuid
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

# Prepare multipart file upload
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = []

body.append(f"--{boundary}".encode())
body.append(b'Content-Disposition: form-data; name="subject"')
body.append(b'')
body.append(b'Biology')

body.append(f"--{boundary}".encode())
body.append(b'Content-Disposition: form-data; name="file_type"')
body.append(b'')
body.append(b'question_paper')

text_content = f"""
Chapter: Principles of Inheritance and Variation (Genetics)
Genetics is a branch of biology concerned with the study of genes, genetic variation, and heredity in organisms.
Gregor Johann Mendel is known as the father of genetics. He conducted hybridization experiments on garden peas (Pisum sativum) for 7 years (1856-1863).
Mendel selected 7 pairs of contrasting traits in pea plants (e.g. stem height: tall/dwarf, seed shape: round/wrinkled, seed color: yellow/green).
In a monohybrid cross between homozygous tall (TT) and dwarf (tt) pea plants:
- F1 generation plants are all heterozygous tall (Tt).
- F2 generation obtained by self-pollination of F1 shows a phenotypic ratio of 3 Tall : 1 Dwarf (3:1).
- The genotypic ratio of F2 is 1 TT : 2 Tt : 1 tt (1:2:1).
In a dihybrid cross involving two traits (seed shape and seed color), the phenotypic ratio in F2 generation is 9 Round Yellow : 3 Round Green : 3 Wrinkled Yellow : 1 Wrinkled Green (9:3:3:1).
Random ID: {uuid.uuid4()}
"""

body.append(f"--{boundary}".encode())
body.append(b'Content-Disposition: form-data; name="file"; filename="Genetics_Biology_Notes.txt"')
body.append(b'Content-Type: text/plain')
body.append(b'')
body.append(text_content.encode('utf-8'))
body.append(f"--{boundary}--".encode())
body.append(b'')

payload = b"\r\n".join(body)

upload_req = urllib.request.Request(
    "http://127.0.0.1:8000/api/admin/upload/single",
    data=payload,
    headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Cookie": cookie_header
    }
)

try:
    resp = urllib.request.urlopen(upload_req)
    result = json.loads(resp.read().decode('utf-8'))
    print("\n--- UPLOAD ENDPOINT RESPONSE ---")
    print(json.dumps(result, indent=2))
except Exception as e:
    print("Upload request failed:", e)
