# CLAUDE.md

## Project Overview

This project is an automated job checking and application pipeline that scrapes job websites, identifies relevant roles, and generates tailored resumes and cover letters. Deployed on AWS with cron scheduling for hourly execution.

## The Golden Rule

When unsure about implementation details, ALWAYS ask the developer.  

## Critical Architecture Decisions  

### This Is The Core Pipeline Flow

1. **Job Scraping**: Collect new job postings from configured websites
2. **Data Persistence**: Store job data in SQLite database for comparison
3. **Relevance Filtering**: Identify new roles that match criteria
4. **Document Generation**: Modify LaTeX templates to fit job descriptions
5. **Email Reporting**: Send hourly reports with tailored PDFs

### Key Components:
- Web scrapers (employing Beautiful Soup and Selenium) for multiple job sites
- SQLite database for job tracking and deduplication
- LaTeX template processor for resume/cover letter customization
- Email service for automated reporting
- AWS deployment configuration for cron scheduling


## Input Requirements

The system expects three main inputs:
- LaTeX template for resume
- Cover letter template
- Configuration file with job websites and scraping parameters

## Code Style and Patterns  

### Anchor comments  

Add specially formatted comments throughout the codebase, where appropriate, for yourself as inline knowledge that can be easily `grep`ped for.  

### Guidelines

- Always add new commands to the README.md file. Ensure that there is a section of the README.md file that gives super basic, step-by-step instructions and commands to run this tool for someone who just received the code and has set up nothing. They should be able to set up their tools and run the code given only this documentation.
- Always add accompanying unit tests for all new code that is added. These unit tests should cover working, "happy path" scenarios and failure modes. All branching logic should be covered, to keep code coverage close to 100%. These tests' interface should match that of the code, so please examine how the code works first before creating tests, instead of making your own assumptions about the interface. 
- All test code (except for `pytest.ini`) should live in the `tests/` folder. 
- Include type hints
- Always include docstrings at the top of each python module / `.py` file. 
- Always include docstrings for classes and functions. Describe inputs and outputs.
- Use `AIDEV-NOTE:`, `AIDEV-TODO:`, or `AIDEV-QUESTION:` (all-caps prefix) for comments aimed at AI and developers.  
- **Important:** Before scanning files, always first try to **grep for existing anchors** `AIDEV-*` in relevant subdirectories.  
- **Update relevant anchors** when modifying associated code.  
- **Do not remove `AIDEV-NOTE`s** without explicit human instruction.  
- Make sure to add relevant anchor comments, whenever a file or piece of code is:  
  * too complex, or  
  * very important, or  
  * confusing, or  
  * could have a bug  
- We optimize for maintainability over cleverness. When in doubt, choose the boring solution.  

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
- Email functionality needs SMTP configuration (gmail credentials will be provided)
- AWS deployment will use Fargate with cron scheduling
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
├── docker-compose.yml               # Multi-container orchestration
├── .python-version                  # Python version
├── CLAUDE.md                        # Claude guidance file
├── pyproject.toml                   # Contains the build system requirements
└── uv.lock                          # UV lock file
```