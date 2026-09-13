"""Apply schema changes for Institution Batches and Exam Scheduling."""

import sqlite3
import os
from pathlib import Path

db_path = Path(__file__).resolve().parent / "smartkcet.db"
print(f"Applying schema changes to {db_path}...")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 1. Create institution_batches table
cursor.execute("""
CREATE TABLE IF NOT EXISTS institution_batches (
    id VARCHAR(36) PRIMARY KEY,
    institution_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (institution_id) REFERENCES institutions (id) ON DELETE CASCADE
);
""")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_institution_batches_inst ON institution_batches(institution_id);")

# 2. Add batch_id to users if not exists
cursor.execute("PRAGMA table_info(users);")
user_cols = [row[1] for row in cursor.fetchall()]
if "batch_id" not in user_cols:
    print("Adding batch_id column to users table...")
    cursor.execute("ALTER TABLE users ADD COLUMN batch_id VARCHAR(36) REFERENCES institution_batches(id) ON DELETE SET NULL;")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_batch_id ON users(batch_id);")

# 3. Add batch_id, duration_minutes, scheduled_start, scheduled_end, total_marks to exams
cursor.execute("PRAGMA table_info(exams);")
exam_cols = [row[1] for row in cursor.fetchall()]

if "batch_id" not in exam_cols:
    print("Adding batch_id column to exams table...")
    cursor.execute("ALTER TABLE exams ADD COLUMN batch_id VARCHAR(36) REFERENCES institution_batches(id) ON DELETE SET NULL;")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exams_batch_id ON exams(batch_id);")

if "duration_minutes" not in exam_cols:
    print("Adding duration_minutes column to exams table...")
    cursor.execute("ALTER TABLE exams ADD COLUMN duration_minutes INTEGER DEFAULT 60;")

if "scheduled_start" not in exam_cols:
    print("Adding scheduled_start column to exams table...")
    cursor.execute("ALTER TABLE exams ADD COLUMN scheduled_start TIMESTAMP;")

if "scheduled_end" not in exam_cols:
    print("Adding scheduled_end column to exams table...")
    cursor.execute("ALTER TABLE exams ADD COLUMN scheduled_end TIMESTAMP;")

if "total_marks" not in exam_cols:
    print("Adding total_marks column to exams table...")
    cursor.execute("ALTER TABLE exams ADD COLUMN total_marks INTEGER DEFAULT 60;")

# 4. Add batch_id to invitations if not exists
cursor.execute("PRAGMA table_info(invitations);")
inv_cols = [row[1] for row in cursor.fetchall()]
if "batch_id" not in inv_cols:
    print("Adding batch_id column to invitations table...")
    cursor.execute("ALTER TABLE invitations ADD COLUMN batch_id VARCHAR(36) REFERENCES institution_batches(id) ON DELETE SET NULL;")

conn.commit()
conn.close()
print("Successfully applied batch schema migrations!")
