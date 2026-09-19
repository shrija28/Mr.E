import sys
import os
import random
sys.path.insert(0, r"c:\Users\SHRIJA SANIL\Mr.E\backend")

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import Exam, ExamSet, ExamSetQuestion
from sqlalchemy import select, delete

session = SessionLocal()
try:
    exams = session.execute(select(Exam)).scalars().all()
    print(f"Repairing {len(exams)} exams in PostgreSQL database...")

    updated_sets_count = 0
    for exam in exams:
        sets = session.execute(
            select(ExamSet).where(ExamSet.exam_id == exam.id).order_by(ExamSet.set_label.asc())
        ).scalars().all()
        if len(sets) <= 1:
            continue
        
        # Get Set A's question IDs in order
        set_a_id = sets[0].id
        set_a_qids = session.execute(
            select(ExamSetQuestion.question_id)
            .where(ExamSetQuestion.exam_set_id == set_a_id)
            .order_by(ExamSetQuestion.order_index.asc())
        ).scalars().all()
        
        if not set_a_qids:
            continue
        
        base_set = set(set_a_qids)
        base_list = list(set_a_qids)
        for es in sets[1:]:
            cur_qids = session.execute(
                select(ExamSetQuestion.question_id)
                .where(ExamSetQuestion.exam_set_id == es.id)
                .order_by(ExamSetQuestion.order_index.asc())
            ).scalars().all()
            
            if set(cur_qids) != base_set or list(cur_qids) == base_list:
                # Delete old mappings for this set
                session.execute(delete(ExamSetQuestion).where(ExamSetQuestion.exam_set_id == es.id))
                
                shuffled_qids = list(base_list)
                random.shuffle(shuffled_qids)
                if shuffled_qids == base_list and len(shuffled_qids) > 1:
                    shuffled_qids.reverse()
                    
                session.add_all([
                    ExamSetQuestion(exam_set_id=es.id, question_id=qid, order_index=idx)
                    for idx, qid in enumerate(shuffled_qids)
                ])
                updated_sets_count += 1
                print(f"  Fixed Exam '{exam.exam_name}' ({exam.subject}) - Set {es.set_label}: Shuffled question order sequence.")

    session.commit()
    print(f"\nPostgreSQL Migration Complete! Total exam sets updated: {updated_sets_count}")
finally:
    session.close()
