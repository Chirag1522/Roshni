from sqlalchemy import create_engine, text
from config import settings

def reset_schema():
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        print("⚠️ Dropping and recreating schema...")

        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))

        conn.commit()

    print("✅ Schema reset complete!")

if __name__ == "__main__":
    reset_schema()