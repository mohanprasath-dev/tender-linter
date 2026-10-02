from __future__ import annotations

import datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field

from packages.rules.normaliser import base_is_number


class StandardRecord(BaseModel):
    id: int
    is_number: str
    part: str | None = None
    section: str | None = None
    title: str = ""
    publication_year: int | None = None
    status: str = "Active"
    superseded_by_id: int | None = None
    amendments: str | None = None
    catalogue_url: str = ""
    verified_on: datetime.date | None = None
    verified_by: str | None = None
    is_conflict: bool = False


class ProductRecord(BaseModel):
    id: int
    canonical_name: str
    family: str
    synonyms_en: list[str] = Field(default_factory=list)
    synonyms_hi: list[str] = Field(default_factory=list)


class ProductStandardMapRecord(BaseModel):
    id: int
    product_id: int
    standard_id: int
    relation: str = "PRIMARY"
    source_url: str = ""
    verified_on: datetime.date | None = None
    verified_by: str | None = None
    is_conflict: bool = False


class CertificationRuleRecord(BaseModel):
    id: int
    product_id: int
    scheme: str = "CRS"
    specified_standard_id: int
    instrument: str = ""
    source_url: str = ""
    verified_on: datetime.date | None = None
    verified_by: str | None = None
    is_conflict: bool = False


class AlliedLinkRecord(BaseModel):
    id: int
    source_standard_id: int
    target_standard_id: int
    relation: str = "NORMATIVE"
    source_url: str = ""
    verified_on: datetime.date | None = None
    verified_by: str | None = None
    is_conflict: bool = False


class VagueTermRecord(BaseModel):
    id: int
    term: str
    language: str = "en"
    explanation: str = ""


class RuleDataContext(Protocol):
    stale_days: int

    def get_standard_by_number(self, is_number: str) -> StandardRecord | None:
        ...

    def get_standard_by_id(self, standard_id: int) -> StandardRecord | None:
        ...

    def list_known_is_numbers(self) -> list[str]:
        ...

    def get_product(self, product_id_or_name: str | int) -> ProductRecord | None:
        ...

    def get_certification_rules_for_product(self, product_id: int) -> list[CertificationRuleRecord]:
        ...

    def get_product_standard_maps_for_product(self, product_id: int) -> list[ProductStandardMapRecord]:
        ...

    def get_product_standard_maps_for_standard(self, standard_id: int) -> list[ProductStandardMapRecord]:
        ...

    def get_allied_links_for_standard(self, standard_id: int) -> list[AlliedLinkRecord]:
        ...

    def get_vague_terms(self, language: str | None = None) -> list[VagueTermRecord]:
        ...


