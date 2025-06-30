from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import hashlib

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(255), nullable=False)
    company_name = Column(String(255))
    role_title = Column(String(255), nullable=False)
    job_website = Column(String(100), nullable=False)
    job_url = Column(Text)
    location = Column(String(255))
    salary_range = Column(String(100))
    job_description = Column(Text)
    requirements = Column(Text)
    when_scraped = Column(DateTime, nullable=False, default=func.now())
    last_seen = Column(DateTime, nullable=False, default=func.now())
    is_new = Column(Boolean, default=True)
    is_relevant = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False)
    content_hash = Column(String(64))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('job_id', 'job_website', name='unique_job_per_site'),
        Index('idx_job_website', 'job_website'),
        Index('idx_when_scraped', 'when_scraped'),
        Index('idx_is_new', 'is_new'),
        Index('idx_is_relevant', 'is_relevant'),
        Index('idx_is_processed', 'is_processed'),
        Index('idx_last_seen', 'last_seen'),
    )
    
    def generate_content_hash(self):
        """Generate hash of key content fields to detect changes"""
        content = f"{self.role_title}|{self.company_name}|{self.location}|{self.salary_range}|{self.job_description}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def __repr__(self):
        return f"<Job(id={self.id}, role_title='{self.role_title}', company_name='{self.company_name}', job_website='{self.job_website}')>"