"""Clean up dummy seed data (test institutions, test students, test submissions).

Preserves:
- Platform Admin accounts
- Real user accounts (e.g. varnitha@gmail.com) and their actual exam submissions
- Standard question bank, syllabus, and subscription plans
"""

import logging
from smartkcet.db.session import SessionLocal
from smartkcet.db.models import User, Submission
from smartkcet.db.subscription_models import Institution, Subscription, UsageRecord, Invitation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup_dummy_data")

def cleanup():
    session = SessionLocal()
    try:
        # 1. Identify test users
        test_users = session.query(User).filter(User.email.like("%@smartkcet.test")).all()
        test_user_ids = [u.id for u in test_users]
        logger.info(f"Found {len(test_users)} dummy test users to clean up.")

        # 2. Delete test submissions
        if test_user_ids:
            deleted_subs = session.query(Submission).filter(Submission.user_id.in_(test_user_ids)).delete(synchronize_session=False)
            logger.info(f"Deleted {deleted_subs} dummy submissions.")

            # 3. Delete test usage records
            deleted_usage = session.query(UsageRecord).filter(UsageRecord.user_id.in_(test_user_ids)).delete(synchronize_session=False)
            logger.info(f"Deleted {deleted_usage} dummy usage records.")

            # 4. Delete test subscriptions
            deleted_subscriptions = session.query(Subscription).filter(Subscription.user_id.in_(test_user_ids)).delete(synchronize_session=False)
            logger.info(f"Deleted {deleted_subscriptions} dummy subscriptions.")

            # 5. Delete test users
            deleted_users = session.query(User).filter(User.id.in_(test_user_ids)).delete(synchronize_session=False)
            logger.info(f"Deleted {deleted_users} dummy users.")

        # 6. Delete test institutions
        test_insts = session.query(Institution).filter(
            Institution.institution_code.in_(["kcetacademy", "engcoaching", "neetplus"])
        ).all()
        test_inst_ids = [i.id for i in test_insts]
        logger.info(f"Found {len(test_insts)} dummy institutions to clean up.")

        if test_inst_ids:
            # Delete any invitations or usage records tied to these institutions
            session.query(Invitation).filter(Invitation.institution_id.in_(test_inst_ids)).delete(synchronize_session=False)
            session.query(UsageRecord).filter(UsageRecord.institution_id.in_(test_inst_ids)).delete(synchronize_session=False)
            session.query(Subscription).filter(Subscription.institution_id.in_(test_inst_ids)).delete(synchronize_session=False)
            deleted_insts = session.query(Institution).filter(Institution.id.in_(test_inst_ids)).delete(synchronize_session=False)
            logger.info(f"Deleted {deleted_insts} dummy institutions.")

        session.commit()
        logger.info("Cleanup successfully committed to database.")

        # Summary of remaining records
        remaining_users = session.query(User).all()
        remaining_subs = session.query(Submission).all()
        remaining_insts = session.query(Institution).all()

        print("\n" + "="*50)
        print("DATABASE CLEANUP COMPLETED")
        print("="*50)
        print(f"Remaining Institutions: {len(remaining_insts)}")
        for inst in remaining_insts:
            print(f" - {inst.name} ({inst.institution_code})")

        print(f"\nRemaining Users: {len(remaining_users)}")
        for u in remaining_users:
            subs_count = session.query(Submission).filter(Submission.user_id == u.id).count()
            print(f" - [{u.role}] {u.email} | {u.display_name or ''} ({subs_count} real submissions)")

        print(f"\nTotal Real Submissions Kept: {len(remaining_subs)}")
        print("="*50 + "\n")

    except Exception as e:
        session.rollback()
        logger.error(f"Error during cleanup: {e}", exc_info=True)
        raise
    finally:
        session.close()

if __name__ == "__main__":
    cleanup()
