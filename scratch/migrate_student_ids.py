import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User

def main():
    session = SessionLocal()
    try:
        users = session.query(User).all()
        updated = 0
        for u in users:
            if u.kcet_student_id:
                old_id = u.kcet_student_id
                if old_id.startswith("KCET") or old_id.startswith("ID"):
                    num_part = old_id.replace("KCET", "").replace("ID", "")
                    new_id = f"MrE{num_part}"
                    u.kcet_student_id = new_id
                    print(f"Updated {u.email}: {old_id} -> {new_id}")
                    updated += 1
        session.commit()
        print(f"Successfully updated {updated} student IDs in database!")
    except Exception as e:
        session.rollback()
        print(f"Error updating database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
