from app.db.database import engine, Base
from app.db import models  # noqa

def main():
    Base.metadata.create_all(bind=engine)
    print("✅ SQLite initialized at data/musclememoirs.db")

if __name__ == "__main__":
    main()