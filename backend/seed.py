"""
Database Seeder Script for Project Phoenix.
Creates default Admin, Staff, Customer accounts, customer profiles, and initial service catalog.
"""
import sys
import os

# Add parent directory to path so app modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, init_db
from app.models import User, Customer, Service
from app.auth import hash_password

def seed_database():
    print("--- Initializing Database Tables ---")
    init_db()
    db = SessionLocal()

    try:
        print("--- Seeding Users ---")
        users_data = [
            {
                "email": "admin@phoenix.local",
                "password": "AdminPass123!",
                "full_name": "Phoenix Administrator",
                "role": "admin",
                "is_active": True
            },
            {
                "email": "staff@phoenix.local",
                "password": "StaffPass123!",
                "full_name": "Sarah Connor (Staff)",
                "role": "staff",
                "is_active": True
            },
            {
                "email": "customer@phoenix.local",
                "password": "CustomerPass123!",
                "full_name": "John Doe (Client)",
                "role": "customer",
                "is_active": True
            },
            {
                "email": "inactive@phoenix.local",
                "password": "InactivePass123!",
                "full_name": "Blocked Account",
                "role": "customer",
                "is_active": False
            }
        ]

        seeded_users = {}
        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                user = User(
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                    full_name=u["full_name"],
                    role=u["role"],
                    is_active=u["is_active"]
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                seeded_users[u["email"]] = user
                print(f"[+] Created user: {user.email} (Role: {user.role}, Active: {user.is_active})")
            else:
                seeded_users[u["email"]] = existing
                print(f"[*] User already exists: {existing.email}")

        print("\n--- Seeding Customer Profiles ---")
        customer_user = seeded_users.get("customer@phoenix.local")
        customers_data = [
            {
                "name": "John Doe",
                "email": "customer@phoenix.local",
                "phone": "+1-555-0199",
                "address": "123 Business Parkway, Suite 100",
                "user_id": customer_user.id if customer_user else None
            },
            {
                "name": "Acme Corporation (Dr. Jane Smith)",
                "email": "jane@acmecorp.local",
                "phone": "+1-555-0244",
                "address": "456 Enterprise Blvd",
                "user_id": None
            }
        ]

        for c in customers_data:
            existing_c = db.query(Customer).filter(Customer.email == c["email"]).first()
            if not existing_c:
                cust = Customer(**c)
                db.add(cust)
                db.commit()
                print(f"[+] Created customer profile: {cust.name} ({cust.email})")
            else:
                print(f"[*] Customer profile already exists: {existing_c.email}")

        print("\n--- Seeding Service Catalog ---")
        services_data = [
            {
                "name": "General IT & Infrastructure Consultation",
                "description": "Comprehensive IT audit, architecture review, and disaster readiness planning.",
                "price": 150.00,
                "duration_minutes": 60,
                "is_active": True
            },
            {
                "name": "Server Backup & Disaster Recovery Audit",
                "description": "Full inspection of backup mechanisms, RTO/RPO verification, and restore drills.",
                "price": 350.00,
                "duration_minutes": 120,
                "is_active": True
            },
            {
                "name": "Network & Firewall Security Hardening",
                "description": "Security group configuration, SSH key rotation, and vulnerability assessment.",
                "price": 250.00,
                "duration_minutes": 90,
                "is_active": True
            },
            {
                "name": "Emergency DevOps On-Demand Support",
                "description": "Priority emergency incident response and self-healing system recovery.",
                "price": 500.00,
                "duration_minutes": 60,
                "is_active": True
            }
        ]

        for s in services_data:
            existing_s = db.query(Service).filter(Service.name == s["name"]).first()
            if not existing_s:
                svc = Service(**s)
                db.add(svc)
                db.commit()
                print(f"[+] Created service: {svc.name} (${svc.price:.2f})")
            else:
                print(f"[*] Service already exists: {existing_s.name}")

        print("\n--- Database Seeding Completed Successfully ---")

    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding database: {e}", file=sys.stderr)
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
