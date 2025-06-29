# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Automated job checking and application pipeline that scrapes job websites, identifies relevant roles, and generates tailored resumes and cover letters. Deployed on AWS with cron scheduling for hourly execution.

## Architecture

**Core Pipeline Flow:**
1. **Job Scraping**: Collect new job postings from configured websites
2. **Data Persistence**: Store job data in SQLite database for comparison
3. **Relevance Filtering**: Identify new roles that match criteria
4. **Document Generation**: Modify LaTeX templates to fit job descriptions
5. **Email Reporting**: Send hourly reports with tailored PDFs

**Key Components:**
- Web scrapers for multiple job sites
- SQLite database for job tracking and deduplication
- LaTeX template processor for resume/cover letter customization
- Email service for automated reporting
- AWS deployment configuration for cron scheduling

## Input Requirements

The system expects three main inputs:
- LaTeX template for resume
- Cover letter template
- Configuration file with job websites and scraping parameters

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run job pipeline manually
python main.py

# Run tests
python -m pytest

# Format and lint
ruff format .
ruff check .

# Database operations
python -m src.database.init_db
python -m src.database.migrate
```

## Development Notes

- SQLite database will track job postings to prevent duplicate processing
- LaTeX processing requires local LaTeX installation or containerized solution
- Email functionality needs SMTP configuration
- AWS deployment will use Lambda or EC2 with cron scheduling
- Consider rate limiting for web scraping to avoid being blocked

## Project Structure

```
.
├── config/                          # Configuration files
│   ├── aws/                         # AWS deployment configurations
│   ├── email/                       # SMTP and email service settings
│   └── sites/                       # Job site scraping configurations
├── data/                            # Data storage directories
│   ├── exports/                     # Generated PDFs and exports
│   └── jobs/                        # Job posting data and SQLite database
├── deploy/                          # Deployment configurations
│   ├── aws/                         # AWS deployment templates
│   │   ├── cloudformation/          # CloudFormation infrastructure templates
│   │   ├── ec2/                     # EC2 deployment scripts
│   │   └── lambda/                  # Lambda function configurations
│   └── docker/                      # Container configurations
├── docs/                            # Documentation
│   ├── api/                         # API documentation
│   ├── architecture/                # System architecture docs
│   └── deployment/                  # Deployment guides
├── logs/                            # Application logs
│   ├── application/                 # General application logs
│   ├── errors/                      # Error logs
│   └── scraping/                    # Web scraping logs
├── scripts/                         # Utility scripts
│   ├── maintenance/                 # System maintenance scripts
│   ├── migration/                   # Database migration scripts
│   └── setup/                       # Environment setup scripts
├── src/                             # Source code
│   ├── database/                    # Database layer
│   │   ├── migrations/              # Database schema migrations
│   │   └── models/                  # SQLite models and schemas
│   ├── email/                       # Email functionality
│   │   └── services/                # Email notification services
│   ├── scrapers/                    # Web scraping components
│   │   ├── parsers/                 # Job posting parsers
│   │   └── sites/                   # Site-specific scrapers
│   ├── templates/                   # Template processing
│   │   └── processors/              # LaTeX template processors
│   └── utils/                       # Shared utilities and helpers
├── templates/                       # Document templates
│   ├── cover_letter/                # LaTeX cover letter templates
│   └── resume/                      # LaTeX resume templates
├── tests/                           # Test suite
│   ├── fixtures/                    # Test data and fixtures
│   ├── integration/                 # Integration tests
│   │   ├── end_to_end/              # Full pipeline tests
│   │   └── pipeline/                # Component integration tests
│   └── unit/                        # Unit tests
│       ├── database/                # Database layer tests
│       ├── email/                   # Email service tests
│       ├── scrapers/                # Scraper tests
│       ├── templates/               # Template processor tests
│       └── utils/                   # Utility function tests
├── main.py                          # Main application entry point
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── Dockerfile                       # Container build configuration
└── docker-compose.yml               # Multi-container orchestration
```