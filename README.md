# Automated Job Search Pipeline

Automated job checking and application pipeline that scrapes job websites, identifies relevant roles, and generates tailored resumes and cover letters. Deployed on AWS with cron scheduling for hourly execution.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Automated Job Scraping**: Continuously monitors multiple job websites for new postings
- **Smart Filtering**: Identifies relevant roles based on configurable criteria
- **Document Generation**: Automatically tailors LaTeX resumes and cover letters to job descriptions
- **Duplicate Detection**: SQLite database prevents reprocessing of existing job postings
- **Email Notifications**: Hourly reports with generated PDFs attached
- **Cloud Deployment**: AWS Lambda/EC2 deployment with cron scheduling
- **Rate Limiting**: Respectful web scraping to avoid being blocked

## Architecture

### Core Pipeline Flow

The automated pipeline (`src/__main__.py`) executes these phases sequentially:

1. **Job Scraping**: Collect new job postings from configured websites with anti-detection measures
2. **Data Persistence**: Store job data in SQLite database with deduplication and change tracking
3. **Relevance Analysis**: Apply ML/NLP techniques to identify jobs matching user criteria
4. **Document Generation**: Generate customized LaTeX resumes and cover letters for relevant jobs
5. **Email Reporting**: Send comprehensive reports with generated PDFs attached
6. **Data Cleanup**: Remove old job records and optimize database storage

### Key Components

- **Web Scrapers**: Multi-site job posting collection with anti-detection features
  - Configurable sites in `config/sites/sites_config.py` 
  - Currently supports: Hirebase.org (with more sites planned)
  - Anti-detection: Random delays, user agent rotation, exponential backoff
- **SQLite Database**: Job tracking, deduplication, and change detection
- **Pipeline Orchestrator**: Central coordinator in `src/__main__.py`
- **LaTeX Processor**: Resume/cover letter customization (planned)
- **Email Service**: Automated reporting system (planned)
- **AWS Integration**: Cloud deployment and scheduling

### Web Scraping Features

- **Anti-Detection Measures**: 
  - Random delays between requests (3-8 seconds)
  - Rotating user agents and HTTP headers
  - Exponential backoff on rate limits
  - Session management with retry strategies
- **Robust Error Handling**: Graceful failure recovery and comprehensive logging
- **Pagination Support**: Automatically handles multi-page job listings
- **Content Deduplication**: Prevents reprocessing of existing jobs
- **Change Detection**: Tracks job updates using content hashing

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

## Installation

### Prerequisites

- Python 3.8 or higher
- LaTeX distribution (TeX Live or MiKTeX)
- SQLite3
- Git

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/automated-job-search.git
   cd automated-job-search
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**
   ```bash
   python scripts/setup/init_database.py
   ```

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## Usage

### Pipeline Execution

The main pipeline orchestrates all components through a single entry point:

```bash
# Run the complete automated job search pipeline
python -m src

# Or alternatively
python src/__main__.py

# Run with specific options
python -m src --log-level DEBUG              # Enable debug logging
python -m src --skip-email                   # Skip email reporting
python -m src --skip-analysis                # Skip job relevance analysis
python -m src --skip-documents               # Skip document generation
python -m src --cleanup-only                 # Only run data cleanup

# Test scraping without full pipeline
python -m src --skip-analysis --skip-documents --skip-email
```

### Component Testing

You can also test individual components:

```bash
# Test database operations
python scripts/setup/init_database.py
python scripts/migration/migrate_database.py current

# Test scraping (when individual scrapers are implemented)
# python -m src.scrapers.sites.hirebase_scraper
```

### Scheduled Execution

The system is designed for automated execution via cron or AWS scheduling:

```bash
# Add to crontab for hourly execution
0 * * * * cd /path/to/automated-job-search && python -m src
```

## Configuration

### Job Site Configuration

Job scraping websites are configured in `config/sites/sites_config.py`:

```python
# Currently configured sites
SITES_CONFIG = {
    'hirebase': SiteConfig(
        name='Hirebase',
        base_url='https://hirebase.org',
        search_url='https://hirebase.org/search?page={page}&...',
        enabled=True,
        max_pages=20,
        delay_range=(3, 8),  # Random delay between requests
        max_retries=3
    )
}
```

To add new job sites:
1. Add configuration to `SITES_CONFIG` in `config/sites/sites_config.py`
2. Create site-specific scraper in `src/scrapers/sites/`
3. Add scraper to the factory method in `ScraperManager`

### Required Template Inputs (Planned)

1. **LaTeX Resume Template**: Place in `templates/resume/`
2. **Cover Letter Template**: Place in `templates/cover_letter/`
3. **Email Configuration**: SMTP settings in `config/email/`

### Environment Variables

Key environment variables (see `.env.example`):

- `DATABASE_PATH`: SQLite database location
- `SMTP_SERVER`: Email server configuration
- `SCRAPING_DELAY`: Rate limiting between requests
- `AWS_REGION`: AWS deployment region

## Development

### Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest

# Format and lint
ruff format .
ruff check .

# Database operations
python scripts/setup/init_database.py
python scripts/migration/migrate_database.py upgrade
python scripts/migration/migrate_database.py current
```

### Development Notes

- SQLite database automatically tracks job postings to prevent duplicate processing
- Content hashing detects job changes and updates existing records
- Anti-detection measures are already implemented for respectful scraping
- Pipeline supports modular execution - individual phases can be skipped for testing
- Comprehensive logging captures all scraping activities and errors
- LaTeX processing requires local LaTeX installation or containerized solution (planned)
- Email functionality needs SMTP configuration (planned)

## Testing

### Unit Tests
```bash
python -m pytest tests/unit/
```

### Integration Tests
```bash
python -m pytest tests/integration/
```

### End-to-End Tests
```bash
python -m pytest tests/integration/end_to_end/
```

## Deployment

### AWS Lambda

Deploy as serverless functions with CloudFormation:

```bash
cd deploy/aws/cloudformation/
aws cloudformation deploy --template-file infrastructure.yaml --stack-name job-scraper
```

### AWS EC2

Deploy on EC2 with cron scheduling:

```bash
cd deploy/aws/ec2/
./deploy.sh
```

### Docker

Run in containers:

```bash
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings for public functions
- Write tests for new features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note**: This is a prototype developed with Claude Code and SuperClaude. Ensure compliance with job website terms of service and local regulations regarding automated data collection.