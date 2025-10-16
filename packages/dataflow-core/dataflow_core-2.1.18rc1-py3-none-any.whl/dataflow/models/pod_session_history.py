from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from dataflow.db import Base

class PodSessionHistory(Base):
    """Model for tracking completed JupyterHub user sessions"""
    __tablename__ = 'POD_SESSION_HISTORY'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, ForeignKey('USER.user_name', ondelete="SET NULL"), nullable=True, index=True)
    pod_name = Column(String, nullable=False, index=True)
    namespace = Column(String, nullable=False, index=True)
    start_time = Column(DateTime(timezone=True))
    stop_time = Column(DateTime(timezone=True), nullable=False)
    session_duration_minutes = Column(Numeric(10, 2))
    instance_type = Column(String, index=True)
    node_name = Column(String)