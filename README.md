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

1. **Job Scraping**: Collect new job postings from configured websites
2. **Data Persistence**: Store job data in SQLite database for comparison
3. **Relevance Filtering**: Identify new roles that match criteria
4. **Document Generation**: Modify LaTeX templates to fit job descriptions
5. **Email Reporting**: Send hourly reports with tailored PDFs

### Key Components

- **Web Scrapers**: Multi-site job posting collection
- **SQLite Database**: Job tracking and deduplication
- **LaTeX Processor**: Resume/cover letter customization
- **Email Service**: Automated reporting system
- **AWS Integration**: Cloud deployment and scheduling

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
   python -m src.database.init_db
   ```

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## Usage

### Manual Execution

```bash
# Run the complete job pipeline
python main.py

# Run specific components
python -m src.scrapers.run_scrapers
python -m src.templates.generate_documents
python -m src.email.send_reports
```

### Scheduled Execution

The system is designed for automated execution via cron or AWS scheduling:

```bash
# Add to crontab for hourly execution
0 * * * * cd /path/to/automated-job-search && python main.py
```

## Configuration

### Required Inputs

The system expects three main configuration inputs:

1. **LaTeX Resume Template**: Place in `templates/resume/`
2. **Cover Letter Template**: Place in `templates/cover_letter/`
3. **Site Configuration**: Define job websites and scraping parameters in `config/sites/`

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
python -m src.database.init_db
python -m src.database.migrate
```

### Development Notes

- SQLite database tracks job postings to prevent duplicate processing
- LaTeX processing requires local LaTeX installation or containerized solution
- Email functionality needs SMTP configuration
- Consider rate limiting for web scraping to avoid being blocked

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