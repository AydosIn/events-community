from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthIn(BaseModel):
    credential: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    auth_provider: str | None = None
    avatar_url: str | None = None
    is_admin: bool = False

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    full_name: str
    is_admin: bool = False


class RegistrationCreate(BaseModel):
    opportunity_id: int
    first_name: str
    last_name: str
    age: int
    phone_number: str
    telegram_username: str


class OpportunityOut(BaseModel):
    id: int
    title: str
    description: str
    type: str
    region_name: str

    class Config:
        from_attributes = True


class RegistrationOut(BaseModel):
    id: int
    user_id: int
    opportunity_id: int
    first_name: str
    last_name: str
    age: int
    phone_number: str
    telegram_username: str

    class Config:
        from_attributes = True


class RegisteredIdsOut(BaseModel):
    registered_ids: list[int]


class OpportunityCreate(BaseModel):
    title: str
    description: str
    type: str
    region_name: str


class OpportunityUpdate(BaseModel):
    title: str
    description: str
    type: str
    region_name: str


class AdminOverviewOut(BaseModel):
    users_count: int
    opportunities_count: int
    registrations_count: int


class RegistrationTypeBreakdown(BaseModel):
    type: str
    count: int


class RegistrationRegionBreakdown(BaseModel):
    region_name: str
    count: int


class TopOpportunityOut(BaseModel):
    opportunity_id: int
    title: str
    type: str
    region_name: str
    registrations_count: int


class AdminAnalyticsOut(BaseModel):
    registrations_by_type: list[RegistrationTypeBreakdown]
    registrations_by_region: list[RegistrationRegionBreakdown]
    top_opportunities: list[TopOpportunityOut]
    registrations_last_7_days: int
    registrations_last_30_days: int
    average_registrations_per_opportunity: float


class AdminListMeta(BaseModel):
    total: int
    limit: int
    offset: int


class AdminOpportunityListOut(BaseModel):
    items: list[OpportunityOut]
    total: int
    limit: int
    offset: int


class AdminRegistrationItemOut(BaseModel):
    id: int
    created_at: datetime | None = None
    user_id: int
    user_name: str
    user_email: EmailStr
    opportunity_id: int
    opportunity_title: str
    opportunity_type: str
    region_name: str
    first_name: str
    last_name: str
    age: int
    phone_number: str
    telegram_username: str


class AdminRegistrationUpdate(BaseModel):
    first_name: str
    last_name: str
    age: int
    phone_number: str
    telegram_username: str


class AdminRegistrationDetailOut(BaseModel):
    id: int
    created_at: datetime | None = None
    user_id: int
    user_name: str
    user_email: EmailStr
    opportunity_id: int
    opportunity_title: str
    opportunity_type: str
    region_name: str
    first_name: str
    last_name: str
    age: int
    phone_number: str
    telegram_username: str


class AdminRegistrationListOut(BaseModel):
    items: list[AdminRegistrationItemOut]
    total: int
    limit: int
    offset: int


class AdminUserItemOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    auth_provider: str | None = None
    avatar_url: str | None = None
    created_at: datetime | None = None
    registrations_count: int
    is_admin: bool = False


class AdminUserListOut(BaseModel):
    items: list[AdminUserItemOut]
    total: int
    limit: int
    offset: int


class AdminUserRegistrationOut(BaseModel):
    registration_id: int
    created_at: datetime | None = None
    opportunity_id: int
    opportunity_title: str
    opportunity_type: str
    region_name: str


class AdminUserDetailOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    auth_provider: str | None = None
    avatar_url: str | None = None
    created_at: datetime | None = None
    registrations_count: int
    is_admin: bool = False
    registrations: list[AdminUserRegistrationOut]
