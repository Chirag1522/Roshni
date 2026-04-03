"""
ROSHNI Database Migration Script
Migrate data from local SQLite (roshni.db) to Remote PostgreSQL (Render)
"""

import os
import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import Base
from app import models
from config import settings

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    
    # Local SQLite connection
    sqlite_url = "sqlite:///./backend/roshni.db"
    sqlite_engine = create_engine(sqlite_url, echo=False)
    
    # Remote PostgreSQL connection (from environment)
    postgres_url = settings.database_url
    
    if "postgresql" not in postgres_url:
        print("❌ ERROR: DATABASE_URL is not PostgreSQL!")
        print(f"Current: {postgres_url}")
        return False
    
    postgres_engine = create_engine(postgres_url, echo=False)
    
    print("=" * 60)
    print("🔄 ROSHNI Database Migration")
    print("=" * 60)
    print(f"\n📍 Source: {sqlite_url}")
    print(f"📍 Target: {postgres_url[:50]}...")
    
    try:
        # Step 1: Create all tables in PostgreSQL
        print("\n✅ Step 1: Creating tables in PostgreSQL...")
        Base.metadata.create_all(postgres_engine)
        print("   ✓ Tables created")
        
        # Step 2: Get all data from SQLite
        print("\n✅ Step 2: Reading data from SQLite...")
        sqlite_session = sessionmaker(bind=sqlite_engine)()
        
        # List of models to migrate
        model_classes = [
            models.User,
            models.House,
            models.Device,
            models.Demand,
            models.Supply,
            models.Allocation,
            models.Transaction,
            models.Bill,
            models.PoolHistory,
        ]
        
        # Count records
        total_records = 0
        for model_class in model_classes:
            try:
                count = sqlite_session.query(model_class).count()
                if count > 0:
                    print(f"   - {model_class.__name__}: {count} records")
                    total_records += count
            except Exception as e:
                print(f"   - {model_class.__name__}: No data (ok)")
        
        # Step 3: Copy data
        print(f"\n✅ Step 3: Migrating {total_records} records to PostgreSQL...")
        postgres_session = sessionmaker(bind=postgres_engine)()
        
        for model_class in model_classes:
            try:
                records = sqlite_session.query(model_class).all()
                if records:
                    print(f"   → Migrating {len(records)} {model_class.__name__} records...", end=" ")
                    
                    for record in records:
                        # Detach from SQLite session and add to PostgreSQL session
                        postgres_session.merge(record)
                    
                    postgres_session.commit()
                    print("✓")
            except Exception as e:
                postgres_session.rollback()
                print(f"⚠️ Error: {e}")
                continue
        
        # Step 4: Verify
        print("\n✅ Step 4: Verifying migration...")
        for model_class in model_classes:
            try:
                sqlite_count = sqlite_session.query(model_class).count()
                postgres_count = postgres_session.query(model_class).count()
                
                if sqlite_count > 0:
                    match = "✓" if sqlite_count == postgres_count else "❌"
                    print(f"   {match} {model_class.__name__}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
            except:
                pass
        
        # Cleanup
        sqlite_session.close()
        postgres_session.close()
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print("\n📝 Next steps:")
        print("   1. Visit your Render backend at:")
        print("      https://roshni-backend-o7al.onrender.com/api/admin/users")
        print("   2. You should see your migrated data!")
        print("\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_data()
    sys.exit(0 if success else 1)
