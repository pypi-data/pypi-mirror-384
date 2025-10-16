from sqlalchemy import Column , Integer, String, Boolean, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from dataflow.db import Base
import enum
from dataflow.models.environment import EnvType

class OrganizationUser(Base):
    """
    Association Table between USER, ROLE, and ORGANIZATION
    """
    __tablename__ = "ORGANIZATION_USER"
    __table_args__ = (UniqueConstraint('org_id', 'user_id', name='uq_org_user'),)

    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete="CASCADE"), primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('USER.user_id', ondelete="CASCADE"), primary_key=True, nullable=False)
    role_id = Column(Integer, ForeignKey('ROLE.id', ondelete="SET NULL"), nullable=False)
    active_env_short_name = Column(String, nullable=True)
    active_env_type = Column(Enum(EnvType), nullable=True)
    active_server_id = Column(Integer, ForeignKey('CUSTOM_SERVER.id', ondelete="SET NULL"))
    show_server_page = Column(Boolean, default = True, server_default='true')
    monthly_allocation = Column(Integer, nullable=True, default=0, server_default='0')

    # Relationships
    user = relationship("User", back_populates="org_user_assocs")
    role = relationship("Role", back_populates="org_user_assocs")
    organization = relationship("Organization", back_populates="org_user_assocs")

class OrganizationServer(Base):
    __tablename__ = "ORGANIZATION_SERVER"

    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete="CASCADE"), primary_key=True, nullable=False)
    server_id = Column(Integer, ForeignKey('SERVER_CONFIG.id', ondelete="CASCADE"), primary_key=True, nullable=False)

class OrganizationAppType(Base):
    __tablename__ = "ORGANIZATION_APP_TYPE"

    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete="CASCADE"), primary_key=True, nullable=False)
    app_type_id = Column(Integer, ForeignKey('APP_TYPE.id', ondelete="CASCADE"), primary_key=True, nullable=False)