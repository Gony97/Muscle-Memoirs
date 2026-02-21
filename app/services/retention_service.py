from datetime import datetime
from app.db.database import SessionLocal
from app.db.models import DriveAsset
from app.services.drive_service import drive_service

def _parse_backup_ts(logical_key: str) -> datetime | None:
    # logical_key = "backup/YYYYMMDD_HHMMSS"
    try:
        ts = logical_key.split("/", 1)[1]
        return datetime.strptime(ts, "%Y%m%d_%H%M%S")
    except Exception:
        return None

def apply_retention(
    keep_daily: int = 30,
    keep_weekly: int = 26,
    keep_monthly: int = 12,
    dry_run: bool = True,
) -> list[str]:
    """
    Keeps:
      - last `keep_daily` daily backups
      - last `keep_weekly` weekly backups
      - last `keep_monthly` monthly backups
    Deletes older backups beyond these sets.
    Never touches 'backup/latest'.
    """
    db = SessionLocal()
    try:
        rows = (
            db.query(DriveAsset)
            .filter(DriveAsset.logical_key.like("backup/%"))
            .filter(DriveAsset.logical_key != "backup/latest")
            .all()
        )

        items = []
        for r in rows:
            dt = _parse_backup_ts(r.logical_key)
            if dt:
                items.append((dt, r.logical_key, r.drive_file_id))

        items.sort(key=lambda x: x[0], reverse=True)
        if not items:
            return []

        # Build keep sets by day/week/month buckets
        kept = set()

        # daily buckets
        day_buckets = {}
        for dt, key, _ in items:
            d = dt.date()
            day_buckets.setdefault(d, []).append((dt, key))
        for d in sorted(day_buckets.keys(), reverse=True)[:keep_daily]:
            # keep newest backup for that day
            kept.add(sorted(day_buckets[d], reverse=True)[0][1])

        # weekly buckets (ISO year-week)
        week_buckets = {}
        for dt, key, _ in items:
            yw = dt.isocalendar()[:2]  # (year, week)
            week_buckets.setdefault(yw, []).append((dt, key))
        for yw in sorted(week_buckets.keys(), reverse=True)[:keep_weekly]:
            kept.add(sorted(week_buckets[yw], reverse=True)[0][1])

        # monthly buckets (year, month)
        month_buckets = {}
        for dt, key, _ in items:
            ym = (dt.year, dt.month)
            month_buckets.setdefault(ym, []).append((dt, key))
        for ym in sorted(month_buckets.keys(), reverse=True)[:keep_monthly]:
            kept.add(sorted(month_buckets[ym], reverse=True)[0][1])

        to_delete = [key for _, key, _ in items if key not in kept]

        if dry_run or not to_delete:
            return to_delete

        svc = drive_service()

        # Delete from Drive + DB
        for key in to_delete:
            row = db.query(DriveAsset).filter(DriveAsset.logical_key == key).first()
            if not row:
                continue
            # delete the file in Drive
            svc.files().delete(fileId=row.drive_file_id).execute()
            # delete registry row
            db.delete(row)

        db.commit()
        return to_delete

    finally:
        db.close()