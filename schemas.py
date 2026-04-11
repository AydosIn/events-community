from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    full_name: str


class RegistrationCreate(BaseModel):
    opportunity_id: int


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

    class Config:
        from_attributes = True


class RegisteredIdsOut(BaseModel):
    registered_ids: list[int]
