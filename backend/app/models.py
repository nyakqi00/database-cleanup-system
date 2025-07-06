from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import VARCHAR
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class InvalidEmail(Base):
    __tablename__ = "invalid_emails"
    email = Column(String, primary_key=True, index=True)
    brand = Column(String)

class EmailTR(Base):
    __tablename__ = "emails_tr"
    email = Column(String, primary_key=True, index=True)
    card_no = Column(String)
    brand = Column(String)
    name = Column(String)
    phone = Column(String)
    segment = Column(String)

class EmailMFM(Base):
    __tablename__ = "emails_mfm"
    email = Column(String, primary_key=True, index=True)
    card_no = Column(String)
    brand = Column(String)
    name = Column(String)
    phone = Column(String)
    segment = Column(String)

class EmailNYSS(Base):
    __tablename__ = "emails_nyss"
    email = Column(String, primary_key=True, index=True)
    card_no = Column(String)
    brand = Column(String)
    name = Column(String)
    phone = Column(String)
    segment = Column(String)

class MasterEmail(Base):
    __tablename__ = "master_emails"
    email = Column(String, primary_key=True, index=True)
    card_no = Column(String)
    name = Column(String)
    phone = Column(String)
    segment_tr = Column(String)
    segment_mfm = Column(String)
    segment_nyss = Column(String)
    is_tr = Column(Boolean, default=False)
    is_mfm = Column(Boolean, default=False)
    is_nyss = Column(Boolean, default=False)
    last_updated = Column(DateTime)