class InMemoryRuleDataContext:
    def __init__(self, stale_days: int = 180):
        self.stale_days = stale_days
        self._standards: dict[int, StandardRecord] = {}
        self._standards_by_number: dict[str, StandardRecord] = {}
        self._products: dict[int, ProductRecord] = {}
        self._products_by_name: dict[str, ProductRecord] = {}
        self._product_standard_maps: list[ProductStandardMapRecord] = []
        self._certification_rules: list[CertificationRuleRecord] = []
        self._allied_links: list[AlliedLinkRecord] = []
        self._vague_terms: list[VagueTermRecord] = []

    def add_standards(self, standards: list[StandardRecord]) -> None:
        for s in standards:
            self._standards[s.id] = s
            self._standards_by_number[s.is_number] = s
            base = base_is_number(s.is_number)
            if base not in self._standards_by_number:
                self._standards_by_number[base] = s

    def add_products(self, products: list[ProductRecord]) -> None:
        for p in products:
            self._products[p.id] = p
            self._products_by_name[p.canonical_name.lower()] = p
            for syn in p.synonyms_en:
                self._products_by_name[syn.lower()] = p
            for syn in p.synonyms_hi:
                self._products_by_name[syn.lower()] = p

    def add_product_standard_maps(self, maps: list[ProductStandardMapRecord]) -> None:
        self._product_standard_maps.extend(maps)

    def add_certification_rules(self, rules: list[CertificationRuleRecord]) -> None:
        self._certification_rules.extend(rules)

    def add_allied_links(self, links: list[AlliedLinkRecord]) -> None:
        self._allied_links.extend(links)

    def add_vague_terms(self, terms: list[VagueTermRecord]) -> None:
        self._vague_terms.extend(terms)

    def get_standard_by_number(self, is_number: str) -> StandardRecord | None:
        if is_number in self._standards_by_number:
            return self._standards_by_number[is_number]
        base = base_is_number(is_number)
        return self._standards_by_number.get(base)

    def get_standard_by_id(self, standard_id: int) -> StandardRecord | None:
        return self._standards.get(standard_id)

    def list_known_is_numbers(self) -> list[str]:
        return [s.is_number for s in self._standards.values()]

    def get_product(self, product_id_or_name: str | int) -> ProductRecord | None:
        if isinstance(product_id_or_name, int):
            return self._products.get(product_id_or_name)
        return self._products_by_name.get(product_id_or_name.lower())

    def get_certification_rules_for_product(self, product_id: int) -> list[CertificationRuleRecord]:
        return [r for r in self._certification_rules if r.product_id == product_id]

    def get_product_standard_maps_for_product(self, product_id: int) -> list[ProductStandardMapRecord]:
        return [m for m in self._product_standard_maps if m.product_id == product_id]

    def get_product_standard_maps_for_standard(self, standard_id: int) -> list[ProductStandardMapRecord]:
        return [m for m in self._product_standard_maps if m.standard_id == standard_id]

    def get_allied_links_for_standard(self, standard_id: int) -> list[AlliedLinkRecord]:
        return [lnk for lnk in self._allied_links if lnk.source_standard_id == standard_id]

    def get_vague_terms(self, language: str | None = None) -> list[VagueTermRecord]:
        if language:
            return [vt for vt in self._vague_terms if vt.language == language]
        return list(self._vague_terms)


