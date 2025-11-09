# models/global_ban.py
from sqlalchemy import Column, BigInteger, String, DateTime
from datetime import datetime
from utils.database import Base

class GlobalBan(Base):
    __tablename__ = "global_bans"

    user_id = Column(BigInteger, primary_key=True, index=True)
    reason = Column(String(255), nullable=True)
    banned_by = Column(BigInteger, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)