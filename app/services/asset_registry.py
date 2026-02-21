from app.db.database import SessionLocal
from app.db.models import DriveAsset

def upsert_drive_asset(
    logical_key: str,
    drive_file_id: str,
    filename: str,
    mime_type: str | None = None,
    notes: str | None = None,
) -> DriveAsset:
    db = SessionLocal()
    try:
        asset = db.query(DriveAsset).filter(DriveAsset.logical_key == logical_key).first()
        if asset:
            asset.drive_file_id = drive_file_id
            asset.filename = filename
            asset.mime_type = mime_type
            asset.notes = notes
        else:
            asset = DriveAsset(
                logical_key=logical_key,
                drive_file_id=drive_file_id,
                filename=filename,
                mime_type=mime_type,
                notes=notes,
            )
            db.add(asset)

        db.commit()
        db.refresh(asset)
        return asset
    finally:
        db.close()

def get_asset(logical_key: str) -> DriveAsset | None:
    db = SessionLocal()
    try:
        return db.query(DriveAsset).filter(DriveAsset.logical_key == logical_key).first()
    finally:
        db.close()

def delete_asset(logical_key: str) -> None:
    db = SessionLocal()
    try:
        asset = db.query(DriveAsset).filter(DriveAsset.logical_key == logical_key).first()
        if asset:
            db.delete(asset)
            db.commit()
    finally:
        db.close()