class DatabaseRuleDataContext:
    """SQLAlchemy-backed implementation of RuleDataContext."""

    def __init__(self, session: Any, stale_days: int = 180):
        self.session = session
        self.stale_days = stale_days

    def get_standard_by_number(self, is_number: str) -> StandardRecord | None:
        from sqlalchemy import select

        from packages.data.models import Standard

        stmt = select(Standard).where(Standard.is_number == is_number)
        std = self.session.execute(stmt).scalar_one_or_none()
        if not std:
            base = base_is_number(is_number)
            stmt = select(Standard).where(Standard.is_number == base)
            std = self.session.execute(stmt).scalar_one_or_none()
        if not std:
            return None
        return StandardRecord(
            id=std.id,
            is_number=std.is_number,
            part=std.part,
            section=std.section,
            title=std.title,
            publication_year=std.publication_year,
            status=std.status,
            superseded_by_id=std.superseded_by_id,
            amendments=std.amendments,
            catalogue_url=std.catalogue_url,
            verified_on=std.verified_on,
            verified_by=std.verified_by,
            is_conflict=(std.status == "CONFLICT"),
        )

    def get_standard_by_id(self, standard_id: int) -> StandardRecord | None:
        from packages.data.models import Standard
        std = self.session.get(Standard, standard_id)
        if not std:
            return None
        return StandardRecord(
            id=std.id,
            is_number=std.is_number,
            part=std.part,
            section=std.section,
            title=std.title,
            publication_year=std.publication_year,
            status=std.status,
            superseded_by_id=std.superseded_by_id,
            amendments=std.amendments,
            catalogue_url=std.catalogue_url,
            verified_on=std.verified_on,
            verified_by=std.verified_by,
            is_conflict=(std.status == "CONFLICT"),
        )

    def list_known_is_numbers(self) -> list[str]:
        from sqlalchemy import select

        from packages.data.models import Standard
        stmt = select(Standard.is_number)
        return list(self.session.execute(stmt).scalars().all())

    def get_product(self, product_id_or_name: str | int) -> ProductRecord | None:
        import json

        from sqlalchemy import select

        from packages.data.models import Product

        if isinstance(product_id_or_name, int):
            prod = self.session.get(Product, product_id_or_name)
        else:
            name_lower = product_id_or_name.lower().strip()
            stmt = select(Product)
            all_prods = self.session.execute(stmt).scalars().all()
            prod = None
            for p in all_prods:
                if p.canonical_name.lower() == name_lower:
                    prod = p
                    break
                syn_en = json.loads(p.synonyms_en or "[]")
                syn_hi = json.loads(p.synonyms_hi or "[]")
                if any(s.lower() == name_lower for s in syn_en + syn_hi):
                    prod = p
                    break

        if not prod:
            return None
        return ProductRecord(
            id=prod.id,
            canonical_name=prod.canonical_name,
            family=prod.family,
            synonyms_en=json.loads(prod.synonyms_en or "[]"),
            synonyms_hi=json.loads(prod.synonyms_hi or "[]"),
        )

    def get_certification_rules_for_product(self, product_id: int) -> list[CertificationRuleRecord]:
        from sqlalchemy import select

        from packages.data.models import CertificationRule

        stmt = select(CertificationRule).where(CertificationRule.product_id == product_id)
        rules = self.session.execute(stmt).scalars().all()
        return [
            CertificationRuleRecord(
                id=r.id,
                product_id=r.product_id,
                scheme=r.scheme,
                specified_standard_id=r.specified_standard_id,
                instrument=r.instrument,
                source_url=r.source_url,
                verified_on=r.verified_on,
                verified_by=r.verified_by,
            )
            for r in rules
        ]

    def get_product_standard_maps_for_product(self, product_id: int) -> list[ProductStandardMapRecord]:
        from sqlalchemy import select

        from packages.data.models import ProductStandardMap

        stmt = select(ProductStandardMap).where(ProductStandardMap.product_id == product_id)
        maps = self.session.execute(stmt).scalars().all()
        return [
            ProductStandardMapRecord(
                id=m.id,
                product_id=m.product_id,
                standard_id=m.standard_id,
                relation=m.relation,
                source_url=m.source_url,
                verified_on=m.verified_on,
                verified_by=m.verified_by,
            )
            for m in maps
        ]

    def get_product_standard_maps_for_standard(self, standard_id: int) -> list[ProductStandardMapRecord]:
        from sqlalchemy import select

        from packages.data.models import ProductStandardMap

        stmt = select(ProductStandardMap).where(ProductStandardMap.standard_id == standard_id)
        maps = self.session.execute(stmt).scalars().all()
        return [
            ProductStandardMapRecord(
                id=m.id,
                product_id=m.product_id,
                standard_id=m.standard_id,
                relation=m.relation,
                source_url=m.source_url,
                verified_on=m.verified_on,
                verified_by=m.verified_by,
            )
            for m in maps
        ]

    def get_allied_links_for_standard(self, standard_id: int) -> list[AlliedLinkRecord]:
        from sqlalchemy import select

        from packages.data.models import AlliedLink

        stmt = select(AlliedLink).where(AlliedLink.from_standard_id == standard_id)
        links = self.session.execute(stmt).scalars().all()
        return [
            AlliedLinkRecord(
                id=lnk.id,
                source_standard_id=lnk.from_standard_id,
                target_standard_id=lnk.to_standard_id,
                relation=lnk.relation,
                source_url=lnk.source_url,
                verified_on=lnk.verified_on,
                verified_by=lnk.verified_by,
            )
            for lnk in links
        ]

    def get_vague_terms(self, language: str | None = None) -> list[VagueTermRecord]:
        from sqlalchemy import select

        from packages.data.models import VagueTerm

        stmt = select(VagueTerm)
        if language:
            stmt = stmt.where(VagueTerm.language == language)
        terms = self.session.execute(stmt).scalars().all()
        return [
            VagueTermRecord(
                id=t.id,
                term=t.phrase,
                language=t.language,
                explanation=t.explanation,
            )
            for t in terms
        ]


