#!/usr/bin/env python3
"""Generate a bcrypt hash for a test password."""

import bcrypt

password = "admin@123"  # Simple test password
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
print(f"Password: {password}")
print(f"Hash: {hashed}")
print("\nUse this in .env:")
print(f"ADMIN_PASSWORD_HASH={hashed}")
