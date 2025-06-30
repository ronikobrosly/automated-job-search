#!/usr/bin/env python3
"""
Main entry point for the automated job search pipeline.

This module orchestrates the entire job search process:
1. Web scraping of job sites
2. Database storage and deduplication
3. Job relevance analysis and filtering
4. Document generation (resume/cover letter customization)
5. Email reporting with generated documents

Usage:
    python -m src
    python src/__main__.py
"""

import logging
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers import ScraperManager
from src.database import JobOperations, get_db_session

def setup_logging(log_level: str = "INFO"):
    """Set up logging configuration"""
    log_dir = project_root / "logs" / "application"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # File handler
    log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return logging.getLogger("main_pipeline")

def scrape_jobs() -> dict:
    """
    Execute the job scraping phase of the pipeline.
    
    Returns:
        dict: Summary statistics from scraping operation
    """
    logger = logging.getLogger("main_pipeline.scraping")
    logger.info("Starting job scraping phase")
    
    try:
        scraper_manager = ScraperManager()
        scrape_results = scraper_manager.scrape_all_sites()
        
        logger.info(f"Scraping completed successfully. "
                   f"New jobs: {scrape_results['overall_stats']['total_new_jobs']}, "
                   f"Total jobs: {scrape_results['overall_stats']['total_jobs_scraped']}")
        
        return scrape_results
        
    except Exception as e:
        logger.error(f"Job scraping failed: {str(e)}")
        raise

def analyze_job_relevance(new_jobs_count: int) -> dict:
    """
    Analyze scraped jobs for relevance based on configured criteria.
    
    This is a placeholder for the job analysis logic that will:
    - Load user-defined job criteria
    - Score jobs against criteria using NLP/ML techniques
    - Mark relevant jobs in the database
    - Filter out jobs that don't meet minimum relevance threshold
    
    Args:
        new_jobs_count: Number of new jobs to analyze
        
    Returns:
        dict: Analysis results and statistics
    """
    logger = logging.getLogger("main_pipeline.analysis")
    logger.info(f"Starting job relevance analysis for {new_jobs_count} new jobs")
    
    # TODO: Implement job relevance analysis
    # This should include:
    # 1. Load job matching criteria from config
    # 2. Retrieve unprocessed new jobs from database
    # 3. Apply scoring algorithm (keyword matching, ML model, etc.)
    # 4. Update job relevance flags in database
    # 5. Return statistics on relevant jobs found
    
    # Placeholder implementation
    relevant_jobs_found = max(1, new_jobs_count // 10)  # Simulate 10% relevance rate
    
    logger.info(f"Job analysis completed. Found {relevant_jobs_found} relevant jobs")
    
    return {
        'jobs_analyzed': new_jobs_count,
        'relevant_jobs_found': relevant_jobs_found,
        'analysis_criteria_applied': ['keyword_matching', 'location_filter', 'salary_range'],
        'status': 'completed'
    }

def generate_documents(relevant_jobs_count: int) -> dict:
    """
    Generate customized resumes and cover letters for relevant jobs.
    
    This is a placeholder for the document generation logic that will:
    - Load LaTeX templates for resume and cover letter
    - Retrieve relevant jobs from database
    - Customize templates based on job descriptions and requirements
    - Generate PDF documents
    - Store generated documents in data/exports/
    - Update job processing status in database
    
    Args:
        relevant_jobs_count: Number of relevant jobs to process
        
    Returns:
        dict: Document generation results and statistics
    """
    logger = logging.getLogger("main_pipeline.documents")
    logger.info(f"Starting document generation for {relevant_jobs_count} relevant jobs")
    
    # TODO: Implement document generation
    # This should include:
    # 1. Load LaTeX templates from templates/ directory
    # 2. Retrieve relevant, unprocessed jobs from database
    # 3. Extract key information from job descriptions
    # 4. Customize resume template with relevant skills/experience
    # 5. Generate personalized cover letters
    # 6. Compile LaTeX to PDF
    # 7. Save PDFs to data/exports/ with job-specific names
    # 8. Update job processed status in database
    
    # Placeholder implementation
    documents_generated = relevant_jobs_count * 2  # Resume + cover letter per job
    
    logger.info(f"Document generation completed. Generated {documents_generated} documents")
    
    return {
        'relevant_jobs_processed': relevant_jobs_count,
        'documents_generated': documents_generated,
        'resumes_created': relevant_jobs_count,
        'cover_letters_created': relevant_jobs_count,
        'output_directory': str(project_root / 'data' / 'exports'),
        'status': 'completed'
    }

def send_email_report(pipeline_results: dict) -> dict:
    """
    Send email report with pipeline results and generated documents.
    
    This is a placeholder for the email reporting logic that will:
    - Load email configuration (SMTP settings, recipients)
    - Compile pipeline summary report
    - Attach generated PDFs for relevant jobs
    - Send HTML email with job summaries and attachments
    - Log email delivery status
    
    Args:
        pipeline_results: Combined results from all pipeline phases
        
    Returns:
        dict: Email sending results and statistics
    """
    logger = logging.getLogger("main_pipeline.email")
    logger.info("Starting email report generation and sending")
    
    # TODO: Implement email reporting
    # This should include:
    # 1. Load email configuration from config/email/
    # 2. Generate HTML email template with pipeline summary
    # 3. Include job listings table with new relevant jobs
    # 4. Attach generated PDFs (with size limits)
    # 5. Send email via configured SMTP server
    # 6. Handle email delivery errors and retries
    # 7. Log email delivery status
    
    # Placeholder implementation
    new_jobs = pipeline_results.get('scraping', {}).get('overall_stats', {}).get('total_new_jobs', 0)
    relevant_jobs = pipeline_results.get('analysis', {}).get('relevant_jobs_found', 0)
    documents = pipeline_results.get('documents', {}).get('documents_generated', 0)
    
    logger.info(f"Email report sent successfully. "
               f"Summary: {new_jobs} new jobs, {relevant_jobs} relevant, {documents} documents generated")
    
    return {
        'email_sent': True,
        'recipients': ['user@example.com'],  # TODO: Load from config
        'attachments_count': documents,
        'email_size_mb': documents * 0.5,  # Estimate 0.5MB per document
        'delivery_status': 'successful',
        'status': 'completed'
    }

def cleanup_old_data() -> dict:
    """
    Clean up old job data and generated files to manage storage.
    
    Returns:
        dict: Cleanup results and statistics
    """
    logger = logging.getLogger("main_pipeline.cleanup")
    logger.info("Starting cleanup of old data")
    
    try:
        session = next(get_db_session())
        try:
            # Clean up old, non-relevant jobs (older than 30 days)
            deleted_jobs = JobOperations.cleanup_old_jobs(session, days_old=30)
            
            # TODO: Clean up old generated documents
            # TODO: Clean up old log files
            # TODO: Optimize database (VACUUM for SQLite)
            
            logger.info(f"Cleanup completed. Removed {deleted_jobs} old job records")
            
            return {
                'old_jobs_deleted': deleted_jobs,
                'old_documents_deleted': 0,  # TODO: Implement
                'old_logs_deleted': 0,  # TODO: Implement
                'status': 'completed'
            }
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }

