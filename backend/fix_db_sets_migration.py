import sqlite3
import random
import os

db_path = r"c:\Users\SHRIJA SANIL\Mr.E\backend\smartkcet.db"
if not os.path.exists(db_path):
    print("Database file not found at", db_path)
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, exam_name, subject FROM exams;")
exams = cursor.fetchall()
print(f"Repairing {len(exams)} exams in database...")

updated_sets_count = 0
for e_id, name, subj in exams:
    cursor.execute("SELECT id, set_label FROM exam_sets WHERE exam_id = ? ORDER BY set_label;", (e_id,))
    sets = cursor.fetchall()
    if len(sets) <= 1:
        continue
    
    # Get Set A's question IDs in order
    set_a_id = sets[0][0]
    cursor.execute("SELECT question_id FROM exam_set_questions WHERE exam_set_id = ? ORDER BY order_index;", (set_a_id,))
    set_a_qids = [row[0] for row in cursor.fetchall()]
    
    if not set_a_qids:
        continue
    
    for s_id, s_lbl in sets[1:]:
        cursor.execute("SELECT question_id FROM exam_set_questions WHERE exam_set_id = ? ORDER BY order_index;", (s_id,))
        cur_qids = [row[0] for row in cursor.fetchall()]
        
        if set(cur_qids) != set(set_a_qids):
            # Delete old mappings for this set
            cursor.execute("DELETE FROM exam_set_questions WHERE exam_set_id = ?;", (s_id,))
            
            # Shuffle Set A's question IDs for this set
            shuffled_qids = list(set_a_qids)
            random.shuffle(shuffled_qids)
            if shuffled_qids == set_a_qids and len(shuffled_qids) > 1:
                shuffled_qids.reverse()
                
            for idx, qid in enumerate(shuffled_qids):
                cursor.execute(
                    "INSERT INTO exam_set_questions (exam_set_id, question_id, order_index) VALUES (?, ?, ?);",
                    (s_id, qid, idx)
                )
            updated_sets_count += 1
            print(f"  Fixed Exam '{name}' ({subj}) - Set {s_lbl}: Updated to Set A's {len(shuffled_qids)} questions in shuffled order.")

conn.commit()
conn.close()
print(f"\nMigration Complete! Total exam sets updated: {updated_sets_count}")
