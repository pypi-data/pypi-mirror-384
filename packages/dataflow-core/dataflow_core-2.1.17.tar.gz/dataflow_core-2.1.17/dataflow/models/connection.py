from sqlalchemy import Column, String, Integer, Boolean, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.sql import func
from dataflow.db import Base

class Connection(Base):
    """
    Database model for storing non-sensitive connection metadata
    """
    __tablename__ = "CONNECTION"

    id = Column(Integer, primary_key=True, index=True)
    conn_id = Column(String, index=True, nullable=False)
    org_id = Column(Integer, ForeignKey("ORGANIZATION.id"), index=True, nullable=False)
    description = Column(String, nullable=True)
    conn_type = Column(String, nullable=False)
    runtime = Column(String, nullable=True)
    slug = Column(String, nullable=True)
    status = Column(Boolean, default=False, server_default='false')
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True, server_default='true')
    
    __table_args__ = (
        UniqueConstraint('conn_id', 'org_id', 'runtime', 'slug', 'is_active', 'created_by', name='uq_active_conn_with_runtime_slug'),
    )