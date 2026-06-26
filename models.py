from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=True)
    google_sub = Column(String, nullable=True, unique=True, index=True)
    auth_provider = Column(String, nullable=False, server_default="local", default="local")
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    type = Column(String, nullable=False)
    region_name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class Registration(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    phone_number = Column(String, nullable=False)
    telegram_username = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
