from sqlalchemy import Boolean, Column, Integer, String, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class ThirdPartyToken(Base):
    __tablename__ = "third_party_tokens"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String)
    refresh_token = Column(String)
    website = Column(String, default='fyers', unique=True)


class SymbolMaster(Base):
    __tablename__ = "symbol_master"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    exchange = Column(String, index=True)
    is_active = Column(Boolean, default=True)

    symbol_history = relationship("SymbolHistory", back_populates="symbol_master")


class SymbolHistory(Base):
    __tablename__ = "symbol_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    symbol_master_id = Column(Integer, ForeignKey("symbol_master.id"), index=True)
    open = Column(Float, index=True)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    
    symbol_master = relationship("SymbolMaster", back_populates="symbol_history")

    UniqueConstraint('timestamp', 'symbol_master_id', name='unique_timestamp_symbol_master_id')