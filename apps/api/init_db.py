"""
Initialize database with Alembic migrations.

Run this after starting the database to create all tables.
"""

import subprocess
import sys
from config import settings

def init_database():
    """Initialize database with Alembic migrations."""
    print("="*60)
    print("TripSense AI - Database Initialization")
    print("="*60)
    print(f"\nDatabase URL: {settings.database_url[:50]}...")
    
    try:
        print("\n📦 Running Alembic migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        
        print("✅ Database initialized successfully!")
        print("\n" + "="*60)
        
        # Show current database version
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True
        )
        print("\nCurrent migration:")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running migrations: {e}")
        print(f"Output: {e.output}")
        print(f"Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
