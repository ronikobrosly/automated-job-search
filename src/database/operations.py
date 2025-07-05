"""Database operations for job management and querying."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from .connection import get_db_session
from .models import Job

class JobOperations:
    """Database operations for job management and querying."""
    
    @staticmethod
    def create_job(session: Session, job_data: Dict) -> Job:
        """Create a new job record.
        
        Args:
            session: Database session.
            job_data: Dictionary containing job information.
            
        Returns:
            Job: The created job instance.
        """
        job = Job(**job_data)
        if not job.content_hash:
            job.content_hash = job.generate_content_hash()
        
        session.add(job)
        session.commit()
        session.refresh(job)
        return job
    
    @staticmethod
    def get_job_by_id_and_website(session: Session, job_id: str, job_website: str) -> Optional[Job]:
        """Get job by job_id and website combination.
        
        Args:
            session: Database session.
            job_id: Unique job identifier.
            job_website: Name of the job website.
            
        Returns:
            Job: The job instance if found, None otherwise.
        """
        return session.query(Job).filter(
            and_(Job.job_id == job_id, Job.job_website == job_website)
        ).first()
    
    @staticmethod
    def update_job_last_seen(session: Session, job: Job) -> Job:
        """Update the last_seen timestamp for a job.
        
        Args:
            session: Database session.
            job: Job instance to update.
            
        Returns:
            Job: The updated job instance.
        """
        job.last_seen = datetime.now()
        job.updated_at = datetime.now()
        session.commit()
        session.refresh(job)
        return job
    
    @staticmethod
    def get_new_jobs_since(session: Session, since: datetime) -> List[Job]:
        """Get jobs that are new since the specified datetime.
        
        Args:
            session: Database session.
            since: Datetime to filter jobs from.
            
        Returns:
            List[Job]: List of new jobs since the specified time.
        """
        return session.query(Job).filter(
            and_(Job.is_new == True, Job.when_scraped >= since)
        ).all()
    
    @staticmethod
    def get_jobs_by_website(session: Session, website: str, limit: Optional[int] = None) -> List[Job]:
        """Get jobs from a specific website.
        
        Args:
            session: Database session.
            website: Name of the website to filter by.
            limit: Maximum number of jobs to return.
            
        Returns:
            List[Job]: List of jobs from the specified website.
        """
        query = session.query(Job).filter(Job.job_website == website)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def mark_jobs_as_not_new(session: Session, job_ids: List[int]) -> None:
        """Mark jobs as no longer new.
        
        Args:
            session: Database session.
            job_ids: List of job IDs to update.
        """
        session.query(Job).filter(Job.id.in_(job_ids)).update(
            {Job.is_new: False}, synchronize_session=False
        )
        session.commit()
    
    @staticmethod
    def mark_job_as_relevant(session: Session, job_id: int, is_relevant: bool = True) -> Optional[Job]:
        """Mark a job as relevant or not relevant.
        
        Args:
            session: Database session.
            job_id: ID of the job to update.
            is_relevant: Whether the job is relevant.
            
        Returns:
            Job: The updated job instance if found, None otherwise.
        """
        job = session.query(Job).filter(Job.id == job_id).first()
        if job:
            job.is_relevant = is_relevant
            job.updated_at = datetime.now()
            session.commit()
            session.refresh(job)
            return job
        return None
    
    @staticmethod
    def mark_job_as_processed(session: Session, job_id: int, is_processed: bool = True) -> Optional[Job]:
        """Mark a job as processed (documents generated).
        
        Args:
            session: Database session.
            job_id: ID of the job to update.
            is_processed: Whether the job has been processed.
            
        Returns:
            Job: The updated job instance if found, None otherwise.
        """
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
        """Get jobs that are relevant but not yet processed.
        
        Args:
            session: Database session.
            
        Returns:
            List[Job]: List of relevant, unprocessed jobs.
        """
        return session.query(Job).filter(
            and_(Job.is_relevant == True, Job.is_processed == False)
        ).all()
    
    @staticmethod
    def cleanup_old_jobs(session: Session, days_old: int = 30) -> int:
        """Remove jobs older than specified days that are not relevant.
        
        Args:
            session: Database session.
            days_old: Number of days after which to remove old jobs.
            
        Returns:
            int: Number of jobs deleted.
        """
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
    def get_job_stats(session: Session) -> Dict:
        """Get statistics about jobs in the database.
        
        Args:
            session: Database session.
            
        Returns:
            Dict: Dictionary containing job statistics.
        """
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