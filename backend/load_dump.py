from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app import models
from config import settings

SQLITE_URL = "sqlite:///./roshni.db"
POSTGRES_URL = settings.database_url  # your Render DB

def migrate():
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)

    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)

    sqlite_session = SQLiteSession()
    postgres_session = PostgresSession()

    print("🔄 Creating tables in PostgreSQL...")
    Base.metadata.create_all(postgres_engine)

    # ✅ IMPORTANT: order matters (parents first)
    model_order = [
        models.Feeder,
        models.House,
        models.PoolState,
        models.DailyLog,
        models.GenerationRecord,
        models.DemandRecord,
        models.Allocation,
        models.MonthlyBill,
    ]

    for model in model_order:
        records = sqlite_session.query(model).all()
        print(f"📦 Migrating {model.__name__}: {len(records)} records")

        for record in records:
            data = {
                column.name: getattr(record, column.name)
                for column in record.__table__.columns
            }

            obj = model(**data)
            postgres_session.add(obj)

        try:
            postgres_session.commit()
            print(f"✅ {model.__name__} done")
        except Exception as e:
            postgres_session.rollback()
            print(f"❌ Error in {model.__name__}: {e}")

    sqlite_session.close()
    postgres_session.close()

    print("🎉 Migration completed!")

if __name__ == "__main__":
    migrate()