from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Opportunity, Registration, User
from schemas import RegisteredIdsOut, RegistrationCreate, RegistrationOut
from security import get_current_user


router = APIRouter()


@router.post("", response_model=RegistrationOut, status_code=status.HTTP_201_CREATED)
def create_registration(
    payload: RegistrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RegistrationOut:
    opportunity = db.query(Opportunity).filter(Opportunity.id == payload.opportunity_id).first()
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")

    existing_registration = (
        db.query(Registration)
        .filter(
            Registration.user_id == current_user.id,
            Registration.opportunity_id == payload.opportunity_id,
        )
        .first()
    )
    if existing_registration is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already registered")

    registration = Registration(user_id=current_user.id, opportunity_id=payload.opportunity_id)
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return registration


@router.get("/me", response_model=RegisteredIdsOut)
def get_my_registrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RegisteredIdsOut:
    registrations = (
        db.query(Registration.opportunity_id)
        .filter(Registration.user_id == current_user.id)
        .order_by(Registration.opportunity_id.asc())
        .all()
    )
    registered_ids = [opportunity_id for (opportunity_id,) in registrations]
    return RegisteredIdsOut(registered_ids=registered_ids)