def create_seed_rule_context(stale_days: int = 180) -> InMemoryRuleDataContext:
    """Build in-memory rule data context with verified seed data from Spec Section 3.2."""
    ctx = InMemoryRuleDataContext(stale_days=stale_days)

    # Verified Standards
    s1 = StandardRecord(
        id=1,
        is_number="IS/IEC 62368 Part 1",
        part="1",
        title="Audio/video, information and communication technology equipment",
        publication_year=2023,
        status="Active",
        catalogue_url="https://standardsbis.bsbedge.com/record/1",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="team",
    )
    s2 = StandardRecord(
        id=2,
        is_number="IS 302-2-25",
        part=None,
        title="Safety of household and similar electrical appliances: Microwave ovens",
        publication_year=None,
        status="Active",
        catalogue_url="https://standardsbis.bsbedge.com/record/2",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="team",
    )
    s3 = StandardRecord(
        id=3,
        is_number="IS 13252 (Part 1)",
        part="1",
        title="Information Technology Equipment - Safety Part 1: General Requirements",
        publication_year=2010,
        status="Active",
        catalogue_url="https://standardsbis.bsbedge.com/record/3",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="team",
    )
    ctx.add_standards([s1, s2, s3])

    # Products
    p1 = ProductRecord(
        id=1,
        canonical_name="Laptop / notebook / tablet",
        family="IT equipment",
        synonyms_en=["laptop", "laptops", "notebook", "tablet", "tablets"],
        synonyms_hi=["लैपटॉप"],
    )
    p2 = ProductRecord(
        id=2,
        canonical_name="Power adaptors for IT equipment",
        family="IT equipment",
        synonyms_en=["power adaptor", "power adaptors", "adaptor"],
        synonyms_hi=[],
    )
    p3 = ProductRecord(
        id=3,
        canonical_name="Microwave ovens",
        family="Household appliances",
        synonyms_en=["microwave oven", "microwave ovens", "microwave"],
        synonyms_hi=["माइक्रोवेव", "माइक्रोवेव ओवन"],
    )
    p4 = ProductRecord(
        id=4,
        canonical_name="IT equipment (general)",
        family="IT equipment",
        synonyms_en=["it equipment"],
        synonyms_hi=[],
    )
    ctx.add_products([p1, p2, p3, p4])

    # Product-Standard Map
    psm1 = ProductStandardMapRecord(
        id=1,
        product_id=1,
        standard_id=1,
        relation="PRIMARY",
        source_url="https://bis.gov.in/scheme2",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="team",
    )
    psm2 = ProductStandardMapRecord(
        id=2,
        product_id=2,
        standard_id=1,
        relation="PRIMARY",
        source_url="https://bis.gov.in/scheme2",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="team",
    )
    psm3 = ProductStandardMapRecord(
        id=3,
        product_id=3,
        standard_id=2,
        relation="PRIMARY",
        source_url="https://bis.gov.in/scheme2",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="team",
    )
    psm4 = ProductStandardMapRecord(
        id=4,
        product_id=4,
        standard_id=3,
        relation="PRIMARY",
        source_url="https://standardsbis.bsbedge.com/record/3",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="team",
    )
    ctx.add_product_standard_maps([psm1, psm2, psm3, psm4])

    # Certification Rules
    cr1 = CertificationRuleRecord(
        id=1,
        product_id=1,
        scheme="CRS",
        specified_standard_id=1,
        instrument="Electronics and Information Technology Goods (Requirement for Compulsory Registration) Order",
        source_url="https://bis.gov.in/scheme2",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="team",
    )
    cr2 = CertificationRuleRecord(
        id=2,
        product_id=3,
        scheme="CRS",
        specified_standard_id=2,
        instrument="Electrical Appliances (Quality Control) Order",
        source_url="https://bis.gov.in/scheme2",
        verified_on=datetime.date(2026, 10, 2),
        verified_by="team",
    )
    ctx.add_certification_rules([cr1, cr2])

    # Vague Terms
    vt1 = VagueTermRecord(
        id=1,
        term="ISI quality",
        language="en",
        explanation="Refers to quality generally without specifying an Indian Standard number.",
    )
    vt2 = VagueTermRecord(
        id=2,
        term="as per BIS",
        language="en",
        explanation="Names the bureau without citing an applicable standard number.",
    )
    ctx.add_vague_terms([vt1, vt2])

    return ctx


