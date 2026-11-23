import sys
from sqlalchemy import select

from app.database import engine, SessionLocal, Base
from app.models.user import User, UserRole
from app.models.leave import LeaveType
from app.core.security import hash_password
import app.models  # Ensure all models are registered


def seed_database():
    """Seed initial founder user and standard company leave types."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        founder_email = "founder@jyohartech.com"
        founder_password = "Jyohar@2024"

        stmt = select(User).where(User.email == founder_email)
        founder = db.execute(stmt).scalar_one_or_none()

        if not founder:
            founder = User(
                email=founder_email,
                role=UserRole.founder,
                password_hash=hash_password(founder_password),
                is_active=True,
                email_verified=True,
                phone_verified=False,
            )
            db.add(founder)
            db.flush()

            db.commit()
            print(f"Founder created: {founder_email} / {founder_password}")
        else:
            print("Founder already exists")

        default_leaves = [
            ("Annual Leave", "Annual paid vacation leave", 18),
            ("Sick Leave", "Paid sick leave for illness or medical recovery", 10),
            ("Casual Leave", "Short casual leave for urgent personal matters", 6),
            ("Unpaid Leave", "Leave of absence without pay", None),
        ]
        for name, desc, days in default_leaves:
            existing_lt = db.execute(
                select(LeaveType).where(LeaveType.name == name)
            ).scalar_one_or_none()
            if not existing_lt:
                db.add(LeaveType(
                    name=name,
                    description=desc,
                    days_per_year=days,
                    is_active=True,
                ))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
