from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Tick(Base):
    __tablename__ = 'ticks'
    id = Column(Integer, primary_key=True)
    ticker = Column(String)
    ts = Column(DateTime, default=datetime.utcnow)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)

class Fundamental(Base):
    __tablename__ = 'fundamentals'
    id = Column(Integer, primary_key=True)
    ticker = Column(String)
    ts = Column(DateTime, default=datetime.utcnow)
    pe = Column(Float)
    pb = Column(Float)
    roe = Column(Float)
    market_cap = Column(BigInteger)

class News(Base):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True)
    ticker = Column(String)
    ts = Column(DateTime, default=datetime.utcnow)
    source = Column(String)
    title = Column(String)
    url = Column(String)
    sentiment = Column(Float)

# SQLite database
DATABASE_URL = "sqlite:///stock_data.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initializes the database tables.
    """
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Dependency to get DB session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_tick(db, tick_data: dict):
    """
    Saves a tick record to the database.
    """
    tick = Tick(**tick_data)
    db.add(tick)
    db.commit()
    db.refresh(tick)
    return tick
