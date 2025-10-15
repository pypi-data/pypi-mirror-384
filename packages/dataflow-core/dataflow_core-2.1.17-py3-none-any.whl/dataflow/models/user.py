"""models.py"""
from sqlalchemy import Column, Integer, String, Boolean, LargeBinary, Enum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy import Index
from sqlalchemy.orm import relationship
from dataflow.db import Base
import enum

class User(Base):
    """
    Table USER
    """
    __tablename__ = 'USER'

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_name = Column(String, unique=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    image = Column(LargeBinary)
    image_url = Column(String, nullable=True)
    active = Column(Boolean, nullable=False, default=True, server_default='true')
    password = Column(String, nullable=False)
    active_org_id = Column(Integer, ForeignKey('ORGANIZATION.id'))

    # Relationships
    org_user_assocs = relationship("OrganizationUser", back_populates="user", cascade="all, delete-orphan")
    teams = relationship("Team", secondary="USER_TEAM", back_populates="users")
    onboarding_requests = relationship("UserOnboarding", back_populates="user", cascade="all, delete-orphan")
    organization_onboarding = relationship("OrganizationOnboarding", back_populates="user", cascade="all, delete-orphan")


class OnboardingStatus(enum.Enum):
    pending = 'pending'
    rejected = 'rejected'
    accepted = 'accepted'

class UserOnboarding(Base):
    """
    SQLAlchemy model for the "USER_ONBOARDING" table.
    This table stores user applications to organizations.
    """
    __tablename__ = "USER_ONBOARDING"
    # This prevents a user from having more than one active ('pending' or 'accepted') application
    # for a given organization, while allowing multiple 'rejected' entries.
    __table_args__ = (
        Index(
            'idx_pending_user_org_application',
            'user_id',
            'org_id',
            unique=True,
            postgresql_where=Column('status').in_([
                OnboardingStatus.pending.value,
                OnboardingStatus.accepted.value
            ])
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey("USER.user_id", ondelete="CASCADE"), nullable=False)
    org_id = Column(Integer, ForeignKey("ORGANIZATION.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(OnboardingStatus, name='onboarding_status'), nullable=False, default=OnboardingStatus.pending.value, server_default='pending')
    created_at = Column(DateTime, default=func.now(), nullable=False, server_default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="onboarding_requests")
    organization = relationship("Organization", back_populates="onboarding_requests")