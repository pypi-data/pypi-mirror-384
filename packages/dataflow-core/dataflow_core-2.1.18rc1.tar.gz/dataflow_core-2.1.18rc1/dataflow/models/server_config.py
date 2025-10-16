from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB 
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from dataflow.db import Base

class ServerConfig(Base):
    __tablename__ = "SERVER_CONFIG"

    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String, nullable=False, unique=True)
    slug = Column(String, unique=True, nullable=False)
    price = Column(String, nullable=False)
    ram = Column(String, nullable=False)
    cpu = Column(String, nullable=False)
    gpu = Column(String)
    default = Column(Boolean, default=False, server_default='false')
    tags = Column(JSONB, default=func.json([]), server_default=text("'[]'::jsonb"))
    description = Column(Text, nullable=True)
    kubespawner_override = Column(JSONB, default=func.json({}), server_default=text("'{}'::jsonb"))

    # Relationships
    organizations = relationship("Organization", secondary="ORGANIZATION_SERVER", back_populates="servers")

class CustomServerConfig(Base):
    __tablename__ = "CUSTOM_SERVER"

    id = Column(Integer, primary_key=True, autoincrement=True)
    base_server_id = Column(Integer, ForeignKey(ServerConfig.id, ondelete="CASCADE"), nullable=False)
    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete="CASCADE"), nullable=False)
    display_name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Relationship to the server_config table
    server_config = relationship(ServerConfig)
    organization = relationship("Organization", back_populates="custom_servers")
    roles = relationship("Role", secondary="ROLE_SERVER", back_populates="servers")