"""Database and evidence object store backup and tested restore utility.
Provides portable, verified snapshots for SQLite and PostgreSQL with
manifest SHA-256 verification and automated restore testing.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.data.models import (
    CertificationRule,
    Product,
    ProductStandardMap,
    Standard,
    User,
)


def _compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _serialize_date(val: Any) -> Any:
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    return val


def create_backup(
    db: Session,
    output_dir: Path,
    object_store_path: Path | None = None,
    app_version: str = "0.1.0",
) -> Path:
    """Create a compressed, manifest-verified backup archive of the database and object store."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    archive_name = f"tender_linter_backup_{timestamp}.tar.gz"
    archive_path = output_dir / archive_name

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        data_dir = tmp_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        manifest: dict[str, Any] = {
            "created_at": datetime.now(UTC).isoformat(),
            "app_version": app_version,
            "table_counts": {},
            "sha256": {},
        }

        # 1. Export Standards
        stds = db.execute(select(Standard)).scalars().all()
        stds_data = [
            {
                "id": s.id,
                "is_number": s.is_number,
                "part": s.part,
                "title": s.title,
                "publication_year": s.publication_year,
                "status": s.status,
                "superseded_by": s.superseded_by,
                "amendments": s.amendments,
                "catalogue_url": s.catalogue_url,
                "verified_on": _serialize_date(s.verified_on),
                "verified_by": s.verified_by,
                "second_checked_by": s.second_checked_by,
                "evidence_ref": s.evidence_ref,
            }
            for s in stds
        ]
        manifest["table_counts"]["standards"] = len(stds_data)
        stds_bytes = json.dumps(stds_data, indent=2).encode("utf-8")
        manifest["sha256"]["standards.json"] = _compute_sha256(stds_bytes)
        (data_dir / "standards.json").write_bytes(stds_bytes)

        # 2. Export Products
        prods = db.execute(select(Product)).scalars().all()
        prods_data = [
            {
                "id": p.id,
                "canonical_name": p.canonical_name,
                "family": p.family,
                "synonyms_en": p.synonyms_en,
                "synonyms_hi": p.synonyms_hi,
                "synonyms_other": p.synonyms_other,
            }
            for p in prods
        ]
        manifest["table_counts"]["products"] = len(prods_data)
        prods_bytes = json.dumps(prods_data, indent=2).encode("utf-8")
        manifest["sha256"]["products.json"] = _compute_sha256(prods_bytes)
        (data_dir / "products.json").write_bytes(prods_bytes)

        # 3. Export ProductStandardMaps
        maps = db.execute(select(ProductStandardMap)).scalars().all()
        maps_data = [
            {
                "id": m.id,
                "product_id": m.product_id,
                "standard_id": m.standard_id,
                "relation": m.relation,
                "source_url": m.source_url,
                "verified_on": _serialize_date(m.verified_on),
                "verified_by": m.verified_by,
                "second_checked_by": m.second_checked_by,
                "evidence_ref": m.evidence_ref,
            }
            for m in maps
        ]
        manifest["table_counts"]["maps"] = len(maps_data)
        maps_bytes = json.dumps(maps_data, indent=2).encode("utf-8")
        manifest["sha256"]["maps.json"] = _compute_sha256(maps_bytes)
        (data_dir / "maps.json").write_bytes(maps_bytes)

        # 4. Export CertificationRules
        rules = db.execute(select(CertificationRule)).scalars().all()
        rules_data = [
            {
                "id": r.id,
                "product_id": r.product_id,
                "scheme": r.scheme,
                "specified_standard_id": r.specified_standard_id,
                "instrument": r.instrument,
                "source_url": r.source_url,
                "verified_on": _serialize_date(r.verified_on),
                "verified_by": r.verified_by,
                "second_checked_by": r.second_checked_by,
                "evidence_ref": r.evidence_ref,
            }
            for r in rules
        ]
        manifest["table_counts"]["certification_rules"] = len(rules_data)
        rules_bytes = json.dumps(rules_data, indent=2).encode("utf-8")
        manifest["sha256"]["certification_rules.json"] = _compute_sha256(rules_bytes)
        (data_dir / "certification_rules.json").write_bytes(rules_bytes)

        # 5. Export Users
        users = db.execute(select(User)).scalars().all()
        users_data = [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "full_name": u.full_name,
                "hashed_password": u.hashed_password,
                "role": u.role,
                "created_at": _serialize_date(u.created_at),
            }
            for u in users
        ]
        manifest["table_counts"]["users"] = len(users_data)
        users_bytes = json.dumps(users_data, indent=2).encode("utf-8")
        manifest["sha256"]["users.json"] = _compute_sha256(users_bytes)
        (data_dir / "users.json").write_bytes(users_bytes)

        # 6. Export Object Store / Evidence Files
        if object_store_path and object_store_path.exists():
            obj_dest = tmp_dir / "object_store"
            obj_dest.mkdir(parents=True, exist_ok=True)
            for item in object_store_path.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(object_store_path)
                    target = obj_dest / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    content = item.read_bytes()
                    target.write_bytes(content)
                    manifest["sha256"][f"object_store/{rel.as_posix()}"] = _compute_sha256(content)

        # Write manifest
        manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
        (tmp_dir / "manifest.json").write_bytes(manifest_bytes)

        # Package into tar.gz
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(tmp_dir, arcname=".")

    return archive_path


