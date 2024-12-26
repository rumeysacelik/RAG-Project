from sqlalchemy import Column, Integer, String, DateTime, Float
import datetime
# from db import Base
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class RequestLog(Base):
    __tablename__ = "request_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request = Column(String, nullable=False)
    response = Column(String, nullable=False)
    status_code = Column(Integer, nullable=False)
    duration = Column(Float, nullable=False)
    log_level = Column(String, nullable=False)
    created_date = Column(DateTime, default=datetime.datetime.utcnow)