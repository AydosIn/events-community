from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Opportunity
from schemas import OpportunityOut


router = APIRouter()


@router.get("", response_model=list[OpportunityOut])
def list_opportunities(
    region_name: str | None = None,
    type: str | None = None,
    db: Session = Depends(get_db),
) -> list[OpportunityOut]:
    query = db.query(Opportunity)

    if region_name:
        query = query.filter(Opportunity.region_name.ilike(f"%{region_name.strip()}%"))
    if type:
        query = query.filter(Opportunity.type == type)

    return query.order_by(Opportunity.id.asc()).all()


@router.get("/{id}", response_model=OpportunityOut)
def get_opportunity(id: int, db: Session = Depends(get_db)) -> OpportunityOut:
    opportunity = db.query(Opportunity).filter(Opportunity.id == id).first()
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")

    return opportunity
