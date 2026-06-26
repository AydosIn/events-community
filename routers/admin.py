from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import get_db
from models import Opportunity, Registration, User
from schemas import (
    AdminAnalyticsOut,
    AdminRegistrationDetailOut,
    AdminOpportunityListOut,
    AdminOverviewOut,
    AdminRegistrationItemOut,
    AdminRegistrationListOut,
    AdminRegistrationUpdate,
    AdminUserDetailOut,
    AdminUserListOut,
    AdminUserItemOut,
    AdminUserRegistrationOut,
    OpportunityCreate,
    OpportunityOut,
    OpportunityUpdate,
    RegistrationRegionBreakdown,
    RegistrationTypeBreakdown,
    TopOpportunityOut,
)
from security import get_admin_user, is_admin_email


router = APIRouter()


def _normalize_pagination(limit: int, offset: int) -> tuple[int, int]:
    safe_limit = max(1, min(limit, 100))
    safe_offset = max(0, offset)
    return safe_limit, safe_offset


@router.get("/overview", response_model=AdminOverviewOut)
def get_admin_overview(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminOverviewOut:
    return AdminOverviewOut(
        users_count=db.query(func.count(User.id)).scalar() or 0,
        opportunities_count=db.query(func.count(Opportunity.id)).scalar() or 0,
        registrations_count=db.query(func.count(Registration.id)).scalar() or 0,
    )


@router.get("/analytics", response_model=AdminAnalyticsOut)
def get_admin_analytics(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminAnalyticsOut:
    # SQLite stores naive UTC timestamps; keep comparisons naive for compatibility.
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    type_rows = (
        db.query(Opportunity.type, func.count(Registration.id).label("count"))
        .join(Registration, Registration.opportunity_id == Opportunity.id)
        .group_by(Opportunity.type)
        .order_by(func.count(Registration.id).desc(), Opportunity.type.asc())
        .all()
    )

    region_rows = (
        db.query(Opportunity.region_name, func.count(Registration.id).label("count"))
        .join(Registration, Registration.opportunity_id == Opportunity.id)
        .group_by(Opportunity.region_name)
        .order_by(func.count(Registration.id).desc(), Opportunity.region_name.asc())
        .all()
    )

    top_rows = (
        db.query(
            Opportunity.id.label("opportunity_id"),
            Opportunity.title,
            Opportunity.type,
            Opportunity.region_name,
            func.count(Registration.id).label("registrations_count"),
        )
        .outerjoin(Registration, Registration.opportunity_id == Opportunity.id)
        .group_by(Opportunity.id)
        .order_by(func.count(Registration.id).desc(), Opportunity.id.asc())
        .limit(10)
        .all()
    )

    registrations_count = db.query(func.count(Registration.id)).scalar() or 0
    opportunities_count = db.query(func.count(Opportunity.id)).scalar() or 0
    registrations_last_7_days = (
        db.query(func.count(Registration.id))
        .filter(Registration.created_at >= seven_days_ago)
        .scalar()
        or 0
    )
    registrations_last_30_days = (
        db.query(func.count(Registration.id))
        .filter(Registration.created_at >= thirty_days_ago)
        .scalar()
        or 0
    )

    average_registrations_per_opportunity = (
        round(registrations_count / opportunities_count, 2) if opportunities_count else 0.0
    )

    return AdminAnalyticsOut(
        registrations_by_type=[
            RegistrationTypeBreakdown(type=row.type, count=row.count) for row in type_rows
        ],
        registrations_by_region=[
            RegistrationRegionBreakdown(region_name=row.region_name, count=row.count)
            for row in region_rows
        ],
        top_opportunities=[
            TopOpportunityOut(
                opportunity_id=row.opportunity_id,
                title=row.title,
                type=row.type,
                region_name=row.region_name,
                registrations_count=row.registrations_count,
            )
            for row in top_rows
        ],
        registrations_last_7_days=registrations_last_7_days,
        registrations_last_30_days=registrations_last_30_days,
        average_registrations_per_opportunity=average_registrations_per_opportunity,
    )


@router.get("/registrations", response_model=AdminRegistrationListOut)
def list_admin_registrations(
    opportunity_id: int | None = None,
    type: str | None = None,
    q: str = "",
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminRegistrationListOut:
    limit, offset = _normalize_pagination(limit, offset)

    query = (
        db.query(
            Registration.id,
            Registration.created_at,
            User.id.label("user_id"),
            User.full_name.label("user_name"),
            User.email.label("user_email"),
            Opportunity.id.label("opportunity_id"),
            Opportunity.title.label("opportunity_title"),
            Opportunity.type.label("opportunity_type"),
            Opportunity.region_name.label("region_name"),
            Registration.first_name,
            Registration.last_name,
            Registration.age,
            Registration.phone_number,
            Registration.telegram_username,
        )
        .join(User, User.id == Registration.user_id)
        .join(Opportunity, Opportunity.id == Registration.opportunity_id)
    )

    if opportunity_id is not None:
        query = query.filter(Registration.opportunity_id == opportunity_id)

    if type is not None and type.strip():
        query = query.filter(Opportunity.type == type.strip().lower())

    search = q.strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(pattern),
                User.email.ilike(pattern),
                Opportunity.title.ilike(pattern),
            )
        )

    total = query.count()
    rows = (
        query.order_by(Registration.created_at.desc(), Registration.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [
        AdminRegistrationItemOut(
            id=row.id,
            created_at=row.created_at,
            user_id=row.user_id,
            user_name=row.user_name,
            user_email=row.user_email,
            opportunity_id=row.opportunity_id,
            opportunity_title=row.opportunity_title,
            opportunity_type=row.opportunity_type,
            region_name=row.region_name,
            first_name=row.first_name,
            last_name=row.last_name,
            age=row.age,
            phone_number=row.phone_number,
            telegram_username=row.telegram_username,
        )
        for row in rows
    ]

    return AdminRegistrationListOut(items=items, total=total, limit=limit, offset=offset)


@router.get("/registrations/{registration_id}", response_model=AdminRegistrationDetailOut)
def get_admin_registration(
    registration_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminRegistrationDetailOut:
    row = (
        db.query(
            Registration.id,
            Registration.created_at,
            User.id.label("user_id"),
            User.full_name.label("user_name"),
            User.email.label("user_email"),
            Opportunity.id.label("opportunity_id"),
            Opportunity.title.label("opportunity_title"),
            Opportunity.type.label("opportunity_type"),
            Opportunity.region_name.label("region_name"),
            Registration.first_name,
            Registration.last_name,
            Registration.age,
            Registration.phone_number,
            Registration.telegram_username,
        )
        .join(User, User.id == Registration.user_id)
        .join(Opportunity, Opportunity.id == Registration.opportunity_id)
        .filter(Registration.id == registration_id)
        .first()
    )

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")

    return AdminRegistrationDetailOut(
        id=row.id,
        created_at=row.created_at,
        user_id=row.user_id,
        user_name=row.user_name,
        user_email=row.user_email,
        opportunity_id=row.opportunity_id,
        opportunity_title=row.opportunity_title,
        opportunity_type=row.opportunity_type,
        region_name=row.region_name,
        first_name=row.first_name,
        last_name=row.last_name,
        age=row.age,
        phone_number=row.phone_number,
        telegram_username=row.telegram_username,
    )


@router.put("/registrations/{registration_id}", response_model=AdminRegistrationDetailOut)
def update_admin_registration(
    registration_id: int,
    payload: AdminRegistrationUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminRegistrationDetailOut:
    registration = db.get(Registration, registration_id)
    if registration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")

    registration.first_name = payload.first_name.strip()
    registration.last_name = payload.last_name.strip()
    registration.age = payload.age
    registration.phone_number = payload.phone_number.strip()
    registration.telegram_username = payload.telegram_username.strip().lstrip("@")

    db.commit()

    return get_admin_registration(registration_id=registration_id, db=db)


@router.delete("/registrations/{registration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_registration(
    registration_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> None:
    registration = db.get(Registration, registration_id)
    if registration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found")

    db.delete(registration)
    db.commit()


@router.get("/opportunities", response_model=AdminOpportunityListOut)
def list_admin_opportunities(
    q: str = "",
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminOpportunityListOut:
    limit, offset = _normalize_pagination(limit, offset)

    query = db.query(Opportunity)
    search = q.strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Opportunity.title.ilike(pattern),
                Opportunity.description.ilike(pattern),
                Opportunity.region_name.ilike(pattern),
                Opportunity.type.ilike(pattern),
            )
        )

    total = query.count()
    items = query.order_by(Opportunity.id.desc()).offset(offset).limit(limit).all()
    return AdminOpportunityListOut(items=items, total=total, limit=limit, offset=offset)


@router.post("/opportunities", response_model=OpportunityOut, status_code=status.HTTP_201_CREATED)
def create_admin_opportunity(
    payload: OpportunityCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> OpportunityOut:
    opportunity = Opportunity(
        title=payload.title.strip(),
        description=payload.description.strip(),
        type=payload.type.strip(),
        region_name=payload.region_name.strip(),
    )
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    return opportunity


@router.put("/opportunities/{opportunity_id}", response_model=OpportunityOut)
def update_admin_opportunity(
    opportunity_id: int,
    payload: OpportunityUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> OpportunityOut:
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")

    opportunity.title = payload.title.strip()
    opportunity.description = payload.description.strip()
    opportunity.type = payload.type.strip()
    opportunity.region_name = payload.region_name.strip()

    db.commit()
    db.refresh(opportunity)
    return opportunity


@router.delete("/opportunities/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> None:
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")

    db.query(Registration).filter(Registration.opportunity_id == opportunity_id).delete()
    db.delete(opportunity)
    db.commit()


@router.get("/users", response_model=AdminUserListOut)
def list_admin_users(
    q: str = "",
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminUserListOut:
    limit, offset = _normalize_pagination(limit, offset)

    query = (
        db.query(
            User.id,
            User.full_name,
            User.email,
            User.auth_provider,
            User.avatar_url,
            User.created_at,
            User.last_login_at,
            func.count(Registration.id).label("registrations_count"),
        )
        .outerjoin(Registration, Registration.user_id == User.id)
        .group_by(User.id)
    )

    search = q.strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(User.full_name.ilike(pattern), User.email.ilike(pattern)))

    total = query.count()
    rows = query.order_by(User.created_at.desc(), User.id.desc()).offset(offset).limit(limit).all()

    items = [
        AdminUserItemOut(
            id=row.id,
            full_name=row.full_name,
            email=row.email,
            auth_provider=row.auth_provider,
            avatar_url=row.avatar_url,
            created_at=row.created_at,
            last_login_at=row.last_login_at,
            registrations_count=row.registrations_count,
            is_admin=is_admin_email(row.email),
        )
        for row in rows
    ]

    return AdminUserListOut(items=items, total=total, limit=limit, offset=offset)


@router.get("/users/{user_id}", response_model=AdminUserDetailOut)
def get_admin_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminUserDetailOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    registrations = (
        db.query(
            Registration.id.label("registration_id"),
            Registration.created_at,
            Opportunity.id.label("opportunity_id"),
            Opportunity.title.label("opportunity_title"),
            Opportunity.type.label("opportunity_type"),
            Opportunity.region_name.label("region_name"),
        )
        .join(Opportunity, Opportunity.id == Registration.opportunity_id)
        .filter(Registration.user_id == user.id)
        .order_by(Registration.created_at.desc(), Registration.id.desc())
        .all()
    )

    return AdminUserDetailOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        auth_provider=user.auth_provider,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        registrations_count=len(registrations),
        is_admin=is_admin_email(user.email),
        registrations=[
            AdminUserRegistrationOut(
                registration_id=row.registration_id,
                created_at=row.created_at,
                opportunity_id=row.opportunity_id,
                opportunity_title=row.opportunity_title,
                opportunity_type=row.opportunity_type,
                region_name=row.region_name,
            )
            for row in registrations
        ],
    )
