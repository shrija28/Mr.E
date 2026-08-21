import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User
from smartkcet.auth.passwords import hash_password

def main():
    session = SessionLocal()
    try:
        email = "admin@smartkcet.com"
        pwd_hash = hash_password("admin@123")
        admin = session.query(User).filter(User.email == email).first()
        if not admin:
            admin = User(
                email=email,
                display_name="Platform Admin",
                password_hash=pwd_hash,
                role="platform_admin",
            )
            session.add(admin)
            print(f"Created admin user {email}")
        else:
            admin.password_hash = pwd_hash
            admin.role = "platform_admin"
            print(f"Updated admin user {email}")
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error seeding admin: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
