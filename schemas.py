from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from validators import (
    validate_age,
    validate_full_name,
    validate_opportunity_description,
    validate_opportunity_title,
    validate_opportunity_type,
    validate_password,
    validate_person_name,
    validate_phone_number,
    validate_region_name,
    validate_telegram_username,
)


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, value: str) -> str:
        return validate_full_name(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password(value)


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

    @field_validator("first_name")
    @classmethod
    def check_first_name(cls, value: str) -> str:
        return validate_person_name(value, "First name")

    @field_validator("last_name")
    @classmethod
    def check_last_name(cls, value: str) -> str:
        return validate_person_name(value, "Last name")

    @field_validator("age")
    @classmethod
    def check_age(cls, value: int) -> int:
        return validate_age(value)

    @field_validator("phone_number")
    @classmethod
    def check_phone_number(cls, value: str) -> str:
        return validate_phone_number(value)

    @field_validator("telegram_username")
    @classmethod
    def check_telegram_username(cls, value: str) -> str:
        return validate_telegram_username(value)


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

    @field_validator("title")
    @classmethod
    def check_title(cls, value: str) -> str:
        return validate_opportunity_title(value)

    @field_validator("description")
    @classmethod
    def check_description(cls, value: str) -> str:
        return validate_opportunity_description(value)

    @field_validator("type")
    @classmethod
    def check_type(cls, value: str) -> str:
        return validate_opportunity_type(value)

    @field_validator("region_name")
    @classmethod
    def check_region_name(cls, value: str) -> str:
        return validate_region_name(value)


class OpportunityUpdate(BaseModel):
    title: str
    description: str
    type: str
    region_name: str

    @field_validator("title")
    @classmethod
    def check_title(cls, value: str) -> str:
        return validate_opportunity_title(value)

    @field_validator("description")
    @classmethod
    def check_description(cls, value: str) -> str:
        return validate_opportunity_description(value)

    @field_validator("type")
    @classmethod
    def check_type(cls, value: str) -> str:
        return validate_opportunity_type(value)

    @field_validator("region_name")
    @classmethod
    def check_region_name(cls, value: str) -> str:
        return validate_region_name(value)


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

    @field_validator("first_name")
    @classmethod
    def check_first_name(cls, value: str) -> str:
        return validate_person_name(value, "First name")

    @field_validator("last_name")
    @classmethod
    def check_last_name(cls, value: str) -> str:
        return validate_person_name(value, "Last name")

    @field_validator("age")
    @classmethod
    def check_age(cls, value: int) -> int:
        return validate_age(value)

    @field_validator("phone_number")
    @classmethod
    def check_phone_number(cls, value: str) -> str:
        return validate_phone_number(value)

    @field_validator("telegram_username")
    @classmethod
    def check_telegram_username(cls, value: str) -> str:
        return validate_telegram_username(value)


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
    last_login_at: datetime | None = None
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
    last_login_at: datetime | None = None
    registrations_count: int
    is_admin: bool = False
    registrations: list[AdminUserRegistrationOut]


class AdminCreateIn(BaseModel):
    email: EmailStr


class AdminOut(BaseModel):
    id: int
    full_name: str | None = None
    email: EmailStr
    created_at: datetime | None = None
    user_id: int | None = None

    class Config:
        from_attributes = True


class AdminListOut(BaseModel):
    items: list[AdminOut]
    total: int
