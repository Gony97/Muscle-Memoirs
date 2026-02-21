import argparse

from app.services.backup_service import create_and_upload_backup
from app.services.restore_service import restore_db_from_logical_key
from app.services.retention_service import apply_retention
from app.services.attachment_service import upload_attachment

def main():
    p = argparse.ArgumentParser(prog="mm", description="MuscleMemoirs Drive/DB tools")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("backup", help="Create full SQLite snapshot and upload to Drive")

    r = sub.add_parser("restore", help="Restore local DB from Drive")
    r.add_argument("--latest", action="store_true", help="Restore from backup/latest")
    r.add_argument("--key", type=str, help="Restore from a specific logical key (e.g., backup/20260221_214148)")

    rt = sub.add_parser("retention", help="Delete old backups using retention policy")
    rt.add_argument("--apply", action="store_true", help="Actually delete (default is dry-run)")
    rt.add_argument("--keep-daily", type=int, default=30)
    rt.add_argument("--keep-weekly", type=int, default=26)
    rt.add_argument("--keep-monthly", type=int, default=12)

    u = sub.add_parser("upload", help="Upload attachment and register in DB")
    u.add_argument("logical_key", type=str, help="e.g. attachment/user123/avatar")
    u.add_argument("path", type=str, help="Local path to file")

    args = p.parse_args()

    if args.cmd == "backup":
        file_id = create_and_upload_backup()
        print("✅ Backup uploaded. Drive file_id:", file_id)

    elif args.cmd == "restore":
        if args.latest:
            key = "backup/latest"
        elif args.key:
            key = args.key
        else:
            raise SystemExit("Provide --latest or --key")

        out = restore_db_from_logical_key(key)
        print("✅ Restored DB to:", out)

    elif args.cmd == "retention":
        dry_run = not args.apply
        deleted = apply_retention(
            keep_daily=args.keep_daily,
            keep_weekly=args.keep_weekly,
            keep_monthly=args.keep_monthly,
            dry_run=dry_run,
        )
        if dry_run:
            print("🧪 DRY-RUN. Would delete:")
        else:
            print("🗑 Deleted:")
        for k in deleted:
            print(" -", k)

    elif args.cmd == "upload":
        file_id = upload_attachment(args.logical_key, args.path)
        print("✅ Uploaded. Drive file_id:", file_id)

if __name__ == "__main__":
    main()