def get_database_stats() -> dict:
    """Get current database statistics for reporting"""
    try:
        session = next(get_db_session())
        try:
            stats = JobOperations.get_job_stats(session)
            return stats
        finally:
            session.close()
    except Exception as e:
        return {'error': str(e)}

def main():
    """Main pipeline execution function"""
    parser = argparse.ArgumentParser(description='Automated Job Search Pipeline')
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level')
    parser.add_argument('--skip-scraping', action='store_true',
                       help='Skip scraping phase (useful for testing other phases)')
    parser.add_argument('--skip-analysis', action='store_true',
                       help='Skip job analysis phase')
    parser.add_argument('--skip-documents', action='store_true',
                       help='Skip document generation phase')
    parser.add_argument('--skip-email', action='store_true',
                       help='Skip email reporting phase')
    parser.add_argument('--cleanup-only', action='store_true',
                       help='Only run cleanup, skip main pipeline')
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(args.log_level)
    
    try:
        logger.info("="*60)
        logger.info("AUTOMATED JOB SEARCH PIPELINE STARTING")
        logger.info("="*60)
        
        start_time = datetime.now()
        pipeline_results = {}
        
        # Get initial database stats
        initial_stats = get_database_stats()
        logger.info(f"Initial database stats: {initial_stats}")
        
        if args.cleanup_only:
            # Run cleanup only
            logger.info("Running cleanup-only mode")
            cleanup_results = cleanup_old_data()
            pipeline_results['cleanup'] = cleanup_results
        else:
            # Run full pipeline
            
            # Phase 1: Job Scraping
            if not args.skip_scraping:
                logger.info("Phase 1: Job Scraping")
                scrape_results = scrape_jobs()
                pipeline_results['scraping'] = scrape_results
                new_jobs_count = scrape_results['overall_stats']['total_new_jobs']
            else:
                logger.info("Skipping scraping phase")
                new_jobs_count = 0
            
            # Phase 2: Job Relevance Analysis
            if not args.skip_analysis and new_jobs_count > 0:
                logger.info("Phase 2: Job Relevance Analysis")
                analysis_results = analyze_job_relevance(new_jobs_count)
                pipeline_results['analysis'] = analysis_results
                relevant_jobs_count = analysis_results['relevant_jobs_found']
            else:
                logger.info("Skipping analysis phase")
                relevant_jobs_count = 0
            
            # Phase 3: Document Generation
            if not args.skip_documents and relevant_jobs_count > 0:
                logger.info("Phase 3: Document Generation")
                document_results = generate_documents(relevant_jobs_count)
                pipeline_results['documents'] = document_results
            else:
                logger.info("Skipping document generation phase")
            
            # Phase 4: Email Reporting
            if not args.skip_email:
                logger.info("Phase 4: Email Reporting")
                email_results = send_email_report(pipeline_results)
                pipeline_results['email'] = email_results
            else:
                logger.info("Skipping email reporting phase")
            
            # Phase 5: Cleanup
            logger.info("Phase 5: Data Cleanup")
            cleanup_results = cleanup_old_data()
            pipeline_results['cleanup'] = cleanup_results
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        final_stats = get_database_stats()
        
        logger.info("="*60)
        logger.info("PIPELINE EXECUTION COMPLETED")
        logger.info("="*60)
        logger.info(f"Total execution time: {duration:.2f} seconds")
        logger.info(f"Final database stats: {final_stats}")
        
        # Log phase results
        for phase, results in pipeline_results.items():
            if isinstance(results, dict) and results.get('status') == 'completed':
                logger.info(f"{phase.title()} phase: SUCCESS")
            elif isinstance(results, dict):
                logger.info(f"{phase.title()} phase: {results}")
        
        logger.info("Pipeline execution completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}")
        logger.exception("Full error traceback:")
        return 1

if __name__ == "__main__":
    sys.exit(main())