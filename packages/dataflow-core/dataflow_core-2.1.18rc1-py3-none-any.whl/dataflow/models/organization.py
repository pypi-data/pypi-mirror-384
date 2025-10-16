from sqlalchemy import (
    Column, Integer, String, Enum, DateTime, ForeignKey, Index, text
)
import uuid, enum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from dataflow.db import Base


class Organization(Base):
    """
    Organization model for the database.
    """
    __tablename__ = "ORGANIZATION"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, unique=True, server_default=text("gen_random_uuid()"))
    name = Column(String(255), nullable=False, unique=True)
    invite_code = Column(String(64), nullable=False, unique=True)
    email_domain = Column(String(255), nullable=False, unique=True)
    spark_enabled_zones = Column(JSONB, default=func.json([]), server_default=text("'[]'::jsonb"))  # List of zone IDs where Spark is enabled
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())

    # Association object link
    org_user_assocs = relationship("OrganizationUser", back_populates="organization", cascade="all, delete-orphan")
    custom_servers = relationship("CustomServerConfig")
    onboarding_requests = relationship("UserOnboarding", back_populates="organization", cascade="all, delete-orphan")
    servers = relationship("ServerConfig", secondary="ORGANIZATION_SERVER", back_populates="organizations")
    apps = relationship("AppType", secondary="ORGANIZATION_APP_TYPE", back_populates="organizations")
    roles = relationship("Role", cascade="all, delete-orphan")
    environments = relationship("Environment", back_populates="organization")

class OnboardingStatus(enum.Enum):
    pending = 'pending'
    rejected = 'rejected'
    accepted = 'accepted'

class OrganizationOnboarding(Base):
    __tablename__ = 'ORGANIZATION_ONBOARDING'
    # This prevents an org from having more than one active ('pending' or 'accepted') application
    # while allowing multiple 'rejected' entries.
    __table_args__ = (
        Index(
            'idx_pending_org_application',
            'name',
            unique=True,
            postgresql_where=Column('status').in_([
                OnboardingStatus.pending.value,
                OnboardingStatus.accepted.value
            ])
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    domain = Column(String(255), nullable=True)
    no_of_employees = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)

    admin_first_name = Column(String(100), nullable=False)
    admin_last_name = Column(String(100), nullable=True)
    admin_designation = Column(String(100), nullable=False)
    admin_email = Column(String(255), nullable=False, unique=True)
    admin_username = Column(String(100), nullable=False, unique=True)
    admin_password = Column(String(255), nullable=False)

    discovery_source = Column(String(255), nullable=True)
    additional_info = Column(String(1000), nullable=True)
    size_of_data = Column(String(100), nullable=True)

    user_id = Column(Integer, ForeignKey('USER.user_id'), nullable=False)
    status = Column(Enum(OnboardingStatus), default=OnboardingStatus.pending, nullable=False)

    user = relationship("User", back_populates="organization_onboarding")