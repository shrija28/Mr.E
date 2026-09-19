import sqlite3
import os

db_path = r"c:\Users\SHRIJA SANIL\Mr.E\backend\smartkcet.db"
if not os.path.exists(db_path):
    print("smartkcet.db not found at", db_path)
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, exam_name, subject FROM exams;")
    exams = cursor.fetchall()
    print(f"Total exams in SQLite DB: {len(exams)}")
    for e_id, name, subj in exams:
        print(f"\n--- Exam ID: {e_id} | Name: {name} | Subject: {subj} ---")
        cursor.execute("SELECT id, set_label FROM exam_sets WHERE exam_id = ? ORDER BY set_label;", (e_id,))
        sets = cursor.fetchall()
        set_q_map = {}
        for s_id, s_lbl in sets:
            cursor.execute("SELECT question_id FROM exam_set_questions WHERE exam_set_id = ? ORDER BY order_index;", (s_id,))
            q_ids = [row[0] for row in cursor.fetchall()]
            set_q_map[s_lbl] = q_ids
            print(f"  Set {s_lbl} (ID: {s_id}): {len(q_ids)} questions")
        
        if len(sets) > 1:
            labels = list(set_q_map.keys())
            set_a_ids = set(set_q_map[labels[0]])
            for lbl in labels[1:]:
                other_ids = set(set_q_map[lbl])
                is_same_set = (set_a_ids == other_ids)
                print(f"  Set {labels[0]} vs Set {lbl}: Same question IDs? {is_same_set}")
                if not is_same_set:
                    print(f"    Set {labels[0]} count: {len(set_a_ids)}, Set {lbl} count: {len(other_ids)}")
                    print(f"    In A but not {lbl}: {len(set_a_ids - other_ids)}")

    conn.close()
