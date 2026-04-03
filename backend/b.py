from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://roshni_user:ETv9IfWZIBuAZWB2i1jYYQ26GSsdtgAq@dpg-d77mcoh4bi0s73f0q3l0-a.oregon-postgres.render.com/roshni"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("""
        SELECT setval(
            'demand_records_id_seq',
            (SELECT MAX(id) FROM demand_records)
        );
    """))
    conn.commit()

print("✅ Sequence fixed successfully")