#!/usr/bin/env python3
"""
Create demo user for quick testing
"""

import sys
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models.user import User
from utils.security import get_password_hash

def create_demo_user():
    """Create demo user: traveler@tripsense.ai / DemoPass123!"""
    db = SessionLocal()
    try:
        # Check if demo user exists
        existing = db.query(User).filter(User.email == "traveler@tripsense.ai").first()
        if existing:
            print("✅ Demo user already exists: traveler@tripsense.ai")
            return
        
        # Create demo user
        demo_user = User(
            email="traveler@tripsense.ai",
            hashed_password=get_password_hash("DemoPass123!")
        )
        db.add(demo_user)
        db.commit()
        print("✅ Demo user created successfully!")
        print("   Email: traveler@tripsense.ai")
        print("   Password: DemoPass123!")
        
    except Exception as e:
        print(f"❌ Error creating demo user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_user()
