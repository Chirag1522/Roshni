import json
from app import models
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

engine = create_engine("sqlite:///./roshni.db")
Session = sessionmaker(bind=engine)
session = Session()

data = {}

for model in [models.User, models.House]:
    records = session.query(model).all()
    data[model.__name__] = [
        {c.name: getattr(r, c.name) for c in r.__table__.columns}
        for r in records
    ]

with open("data.json", "w") as f:
    json.dump(data, f, indent=2)