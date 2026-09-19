import sys
import os
sys.path.insert(0, r"c:\Users\SHRIJA SANIL\Mr.E\backend")

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import Exam, ExamSet, ExamSetQuestion, Question
from sqlalchemy import select

session = SessionLocal()
try:
    exams = session.execute(select(Exam)).scalars().all()
    print(f"Total exams in DB: {len(exams)}")
    for exam in exams:
        print(f"\n--- Exam ID: {exam.id} | Name: {exam.exam_name} | Subject: {exam.subject} ---")
        sets = session.execute(select(ExamSet).where(ExamSet.exam_id == exam.id).order_by(ExamSet.set_label)).scalars().all()
        set_q_map = {}
        for es in sets:
            q_ids = session.execute(
                select(ExamSetQuestion.question_id)
                .where(ExamSetQuestion.exam_set_id == es.id)
                .order_by(ExamSetQuestion.order_index)
            ).scalars().all()
            set_q_map[es.set_label] = list(q_ids)
            print(f"  Set {es.set_label} (ID: {es.id}): {len(q_ids)} questions")
        
        # Check if set A, B, C, D have exact same set of question IDs
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
finally:
    session.close()
