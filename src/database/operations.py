from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from .models import Job
from .connection import get_db_session

class JobOperations:
    """Database operations for job management"""
    
    @staticmethod
    def create_job(session: Session, job_data: dict) -> Job:
        """Create a new job record"""
        job = Job(**job_data)
        if not job.content_hash:
            job.content_hash = job.generate_content_hash()
        
        session.add(job)
        session.commit()
        session.refresh(job)
        return job
    
    @staticmethod
    def get_job_by_id_and_website(session: Session, job_id: str, job_website: str) -> Optional[Job]:
        """Get job by job_id and website combination"""
        return session.query(Job).filter(
            and_(Job.job_id == job_id, Job.job_website == job_website)
        ).first()
    
    @staticmethod
    def update_job_last_seen(session: Session, job: Job) -> Job:
        """Update the last_seen timestamp for a job"""
        job.last_seen = datetime.now()
        job.updated_at = datetime.now()
        session.commit()
        session.refresh(job)
        return job
    
    @staticmethod
    def get_new_jobs_since(session: Session, since: datetime) -> List[Job]:
        """Get jobs that are new since the specified datetime"""
        return session.query(Job).filter(
            and_(Job.is_new == True, Job.when_scraped >= since)
        ).all()
    
    @staticmethod
    def get_jobs_by_website(session: Session, website: str, limit: int = None) -> List[Job]:
        """Get jobs from a specific website"""
        query = session.query(Job).filter(Job.job_website == website)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def mark_jobs_as_not_new(session: Session, job_ids: List[int]):
        """Mark jobs as no longer new"""
        session.query(Job).filter(Job.id.in_(job_ids)).update(
            {Job.is_new: False}, synchronize_session=False
        )
        session.commit()
    
    @staticmethod
    def mark_job_as_relevant(session: Session, job_id: int, is_relevant: bool = True):
        """Mark a job as relevant or not relevant"""
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.is_relevant = is_relevant
            job.updated_at = datetime.now()
            session.commit()
            session.refresh(job)
            return job
        return None
    
    @staticmethod
    def mark_job_as_processed(session: Session, job_id: int, is_processed: bool = True):
        """Mark a job as processed (documents generated)"""
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.is_processed = is_processed
            job.updated_at = datetime.now()
            session.commit()
            session.refresh(job)
            return job
        return None
    
    @staticmethod
    def get_unprocessed_relevant_jobs(session: Session) -> List[Job]:
        """Get jobs that are relevant but not yet processed"""
        return session.query(Job).filter(
            and_(Job.is_relevant == True, Job.is_processed == False)
        ).all()
    
    @staticmethod
    def cleanup_old_jobs(session: Session, days_old: int = 30):
        """Remove jobs older than specified days that are not relevant"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_count = session.query(Job).filter(
            and_(
                Job.when_scraped < cutoff_date,
                Job.is_relevant == False
            )
        ).delete()
        session.commit()
        return deleted_count
    
    @staticmethod
    def get_job_stats(session: Session) -> dict:
        """Get statistics about jobs in the database"""
        total_jobs = session.query(Job).count()
        new_jobs = session.query(Job).filter(Job.is_new == True).count()
        relevant_jobs = session.query(Job).filter(Job.is_relevant == True).count()
        processed_jobs = session.query(Job).filter(Job.is_processed == True).count()
        
        websites = session.query(Job.job_website, func.count(Job.id)).group_by(Job.job_website).all()
        
        return {
            'total_jobs': total_jobs,
            'new_jobs': new_jobs,
            'relevant_jobs': relevant_jobs,
            'processed_jobs': processed_jobs,
            'jobs_by_website': dict(websites)
        }