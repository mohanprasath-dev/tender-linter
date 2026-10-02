import json
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    event,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    validates,
)


class Base(DeclarativeBase):
    """Base class for all data layer models."""

    pass


def validate_provenance_field(key: str, value: Any) -> Any:
    """Validate common provenance constraints across models."""
    if value is not None and isinstance(value, str):
        if "unverified" in value.lower():
            raise ValueError(f"Field {key} contains prohibited term 'UNVERIFIED'")
    return value


class Standard(Base):
    """Indian Standards catalogue records with verified provenance."""

    __tablename__ = "standards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    is_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    part: Mapped[str | None] = mapped_column(String(50), nullable=True)
    section: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="UNKNOWN")
    superseded_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("standards.id"), nullable=True
    )
    amendments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Provenance fields (Mandatory)
    catalogue_url: Mapped[str] = mapped_column(Text, nullable=False)
    verified_on: Mapped[date] = mapped_column(Date, nullable=False)
    verified_by: Mapped[str] = mapped_column(String(100), nullable=False)
    second_checked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    evidence_ref: Mapped[str] = mapped_column(Text, nullable=False)

    superseded_by = relationship("Standard", remote_side=[id])

    __table_args__ = (
        CheckConstraint("length(catalogue_url) > 0", name="check_std_catalogue_url_nonempty"),
        CheckConstraint("catalogue_url LIKE 'https://%'", name="check_std_catalogue_url_https"),
        CheckConstraint("length(verified_by) > 0", name="check_std_verified_by_nonempty"),
        CheckConstraint("length(evidence_ref) > 0", name="check_std_evidence_ref_nonempty"),
        CheckConstraint(
            "second_checked_by IS NULL OR lower(second_checked_by) != lower(verified_by)",
            name="check_std_second_checker_distinct",
        ),
    )

    @validates("catalogue_url")
    def validate_catalogue_url(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("catalogue_url is required and cannot be empty")
        if not value.startswith("https://"):
            raise ValueError("catalogue_url must start with https://")
        return validate_provenance_field(key, value)

    @validates("verified_on")
    def validate_verified_on(self, key: str, value: Any) -> Any:
        if value is None:
            raise ValueError("verified_on is required")
        return value

    @validates("verified_by")
    def validate_verified_by(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("verified_by is required and cannot be empty")
        if hasattr(self, "second_checked_by") and self.second_checked_by:
            if value.strip().lower() == self.second_checked_by.strip().lower():
                raise ValueError("second_checked_by must differ from verified_by")
        return validate_provenance_field(key, value)

    @validates("second_checked_by")
    def validate_second_checked_by(self, key: str, value: str | None) -> str | None:
        if value and value.strip():
            if hasattr(self, "verified_by") and self.verified_by:
                if value.strip().lower() == self.verified_by.strip().lower():
                    raise ValueError("second_checked_by must differ from verified_by")
            return validate_provenance_field(key, value)
        return None

    @validates("evidence_ref")
    def validate_evidence_ref(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("evidence_ref is required and cannot be empty")
        return validate_provenance_field(key, value)

    @validates("title", "is_number", "part", "section", "amendments")
    def validate_generic_text(self, key: str, value: Any) -> Any:
        return validate_provenance_field(key, value)


class Product(Base):
    """Product catalog with curated multilingual synonyms."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True, index=True
    )
    synonyms_en: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    synonyms_hi: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    synonyms_other: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    family: Mapped[str] = mapped_column(String(100), nullable=False)


class ProductStandardMap(Base):
    """Mapping between products and relevant Indian Standards with provenance."""

    __tablename__ = "product_standard_map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    standard_id: Mapped[int] = mapped_column(Integer, ForeignKey("standards.id"), nullable=False)
    relation: Mapped[str] = mapped_column(String(50), nullable=False)

    # Provenance fields (Mandatory)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    verified_on: Mapped[date] = mapped_column(Date, nullable=False)
    verified_by: Mapped[str] = mapped_column(String(100), nullable=False)
    second_checked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    evidence_ref: Mapped[str] = mapped_column(Text, nullable=False)

    product = relationship("Product")
    standard = relationship("Standard")

    __table_args__ = (
        CheckConstraint("length(source_url) > 0", name="check_psm_source_url_nonempty"),
        CheckConstraint("source_url LIKE 'https://%'", name="check_psm_source_url_https"),
        CheckConstraint("length(verified_by) > 0", name="check_psm_verified_by_nonempty"),
        CheckConstraint("length(evidence_ref) > 0", name="check_psm_evidence_ref_nonempty"),
        CheckConstraint(
            "second_checked_by IS NULL OR lower(second_checked_by) != lower(verified_by)",
            name="check_psm_second_checker_distinct",
        ),
    )

    @validates("source_url")
    def validate_source_url(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("source_url is required and cannot be empty")
        if not value.startswith("https://"):
            raise ValueError("source_url must start with https://")
        return validate_provenance_field(key, value)

    @validates("verified_on")
    def validate_verified_on(self, key: str, value: Any) -> Any:
        if value is None:
            raise ValueError("verified_on is required")
        return value

    @validates("verified_by")
    def validate_verified_by(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("verified_by is required and cannot be empty")
        if hasattr(self, "second_checked_by") and self.second_checked_by:
            if value.strip().lower() == self.second_checked_by.strip().lower():
                raise ValueError("second_checked_by must differ from verified_by")
        return validate_provenance_field(key, value)

    @validates("second_checked_by")
    def validate_second_checked_by(self, key: str, value: str | None) -> str | None:
        if value and value.strip():
            if hasattr(self, "verified_by") and self.verified_by:
                if value.strip().lower() == self.verified_by.strip().lower():
                    raise ValueError("second_checked_by must differ from verified_by")
            return validate_provenance_field(key, value)
        return None

    @validates("evidence_ref")
    def validate_evidence_ref(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("evidence_ref is required and cannot be empty")
        return validate_provenance_field(key, value)


class CertificationRule(Base):
    """Mandatory certification requirements (CRS, QCO, etc.) for products."""

    __tablename__ = "certification_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    scheme: Mapped[str] = mapped_column(String(50), nullable=False)
    specified_standard_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("standards.id"), nullable=False
    )
    instrument: Mapped[str] = mapped_column(Text, nullable=False)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    transition_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Provenance fields (Mandatory)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    verified_on: Mapped[date] = mapped_column(Date, nullable=False)
    verified_by: Mapped[str] = mapped_column(String(100), nullable=False)
    second_checked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    evidence_ref: Mapped[str] = mapped_column(Text, nullable=False)

    product = relationship("Product")
    specified_standard = relationship("Standard")

    __table_args__ = (
        CheckConstraint("length(source_url) > 0", name="check_cert_source_url_nonempty"),
        CheckConstraint("source_url LIKE 'https://%'", name="check_cert_source_url_https"),
        CheckConstraint("length(verified_by) > 0", name="check_cert_verified_by_nonempty"),
        CheckConstraint("length(evidence_ref) > 0", name="check_cert_evidence_ref_nonempty"),
        CheckConstraint(
            "second_checked_by IS NULL OR lower(second_checked_by) != lower(verified_by)",
            name="check_cert_second_checker_distinct",
        ),
    )

    @validates("source_url")
    def validate_source_url(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("source_url is required and cannot be empty")
        if not value.startswith("https://"):
            raise ValueError("source_url must start with https://")
        return validate_provenance_field(key, value)

    @validates("verified_on")
    def validate_verified_on(self, key: str, value: Any) -> Any:
        if value is None:
            raise ValueError("verified_on is required")
        return value

    @validates("verified_by")
    def validate_verified_by(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("verified_by is required and cannot be empty")
        if hasattr(self, "second_checked_by") and self.second_checked_by:
            if value.strip().lower() == self.second_checked_by.strip().lower():
                raise ValueError("second_checked_by must differ from verified_by")
        return validate_provenance_field(key, value)

    @validates("second_checked_by")
    def validate_second_checked_by(self, key: str, value: str | None) -> str | None:
        if value and value.strip():
            if hasattr(self, "verified_by") and self.verified_by:
                if value.strip().lower() == self.verified_by.strip().lower():
                    raise ValueError("second_checked_by must differ from verified_by")
            return validate_provenance_field(key, value)
        return None

    @validates("evidence_ref")
    def validate_evidence_ref(self, key: str, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("evidence_ref is required and cannot be empty")
        return validate_provenance_field(key, value)


class AlliedLink(Base):
    """Standard to standard linkages with provenance."""

    __tablename__ = "allied_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_standard_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("standards.id"), nullable=False
    )
    to_standard_id: Mapped[int] = mapped_column(Integer, ForeignKey("standards.id"), nullable=False)
    relation: Mapped[str] = mapped_column(String(50), nullable=False)

    # Provenance fields (Mandatory)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    verified_on: Mapped[date] = mapped_column(Date, nullable=False)
    verified_by: Mapped[str] = mapped_column(String(100), nullable=False)
    second_checked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    evidence_ref: Mapped[str] = mapped_column(Text, nullable=False)

    from_standard = relationship("Standard", foreign_keys=[from_standard_id])
    to_standard = relationship("Standard", foreign_keys=[to_standard_id])

    __table_args__ = (
        CheckConstraint("length(source_url) > 0", name="check_allied_source_url_nonempty"),
        CheckConstraint("source_url LIKE 'https://%'", name="check_allied_source_url_https"),
        CheckConstraint("length(verified_by) > 0", name="check_allied_verified_by_nonempty"),
        CheckConstraint("length(evidence_ref) > 0", name="check_allied_evidence_ref_nonempty"),
        CheckConstraint(
            "second_checked_by IS NULL OR lower(second_checked_by) != lower(verified_by)",
            name="check_allied_second_checker_distinct",
        ),
    )


class VagueTerm(Base):
    """Curated phrases that imply standards without citing an exact number."""

    __tablename__ = "vague_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phrase: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    explanation: Mapped[str] = mapped_column(Text, nullable=False)


class User(Base):
    """User account model for authentication and role management."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # Reviewer, Curator, Verifier, Admin
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )


class AuditSession(Base):
    """Audit session tracking uploaded or pasted tender documents and findings."""

    __tablename__ = "audit_sessions"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    document_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    language_hint: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="COMPLETED")
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    clauses_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    findings_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")


class AuditLog(Base):
    """Append-only audit log tracking changes to data layer tables."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # INSERT, UPDATE, DELETE
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    old_values: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_values: Mapped[str | None] = mapped_column(Text, nullable=True)


# Append-only audit logging event listeners
def _extract_dict(target: Any) -> dict[str, Any]:
    state = {}
    for column in target.__table__.columns:
        val = getattr(target, column.name, None)
        if isinstance(val, (date, datetime)):
            state[column.name] = val.isoformat()
        else:
            state[column.name] = val
    return state


def register_audit_listeners() -> None:
    audited_classes = (Standard, ProductStandardMap, CertificationRule, AlliedLink)

    for cls in audited_classes:

        @event.listens_for(cls, "after_insert")
        def audit_insert(mapper: Any, connection: Any, target: Any) -> None:
            data = _extract_dict(target)
            connection.execute(
                AuditLog.__table__.insert().values(
                    timestamp=datetime.now(UTC),
                    action="INSERT",
                    table_name=target.__tablename__,
                    record_id=target.id,
                    new_values=json.dumps(data),
                )
            )

        @event.listens_for(cls, "after_update")
        def audit_update(mapper: Any, connection: Any, target: Any) -> None:
            data = _extract_dict(target)
            connection.execute(
                AuditLog.__table__.insert().values(
                    timestamp=datetime.now(UTC),
                    action="UPDATE",
                    table_name=target.__tablename__,
                    record_id=target.id,
                    new_values=json.dumps(data),
                )
            )


register_audit_listeners()
