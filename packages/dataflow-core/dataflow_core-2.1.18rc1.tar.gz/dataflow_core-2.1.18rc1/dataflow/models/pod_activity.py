from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from dataflow.db import Base

class PodActivity(Base):
    """Model for tracking active JupyterHub pod sessions"""
    __tablename__ = 'POD_ACTIVITY'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, ForeignKey('USER.user_name', ondelete="SET NULL"), nullable=True, index=True)
    pod_name = Column(String, nullable=False, unique=True, index=True)
    namespace = Column(String, nullable=False, index=True)
    start_time = Column(DateTime(timezone=True))
    stop_time = Column(DateTime(timezone=True))
    status = Column(String, nullable=False, index=True)
    instance_type = Column(String, index=True)
    node_name = Column(String)