from app.db.database import engine, Base
from app.db import models  # ensure models are imported

def main():
    Base.metadata.create_all(bind=engine)
    print("✅ SQLite DB initialized.")

if __name__ == "__main__":
    main()