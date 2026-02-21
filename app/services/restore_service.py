import time
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload

from app.db.database import DB_PATH, engine
from app.services.drive_service import drive_service
from app.services.asset_registry import get_asset

def _download_file(svc, file_id: str, out_path: Path) -> None:
    request = svc.files().get_media(fileId=file_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

def _safe_rename(src: Path, dst: Path, retries: int = 10, delay_s: float = 0.3) -> None:
    last_err = None
    for _ in range(retries):
        try:
            src.rename(dst)
            return
        except PermissionError as e:
            last_err = e
            time.sleep(delay_s)
    raise last_err

def restore_db_from_logical_key(logical_key: str) -> Path:
    asset = get_asset(logical_key)
    if not asset:
        raise RuntimeError(f"No asset found for key: {logical_key}")

    # IMPORTANT: close any open DB connections from this process
    engine.dispose()

    svc = drive_service()

    temp_path = DB_PATH.with_suffix(".restore_tmp.db")
    _download_file(svc, asset.drive_file_id, temp_path)

    # Try atomic-ish swap: rename current -> backup, temp -> current
    pre_restore = DB_PATH.with_suffix(".pre_restore.db")
    if DB_PATH.exists():
        try:
            _safe_rename(DB_PATH, pre_restore)
        except PermissionError:
            # If Windows still blocks rename, tell user what to close
            raise PermissionError(
                f"Windows is still locking {DB_PATH}. "
                "Close any running app/server/DB browser using the database and try again."
            )

    _safe_rename(temp_path, DB_PATH)
    return DB_PATH