def create_rule_context_from_db(db_session: Any, stale_days: int = 180) -> InMemoryRuleDataContext:
    """Build an InMemoryRuleDataContext by querying verified database rows."""
    import json

    from sqlalchemy import select

    from packages.data.models import (
        AlliedLink,
        CertificationRule,
        Product,
        ProductStandardMap,
        Standard,
        VagueTerm,
    )

    ctx = InMemoryRuleDataContext(stale_days=stale_days)

    # 1. Standards
    db_standards = db_session.execute(select(Standard)).scalars().all()
    standards_records = []
    for s in db_standards:
        standards_records.append(
            StandardRecord(
                id=s.id,
                is_number=s.is_number,
                part=s.part,
                section=s.section,
                title=s.title,
                publication_year=s.publication_year,
                status=s.status,
                superseded_by_id=s.superseded_by_id,
                amendments=s.amendments,
                catalogue_url=s.catalogue_url,
                verified_on=s.verified_on,
                verified_by=s.verified_by,
            )
        )
    ctx.add_standards(standards_records)

    # 2. Products
    db_products = db_session.execute(select(Product)).scalars().all()
    product_records = []
    for p in db_products:
        syn_en = json.loads(p.synonyms_en) if isinstance(p.synonyms_en, str) else p.synonyms_en
        syn_hi = json.loads(p.synonyms_hi) if isinstance(p.synonyms_hi, str) else p.synonyms_hi
        product_records.append(
            ProductRecord(
                id=p.id,
                canonical_name=p.canonical_name,
                family=p.family,
                synonyms_en=syn_en or [],
                synonyms_hi=syn_hi or [],
            )
        )
    ctx.add_products(product_records)

    # 3. Product Standard Maps
    db_maps = db_session.execute(select(ProductStandardMap)).scalars().all()
    map_records = []
    for m in db_maps:
        map_records.append(
            ProductStandardMapRecord(
                id=m.id,
                product_id=m.product_id,
                standard_id=m.standard_id,
                relation=m.relation,
                source_url=m.source_url,
                verified_on=m.verified_on,
                verified_by=m.verified_by,
            )
        )
    ctx.add_product_standard_maps(map_records)

    # 4. Certification Rules
    db_certs = db_session.execute(select(CertificationRule)).scalars().all()
    cert_records = []
    for c in db_certs:
        cert_records.append(
            CertificationRuleRecord(
                id=c.id,
                product_id=c.product_id,
                scheme=c.scheme,
                specified_standard_id=c.specified_standard_id,
                instrument=c.instrument,
                source_url=c.source_url,
                verified_on=c.verified_on,
                verified_by=c.verified_by,
            )
        )
    ctx.add_certification_rules(cert_records)

    # 5. Allied Links
    db_allied = db_session.execute(select(AlliedLink)).scalars().all()
    allied_records = []
    for a in db_allied:
        allied_records.append(
            AlliedLinkRecord(
                id=a.id,
                source_standard_id=a.from_standard_id,
                allied_standard_id=a.to_standard_id,
                relation=a.relation,
                source_url=a.source_url,
                verified_on=a.verified_on,
                verified_by=a.verified_by,
            )
        )
    ctx.add_allied_links(allied_records)

    # 6. Vague Terms
    db_vague = db_session.execute(select(VagueTerm)).scalars().all()
    if db_vague:
        vague_records = [
            VagueTermRecord(id=v.id, term=v.phrase, language=v.language, explanation=v.explanation)
            for v in db_vague
        ]
        ctx.add_vague_terms(vague_records)
    else:
        ctx.add_vague_terms([
            VagueTermRecord(
                id=1,
                term="ISI quality",
                language="en",
                explanation="Refers to quality generally without specifying an Indian Standard number.",
            ),
            VagueTermRecord(
                id=2,
                term="as per BIS",
                language="en",
                explanation="Names the bureau without citing an applicable standard number.",
            ),
        ])

    return ctx

