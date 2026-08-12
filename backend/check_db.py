import os
import sys
import sqlite3

# find db
db_path = "c:\\Users\\SHRIJA SANIL\\SmartKCET-Prep\\backend\\database.db"

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT id, name, subscription_status FROM institutions")
print("Institutions:", cur.fetchall())

cur.execute("SELECT id, institution_id, status FROM subscriptions")
print("Subscriptions:", cur.fetchall())

conn.close()
