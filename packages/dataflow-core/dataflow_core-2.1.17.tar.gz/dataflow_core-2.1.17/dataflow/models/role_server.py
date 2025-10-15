# models/user_team.py
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from dataflow.db import Base

class RoleServer(Base):
    __tablename__ = 'ROLE_SERVER'
    __table_args__ = (UniqueConstraint('role_id', 'custom_server_id', name='_role_server_uc'),)

    role_id = Column(Integer, ForeignKey('ROLE.id', ondelete="CASCADE"), nullable=False, primary_key=True)
    custom_server_id = Column(Integer, ForeignKey('CUSTOM_SERVER.id', ondelete="CASCADE"), nullable=False, primary_key=True)