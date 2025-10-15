"""models.py"""
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from dataflow.db import Base

class Team(Base):
    """
    Table TEAM
    """

    __tablename__='TEAM'
    __table_args__ = (
        UniqueConstraint('team_name', 'org_id', name='uc_team_name_org_id'),
    )

    team_id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    team_name = Column(String, nullable=False)
    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete="CASCADE"), nullable=False)
    description = Column(String, nullable=True)

    # relationships
    users = relationship("User", secondary="USER_TEAM", back_populates="teams")
    organization = relationship("Organization")