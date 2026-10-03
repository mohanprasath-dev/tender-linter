"""Security validation, upload scanning, and data retention policies for Tender Linter."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.config import settings
from packages.data.models import AuditLog, AuditSession, User

# Maximum file upload size: 25 Megabytes
MAX_UPLOAD_SIZE = 25 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# Prohibited executable signatures and magic bytes
PROHIBITED_MAGIC_SIGNATURES = [
    (b"MZ", "Windows PE executable / DLL"),
    (b"\x7fELF", "Linux ELF binary executable"),
    (b"\xca\xfe\xba\xbe", "Mach-O / Java class binary"),
    (b"\xfe\xed\xfa\xce", "Mach-O binary"),
    (b"\xfe\xed\xfa\xcf", "Mach-O 64-bit binary"),
    (b"\xce\xfa\xed\xfe", "Mach-O binary"),
    (b"\xcf\xfa\xed\xfe", "Mach-O 64-bit binary"),
    (b"#!/bin/sh", "Shell script executable"),
    (b"#!/bin/bash", "Bash script executable"),
    (b"#!/usr/bin/env", "Script interpreter executable"),
]


def validate_upload_safety(content: bytes, filename: str) -> None:
    """Validate uploaded document for size limits, allowed extensions, and malicious payloads.

    Raises:
        HTTPException: If file exceeds size limit, has unsupported extension, or contains
                       disallowed executable signatures.
    """
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # 1. Enforce size limits
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_SIZE // (1024 * 1024)} MB",
        )

    # 2. Enforce extension whitelist
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Extension '{ext}' is not permitted. Allowed: {sorted(list(ALLOWED_EXTENSIONS))}",
        )

    # 3. Check for prohibited binary/executable signatures
    for sig, desc in PROHIBITED_MAGIC_SIGNATURES:
        if content.startswith(sig):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security violation: uploaded content matches disallowed signature ({desc})",
            )

    # 4. Strict format-specific header validation
    if ext == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF structure: missing %PDF- header signature",
            )
    elif ext == ".docx":
        if not content.startswith(b"PK\x03\x04"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid DOCX package: missing PK archive header signature",
            )
    elif ext == ".txt":
        if b"\x00" in content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid text format: binary null bytes detected in text upload",
            )


def delete_audit_session(db: Session, audit_id: str, requesting_user: User) -> bool:
    """Perform one-click complete deletion of a confidential audit draft.

    Enforces ownership authorization (or Admin role) and writes an append-only audit log entry.
    """
    session = db.execute(
        select(AuditSession).where(AuditSession.id == audit_id)
    ).scalar_one_or_none()
    if not session:
        return False

    # Check permission: Creator or Admin
    if session.created_by != requesting_user.username and requesting_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete another officer's audit draft",
        )

    # Record deletion in append-only audit log
    audit_log = AuditLog(
        timestamp=datetime.now(UTC),
        user_id=requesting_user.id,
        action="DELETE_AUDIT",
        table_name="audit_sessions",
        record_id=0,
        old_values=json.dumps(
            {
                "audit_id": session.id,
                "document_name": session.document_name,
                "created_by": session.created_by,
                "deleted_by": requesting_user.username,
            }
        ),
        new_values=None,
    )
    db.add(audit_log)

    db.delete(session)
    db.commit()
    return True


def purge_expired_audit_sessions(db: Session, max_age_days: int | None = None) -> int:
    """Purge confidential tender audits older than the retention threshold.

    Default retention is short (configurable via RETENTION_DAYS or max_age_days parameter).
    """
    days = max_age_days or settings.RETENTION_DAYS or 30
    cutoff = datetime.now(UTC) - timedelta(days=days)

    stmt = select(AuditSession).where(AuditSession.created_at < cutoff)
    expired_sessions = db.execute(stmt).scalars().all()
    count = len(expired_sessions)

    if count > 0:
        for s in expired_sessions:
            log_entry = AuditLog(
                timestamp=datetime.now(UTC),
                user_id=None,
                action="RETENTION_PURGE",
                table_name="audit_sessions",
                record_id=0,
                old_values=json.dumps({"audit_id": s.id, "created_at": s.created_at.isoformat()}),
                new_values=None,
            )
            db.add(log_entry)
            db.delete(s)

        db.commit()

    return count
