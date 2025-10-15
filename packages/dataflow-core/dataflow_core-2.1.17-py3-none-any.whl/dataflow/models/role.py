"""models.py"""
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from dataflow.db import Base
import enum

class BaseRoleField(enum.Enum):
    admin = "admin"
    user = "user"
    applicant = "applicant"

class Role(Base):
    """
    Table ROLE
    """

    __tablename__='ROLE'
    __table_args__ = (
        UniqueConstraint('name', 'org_id', name='uq_role_name_org'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    org_id = Column(Integer, ForeignKey('ORGANIZATION.id'))
    description = Column(String, nullable=True)
    base_role = Column(Enum(BaseRoleField), nullable=False, default=BaseRoleField.user, server_default=BaseRoleField.user.value)

    # Relationships
    role_zone_assocs = relationship("RoleZone", back_populates="role")
    org_user_assocs = relationship("OrganizationUser", back_populates="role", cascade="all, delete-orphan")
    organization = relationship("Organization", back_populates="roles")
    servers = relationship("CustomServerConfig", secondary="ROLE_SERVER", back_populates="roles")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', base_role='{self.base_role}')>"