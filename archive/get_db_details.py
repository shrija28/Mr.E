#!/usr/bin/env python
"""Query database for all institutions and students details."""

from sqlalchemy.orm import sessionmaker
from smartkcet.db.models import User
from smartkcet.db.subscription_models import Institution, Subscription, SubscriptionPlan
from smartkcet.db.session import engine

# Create session
Session = sessionmaker(bind=engine)
session = Session()

print("\n" + "="*120)
print("INSTITUTION DETAILS")
print("="*120)

institutions = session.query(Institution).all()
print(f"\nTotal Institutions: {len(institutions)}\n")

for idx, inst in enumerate(institutions, 1):
    print(f"\n{'='*120}")
    print(f"Institution {idx}:")
    print(f"  ID: {inst.id}")
    print(f"  Name: {inst.name}")
    print(f"  Code: {inst.institution_code}")
    print(f"  Phone: {inst.contact_phone}")
    print(f"  Status: {inst.subscription_status}")
    print(f"  Registered: {inst.registered_at}")
    
    # Get subscription for this institution
    subs = session.query(Subscription).filter(
        Subscription.institution_id == inst.id
    ).first()
    
    if subs:
        plan = session.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == subs.plan_id
        ).first()
        print(f"  Subscription Status: {subs.status}")
        print(f"  Plan: {plan.name if plan else 'N/A'}")
        print(f"  Start Date: {subs.start_date}")
        print(f"  Renewal Date: {subs.next_renewal_date}")
    else:
        print(f"  Subscription: None")
    
    # Get students for this institution
    students = session.query(User).filter(
        User.institution_id == inst.id
    ).all()
    print(f"  Students: {len(students)}")
    for student in students:
        print(f"    - {student.display_name} ({student.kcet_student_id}) | {student.email}")

print(f"\n\n{'='*120}")
print("STUDENT DETAILS")
print("="*120)

students = session.query(User).filter(User.role == 'student').all()
print(f"\nTotal Students: {len(students)}\n")

direct_subscribers = []
institution_students = []

for student in students:
    if student.institution_id:
        institution_students.append(student)
    else:
        direct_subscribers.append(student)

# Direct Subscribers
print(f"\n{'='*120}")
print(f"DIRECT SUBSCRIBERS ({len(direct_subscribers)} total)")
print(f"{'='*120}\n")

for idx, student in enumerate(direct_subscribers, 1):
    print(f"{idx}. Name: {student.display_name}")
    print(f"   KCET ID: {student.kcet_student_id}")
    print(f"   Email: {student.email}")
    print(f"   Phone: {student.phone if hasattr(student, 'phone') else 'N/A'}")
    print(f"   Type: Direct Subscriber")
    
    # Get subscription
    subs = session.query(Subscription).filter(
        Subscription.user_id == student.id
    ).first()
    if subs:
        plan = session.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == subs.plan_id
        ).first()
        print(f"   Subscription Status: {subs.status}")
        print(f"   Plan: {plan.name if plan else 'N/A'}")
        print(f"   Renewal: {subs.next_renewal_date}")
    else:
        print(f"   Subscription: None")
    
    print()

# Institution Students
print(f"\n{'='*120}")
print(f"INSTITUTION-LINKED STUDENTS ({len(institution_students)} total)")
print(f"{'='*120}\n")

for idx, student in enumerate(institution_students, 1):
    inst = session.query(Institution).filter(
        Institution.id == student.institution_id
    ).first()
    
    print(f"{idx}. Name: {student.display_name}")
    print(f"   KCET ID: {student.kcet_student_id}")
    print(f"   Email: {student.email}")
    print(f"   Phone: {student.phone if hasattr(student, 'phone') else 'N/A'}")
    print(f"   Institution: {inst.name if inst else 'Unknown'}")
    print(f"   Institution Code: {inst.institution_code if inst else 'N/A'}")
    print(f"   Type: Institution-linked")
    
    # Get subscription
    subs = session.query(Subscription).filter(
        Subscription.user_id == student.id
    ).first()
    if subs:
        plan = session.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == subs.plan_id
        ).first()
        print(f"   Subscription Status: {subs.status}")
        print(f"   Plan: {plan.name if plan else 'N/A'}")
        print(f"   Renewal: {subs.next_renewal_date}")
    else:
        print(f"   Subscription: None")
    
    print()

print(f"\n{'='*120}")
print("SUMMARY")
print(f"{'='*120}")
print(f"Total Institutions: {len(institutions)}")
print(f"Total Students: {len(students)}")
print(f"  - Direct Subscribers: {len(direct_subscribers)}")
print(f"  - Institution-linked: {len(institution_students)}")
print(f"{'='*120}\n")

session.close()