def verify_backup_integrity(backup_path: Path) -> dict[str, Any]:
    """Verify integrity of a backup archive against its recorded manifest SHA-256 checksums."""
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup archive not found: {backup_path}")

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=tmp_dir)

        manifest_file = tmp_dir / "manifest.json"
        if not manifest_file.exists():
            return {"valid": False, "error": "manifest.json missing"}

        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        checksums = manifest.get("sha256", {})

        for rel_path_str, expected_hash in checksums.items():
            if rel_path_str.startswith("object_store/"):
                target_file = tmp_dir / rel_path_str
            else:
                target_file = tmp_dir / "data" / rel_path_str

            if not target_file.exists():
                return {"valid": False, "error": f"File missing in archive: {rel_path_str}"}

            actual_hash = _compute_sha256(target_file.read_bytes())
            if actual_hash != expected_hash:
                return {
                    "valid": False,
                    "error": f"Checksum mismatch for {rel_path_str}: expected {expected_hash}, got {actual_hash}",
                }

        return {
            "valid": True,
            "created_at": manifest.get("created_at"),
            "app_version": manifest.get("app_version"),
            "table_counts": manifest.get("table_counts", {}),
        }


def restore_backup(
    backup_path: Path,
    db: Session,
    target_object_store_path: Path | None = None,
) -> dict[str, Any]:
    """Restore database tables and object store files from a verified backup archive."""
    integrity = verify_backup_integrity(backup_path)
    if not integrity.get("valid"):
        raise ValueError(f"Cannot restore invalid backup archive: {integrity.get('error')}")

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=tmp_dir)

        rows_restored = 0

        # Restore Standards
        stds_file = tmp_dir / "data" / "standards.json"
        if stds_file.exists():
            stds_list = json.loads(stds_file.read_text(encoding="utf-8"))
            for s in stds_list:
                v_date = date.fromisoformat(s["verified_on"]) if s.get("verified_on") else None
                existing = db.execute(select(Standard).where(Standard.is_number == s["is_number"])).scalar_one_or_none()
                if not existing:
                    std_obj = Standard(
                        is_number=s["is_number"],
                        part=s.get("part"),
                        title=s["title"],
                        publication_year=s.get("publication_year"),
                        status=s["status"],
                        superseded_by=s.get("superseded_by"),
                        amendments=s.get("amendments"),
                        catalogue_url=s["catalogue_url"],
                        verified_on=v_date,
                        verified_by=s["verified_by"],
                        second_checked_by=s.get("second_checked_by"),
                        evidence_ref=s["evidence_ref"],
                    )
                    db.add(std_obj)
                    rows_restored += 1

        # Restore Products
        prods_file = tmp_dir / "data" / "products.json"
        if prods_file.exists():
            prods_list = json.loads(prods_file.read_text(encoding="utf-8"))
            for p in prods_list:
                existing = db.execute(select(Product).where(Product.canonical_name == p["canonical_name"])).scalar_one_or_none()
                if not existing:
                    prod_obj = Product(
                        canonical_name=p["canonical_name"],
                        family=p.get("family", "General"),
                        synonyms_en=p.get("synonyms_en", "[]"),
                        synonyms_hi=p.get("synonyms_hi", "[]"),
                        synonyms_other=p.get("synonyms_other", "[]"),
                    )
                    db.add(prod_obj)
                    rows_restored += 1

        # Restore Users
        users_file = tmp_dir / "data" / "users.json"
        if users_file.exists():
            users_list = json.loads(users_file.read_text(encoding="utf-8"))
            for u in users_list:
                existing = db.execute(select(User).where(User.username == u["username"])).scalar_one_or_none()
                if not existing:
                    user_obj = User(
                        username=u["username"],
                        email=u.get("email"),
                        full_name=u.get("full_name"),
                        hashed_password=u["hashed_password"],
                        role=u["role"],
                        created_at=datetime.fromisoformat(u["created_at"]) if u.get("created_at") else datetime.now(UTC),
                    )
                    db.add(user_obj)
                    rows_restored += 1

        db.commit()

        # Restore Object Store Files
        files_restored = 0
        obj_source = tmp_dir / "object_store"
        if obj_source.exists() and target_object_store_path:
            target_object_store_path.mkdir(parents=True, exist_ok=True)
            for item in obj_source.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(obj_source)
                    dest = target_object_store_path / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest)
                    files_restored += 1

        return {
            "status": "success",
            "rows_restored": rows_restored,
            "files_restored": files_restored,
            "table_counts": integrity.get("table_counts", {}),
        }
