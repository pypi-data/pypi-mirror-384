from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from dataflow.db import Base

class AppType(Base):
    __tablename__ = "APP_TYPE"
    
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    code_based = Column(Boolean, nullable=False)
    studio = Column(Boolean, nullable=False, default=False, server_default='false')
    runtime = Column(Boolean, nullable=False, default=False, server_default='false')

    organizations = relationship("Organization", secondary="ORGANIZATION_APP_TYPE", back_populates="apps")