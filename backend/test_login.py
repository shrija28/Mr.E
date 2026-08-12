import sqlite3
from smartkcet.auth.passwords import verify_password
import os
import sys

print(f"CWD: {os.getcwd()}")
print(f"sys.path: {sys.path}")

conn = sqlite3.connect('smartkcet.db')
cursor = conn.cursor()
cursor.execute("SELECT password_hash FROM users WHERE email = 'admin@smartkcet.com'")
row = cursor.fetchone()
if not row:
    print("User not found!")
    sys.exit(1)

stored_hash = row[0]
print(f"Stored Hash: {stored_hash}")

is_valid = verify_password('admin@123', stored_hash)
print(f"Password valid? {is_valid}")

conn.close()
