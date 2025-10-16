from sqlalchemy import (
    Column, Integer, String, Boolean, Text, 
    ForeignKey, DateTime, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
from datetime import datetime, timezone
from dataflow.db import Base
from enum import Enum

class EnvironmentAttributes(Base):
    """
    Shared columns between Environment and ArchivedEnvironment.
    """
    __abstract__ = True 

    name = Column(String, nullable=False)
    url = Column(String)
    enabled = Column(Boolean, default=True, server_default='true')
    version = Column(String, default=0, server_default='0')
    is_latest = Column(Boolean, default=True, server_default='true')
    base_env_id = Column(Integer, default=None)
    short_name = Column(String(5))
    status = Column(String, default="Saved", server_default="Saved")
    icon = Column(String)
    py_version = Column(String)
    r_version = Column(String)
    pip_libraries = Column(Text)
    conda_libraries = Column(Text)
    r_requirements = Column(Text)
    created_date = Column(DateTime, server_default=func.now())
    created_by = Column(String)
    org_id = Column(Integer, ForeignKey('ORGANIZATION.id'))

class Environment(EnvironmentAttributes): 
    __tablename__ = 'ENVIRONMENT'
    __table_args__ = (UniqueConstraint('short_name', 'org_id', name='_env_short_name_org_uc'),)
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Relationships
    organization = relationship("Organization", back_populates="environments")
    archived_versions = relationship("ArchivedEnvironment", back_populates="original_environment")

class ArchivedEnvironment(EnvironmentAttributes):
    __tablename__ = 'ARCHIVED_ENVIRONMENT'

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_env_id = Column(Integer, ForeignKey('ENVIRONMENT.id', ondelete='CASCADE'))

    # Relationship with Environment
    original_environment = relationship("Environment", back_populates="archived_versions")

class JobLogs(Base):
    __tablename__ = "JOB_LOG"
    __table_args__ = (UniqueConstraint('log_file_name', 'org_id', name='_job_log_file_org_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    log_file_name = Column(String, nullable=False)
    log_file_location = Column(String, nullable=False)
    status = Column(String)
    created_by = Column(String)
    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete='CASCADE'))


class LocalEnvironment(Base):
    __tablename__ = "LOCAL_ENVIRONMENT"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    user_name = Column(String, ForeignKey('USER.user_name', ondelete='CASCADE'), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete='CASCADE'), nullable=False, index=True)
    py_version = Column(String)
    pip_libraries = Column(Text)
    conda_libraries = Column(Text)
    status = Column(String, default="Created", server_default="Created")
    cloned_from = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    need_refresh = Column(Boolean, default=False, server_default='false')

class EnvType(str, Enum):
    dataflow = "dataflow"
    local = "local"

class PipSource(Base):
    __tablename__ = "PIP_SOURCE"

    id = Column(Integer, primary_key=True, autoincrement=True)

    org_id = Column(Integer, ForeignKey("ORGANIZATION.id", ondelete="CASCADE"), nullable=False, index=True)
    user_name = Column(String, ForeignKey("USER.user_name", ondelete="CASCADE"), nullable=True, index=True)

    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    is_index = Column(Boolean, default=False, nullable=False, server_default='false')

    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("org_id", "name", "user_name", name="uq_pip_source_per_user_org"),
        CheckConstraint("NOT (is_index = TRUE AND user_name IS NOT NULL)", name="check_no_user_index_url"),
    )

    @classmethod
    def get_org_sources(cls, session: Session, org_id: int):
        """
        Returns all sources for the given org (org-level).
        """
        return session.query(cls).filter(
            cls.org_id == org_id,
            cls.user_name == None
        ).all()

    @classmethod
    def get_user_sources(cls, session: Session, org_id: int, user_name: str):
        """
        Returns merged sources for a user in an org (org-level + user-level personal sources).
        """
        return session.query(cls).filter(
            cls.org_id == org_id,
            ((cls.user_name == None) | (cls.user_name == user_name))
        ).all()

