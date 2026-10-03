"""Command-line utility for database and object store backup, restore, and verification.
Usage:
    python scripts/backup_restore.py --backup --output backups/
    python scripts/backup_restore.py --verify-backup backups/tender_linter_backup_xxx.tar.gz
    python scripts/backup_restore.py --restore backups/tender_linter_backup_xxx.tar.gz
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from apps.api.core.config import settings
from packages.data.backup_restore import create_backup, restore_backup, verify_backup_integrity
from packages.data.db import get_session_local


def main() -> int:
    parser = argparse.ArgumentParser(description="Tender Linter Database Backup and Restore Utility")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--backup", action="store_true", help="Create a verified backup archive")
    group.add_argument("--verify-backup", type=str, metavar="PATH", help="Verify backup archive integrity")
    group.add_argument("--restore", type=str, metavar="PATH", help="Restore database from backup archive")

    parser.add_argument(
        "--output",
        type=str,
        default="./backups",
        help="Output directory for backup archive (default: ./backups)",
    )
    parser.add_argument(
        "--object-store",
        type=str,
        default=settings.OBJECT_STORE_PATH,
        help="Path to object store directory",
    )

    args = parser.parse_args()

    session_local = get_session_local()

    if args.backup:
        out_dir = Path(args.output)
        obj_path = Path(args.object_store) if args.object_store else None
        print(f"Starting backup to {out_dir}...")
        with session_local() as db:
            archive = create_backup(
                db=db,
                output_dir=out_dir,
                object_store_path=obj_path,
                app_version=settings.APP_VERSION,
            )
        print(f"Backup created successfully: {archive}")
        # Verify right away
        res = verify_backup_integrity(archive)
        print(f"Verification: {res}")
        return 0

    if args.verify_backup:
        archive_path = Path(args.verify_backup)
        print(f"Verifying backup integrity for: {archive_path}")
        res = verify_backup_integrity(archive_path)
        if res.get("valid"):
            print("SUCCESS: Backup archive is valid and all checksums match.")
            print(f"Details: {res}")
            return 0
        else:
            print(f"FAILURE: Backup verification failed: {res.get('error')}")
            return 1

    if args.restore:
        archive_path = Path(args.restore)
        obj_path = Path(args.object_store) if args.object_store else None
        print(f"Restoring backup from {archive_path}...")
        with session_local() as db:
            result = restore_backup(
                backup_path=archive_path,
                db=db,
                target_object_store_path=obj_path,
            )
        print(f"Restore finished: {result}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
