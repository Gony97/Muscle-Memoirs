from sqlalchemy import text
from app.db.database import engine

def main():
    with engine.begin() as conn:
        # Rename old table
        conn.execute(text("ALTER TABLE drive_assets RENAME TO drive_assets_old;"))

        # Recreate table with correct schema
        conn.execute(text("""
        CREATE TABLE drive_assets (
            id INTEGER PRIMARY KEY,
            logical_key VARCHAR(255) NOT NULL UNIQUE,
            drive_file_id VARCHAR(255) NOT NULL,
            filename VARCHAR(512) NOT NULL,
            mime_type VARCHAR(255),
            notes TEXT,
            created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
            updated_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL
        );
        """))

        # Copy existing data
        conn.execute(text("""
        INSERT INTO drive_assets (
            id, logical_key, drive_file_id, filename,
            mime_type, notes, created_at, updated_at
        )
        SELECT
            id, logical_key, drive_file_id, filename,
            mime_type, notes, created_at, updated_at
        FROM drive_assets_old;
        """))

        # Drop old table
        conn.execute(text("DROP TABLE drive_assets_old;"))

        # Add index (since logical_key is unique, SQLite auto-indexes it,
        # but we explicitly keep consistent naming)
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_drive_assets_logical_key ON drive_assets (logical_key);"
        ))

    print("✅ drive_assets schema migrated successfully.")

if __name__ == "__main__":
    main()