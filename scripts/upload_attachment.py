import os
import sys
from pathlib import Path

from app.services.drive_service import drive_service, upload_or_replace
from app.services.asset_registry import upsert_drive_asset

def main():
    if len(sys.argv) < 3:
        print("Usage: python -m scripts.upload_attachment <logical_key> <path_to_file>")
        print(r"Example: python -m scripts.upload_attachment attachment/user123 C:\tmp\photo.jpg")
        raise SystemExit(1)

    logical_key = sys.argv[1]
    file_path = Path(sys.argv[2]).resolve()
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    folder_id = os.environ["MUSCLEMEMOIRS_DRIVE_FOLDER_ID"]
    svc = drive_service()

    drive_file_id = upload_or_replace(svc, folder_id, str(file_path), drive_filename=file_path.name)

    upsert_drive_asset(
        logical_key=logical_key,
        drive_file_id=drive_file_id,
        filename=file_path.name,
        notes="Attachment"
    )

    print("✅ Uploaded attachment. drive_file_id:", drive_file_id)

if __name__ == "__main__":
    main()