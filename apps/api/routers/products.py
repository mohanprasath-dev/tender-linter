from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.schemas.products import (
    CertificationRuleRead,
    ProductRead,
    ProductRulesResponse,
)
from packages.data.db import get_db
from packages.data.models import CertificationRule, Product

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[ProductRead]:
    """Retrieve curated list of product categories."""
    stmt = select(Product).offset(skip).limit(limit)
    products = db.execute(stmt).scalars().all()
    return [ProductRead.model_validate(p) for p in products]


@router.get("/{product_id}/rules", response_model=ProductRulesResponse)
def get_product_rules(
    product_id: int,
    db: Session = Depends(get_db),
) -> ProductRulesResponse:
    """Retrieve product details along with mandatory certification requirements."""
    product = db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

    rules_stmt = select(CertificationRule).where(CertificationRule.product_id == product_id)
    rules = db.execute(rules_stmt).scalars().all()

    return ProductRulesResponse(
        product=ProductRead.model_validate(product),
        certification_rules=[CertificationRuleRead.model_validate(r) for r in rules],
    )
