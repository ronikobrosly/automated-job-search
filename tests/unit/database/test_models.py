"""Unit tests for database models."""

import hashlib
from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from src.database.models.job import Base, Job


class TestJob:
    """Test cases for the Job SQLAlchemy model."""

    def test_job_creation_with_required_fields(self, test_db_session):
        """Test creating a Job instance with only required fields.

        Args:
            test_db_session: Test database session fixture.
        """
        job = Job(
            job_id="test-job-1", job_website="test-site", role_title="Software Engineer"
        )
        test_db_session.add(job)
        test_db_session.commit()

        assert job.id is not None
        assert job.job_id == "test-job-1"
        assert job.job_website == "test-site"
        assert job.role_title == "Software Engineer"
        assert job.is_new is True  # Default value
        assert job.is_relevant is False  # Default value
        assert job.is_processed is False  # Default value
        assert job.when_scraped is not None
        assert job.last_seen is not None

    def test_job_creation_with_all_fields(self, test_db_session, sample_job_data):
        """Test creating a Job instance with all fields populated.

        Args:
            test_db_session: Test database session fixture.
            sample_job_data: Sample job data fixture.
        """
        job = Job(**sample_job_data)
        test_db_session.add(job)
        test_db_session.commit()

        assert job.id is not None
        assert job.job_id == sample_job_data["job_id"]
        assert job.company_name == sample_job_data["company_name"]
        assert job.role_title == sample_job_data["role_title"]
        assert job.job_website == sample_job_data["job_website"]
        assert job.job_url == sample_job_data["job_url"]
        assert job.location == sample_job_data["location"]
        assert job.salary_range == sample_job_data["salary_range"]
        assert job.job_description == sample_job_data["job_description"]
        assert job.requirements == sample_job_data["requirements"]
        assert job.additional_data == sample_job_data["additional_data"]

    def test_job_unique_constraint(self, test_db_session):
        """Test that job_id and job_website combination must be unique.

        Args:
            test_db_session: Test database session fixture.
        """
        # Create first job
        job1 = Job(
            job_id="duplicate-job", job_website="test-site", role_title="Engineer 1"
        )
        test_db_session.add(job1)
        test_db_session.commit()

        # Try to create duplicate job with same job_id and job_website
        job2 = Job(
            job_id="duplicate-job", job_website="test-site", role_title="Engineer 2"
        )
        test_db_session.add(job2)

        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_job_different_websites_same_id_allowed(self, test_db_session):
        """Test that same job_id is allowed on different websites.

        Args:
            test_db_session: Test database session fixture.
        """
        # Create job on first website
        job1 = Job(job_id="same-job-id", job_website="site-1", role_title="Engineer")
        test_db_session.add(job1)
        test_db_session.commit()

        # Create job with same ID on different website - should succeed
        job2 = Job(job_id="same-job-id", job_website="site-2", role_title="Engineer")
        test_db_session.add(job2)
        test_db_session.commit()

        assert job1.id != job2.id
        assert job1.job_id == job2.job_id
        assert job1.job_website != job2.job_website

    def test_generate_content_hash_basic(self):
        """Test content hash generation with basic job data."""
        job = Job(
            job_id="hash-test",
            job_website="test-site",
            role_title="Software Engineer",
            company_name="Tech Corp",
            location="San Francisco, CA",
            salary_range="$100,000 - $120,000",
            job_description="Build web applications using Python.",
        )

        content_hash = job.generate_content_hash()

        # Hash should be 64 character hex string (SHA256)
        assert len(content_hash) == 64
        assert all(c in "0123456789abcdef" for c in content_hash)

        # Same job should generate same hash
        same_hash = job.generate_content_hash()
        assert content_hash == same_hash

    def test_generate_content_hash_with_additional_data(self):
        """Test content hash generation includes additional_data field."""
        job = Job(
            job_id="hash-test-2",
            job_website="test-site",
            role_title="Data Scientist",
            company_name="AI Corp",
            location="Remote",
            salary_range="$120,000 - $150,000",
            job_description="Build ML models.",
            additional_data={"benefits": "Health, Dental", "work_type": "Remote"},
        )

        content_hash = job.generate_content_hash()

        # Create same job without additional_data
        job_no_extra = Job(
            job_id="hash-test-3",
            job_website="test-site",
            role_title="Data Scientist",
            company_name="AI Corp",
            location="Remote",
            salary_range="$120,000 - $150,000",
            job_description="Build ML models.",
            additional_data=None,
        )

        hash_no_extra = job_no_extra.generate_content_hash()

        # Hashes should be different
        assert content_hash != hash_no_extra

    def test_generate_content_hash_deterministic(self):
        """Test that content hash generation is deterministic."""
        job_data = {
            "job_id": "deterministic-test",
            "job_website": "test-site",
            "role_title": "Backend Engineer",
            "company_name": "StartupCo",
            "location": "New York, NY",
            "salary_range": "$90,000 - $110,000",
            "job_description": "Build scalable backend systems.",
            "additional_data": {"experience": "3+ years", "remote": True},
        }

        # Create multiple instances with same data
        job1 = Job(**job_data)
        job2 = Job(**job_data)

        hash1 = job1.generate_content_hash()
        hash2 = job2.generate_content_hash()

        assert hash1 == hash2

    def test_generate_content_hash_content_changes(self):
        """Test that content hash changes when job content changes."""
        job = Job(
            job_id="change-test",
            job_website="test-site",
            role_title="Frontend Engineer",
            company_name="WebCorp",
            location="Austin, TX",
            salary_range="$80,000 - $100,000",
            job_description="Build React applications.",
        )

        original_hash = job.generate_content_hash()

        # Change job description
        job.job_description = "Build Vue.js applications."
        changed_hash = job.generate_content_hash()

        assert original_hash != changed_hash

        # Change salary range
        job.salary_range = "$85,000 - $105,000"
        salary_changed_hash = job.generate_content_hash()

        assert changed_hash != salary_changed_hash

    def test_generate_content_hash_handles_none_values(self):
        """Test content hash generation handles None values gracefully."""
        job = Job(
            job_id="none-test",
            job_website="test-site",
            role_title="QA Engineer",
            company_name=None,  # None value
            location=None,  # None value
            salary_range=None,  # None value
            job_description=None,  # None value
        )

        # Should not raise exception
        content_hash = job.generate_content_hash()
        assert len(content_hash) == 64

    def test_job_repr_method(self, sample_job_data):
        """Test the string representation of Job instances.

        Args:
            sample_job_data: Sample job data fixture.
        """
        job = Job(**sample_job_data)
        job.id = 123  # Set ID for testing

        repr_str = repr(job)

        assert f"Job(id={job.id}" in repr_str
        assert f"role_title='{job.role_title}'" in repr_str
        assert f"company_name='{job.company_name}'" in repr_str
        assert f"job_website='{job.job_website}'" in repr_str

    def test_job_repr_method_with_none_values(self):
        """Test the string representation with None values."""
        job = Job(
            job_id="repr-test",
            job_website="test-site",
            role_title="Test Engineer",
            company_name=None,
        )
        job.id = 456

        repr_str = repr(job)
        assert "Job(id=456" in repr_str
        assert "company_name='None'" in repr_str

    def test_job_timestamps_set_automatically(self, test_db_session):
        """Test that timestamps are set automatically on creation.

        Args:
            test_db_session: Test database session fixture.
        """
        job = Job(
            job_id="timestamp-test",
            job_website="test-site",
            role_title="DevOps Engineer",
        )

        # Before adding to session, timestamps might be None
        # After commit, they should be set
        test_db_session.add(job)
        test_db_session.commit()

        assert job.when_scraped is not None
        assert job.last_seen is not None
        assert job.created_at is not None
        assert job.updated_at is not None
        assert isinstance(job.when_scraped, datetime)
        assert isinstance(job.last_seen, datetime)

    def test_job_boolean_defaults(self, test_db_session):
        """Test that boolean fields have correct default values.

        Args:
            test_db_session: Test database session fixture.
        """
        job = Job(
            job_id="boolean-test",
            job_website="test-site",
            role_title="Security Engineer",
        )
        test_db_session.add(job)
        test_db_session.commit()

        assert job.is_new is True
        assert job.is_relevant is False
        assert job.is_processed is False

    def test_job_with_complex_additional_data(self, test_db_session):
        """Test job creation with complex JSON data in additional_data field.

        Args:
            test_db_session: Test database session fixture.
        """
        complex_data = {
            "benefits": ["Health", "Dental", "Vision", "401k"],
            "requirements": {
                "education": "Bachelor's degree",
                "experience": "3-5 years",
                "skills": ["Python", "Django", "PostgreSQL"],
            },
            "company_info": {
                "size": "50-100 employees",
                "industry": "FinTech",
                "founded": 2015,
            },
            "remote_policy": "Fully Remote",
            "interview_process": [
                "Phone screening",
                "Technical interview",
                "Onsite interview",
            ],
        }

        job = Job(
            job_id="complex-data-test",
            job_website="test-site",
            role_title="Full Stack Engineer",
            company_name="FinTech Startup",
            additional_data=complex_data,
        )
        test_db_session.add(job)
        test_db_session.commit()

        # Retrieve job and verify complex data is preserved
        retrieved_job = (
            test_db_session.query(Job).filter_by(job_id="complex-data-test").first()
        )
        assert retrieved_job.additional_data == complex_data
        assert retrieved_job.additional_data["benefits"] == [
            "Health",
            "Dental",
            "Vision",
            "401k",
        ]
        assert retrieved_job.additional_data["requirements"]["skills"] == [
            "Python",
            "Django",
            "PostgreSQL",
        ]

    def test_job_missing_required_fields_fails(self, test_db_session):
        """Test that creating job without required fields fails appropriately.

        Args:
            test_db_session: Test database session fixture.
        """
        # Missing job_id (nullable=False)
        with pytest.raises((IntegrityError, TypeError)):
            job = Job(job_website="test-site", role_title="Engineer")
            test_db_session.add(job)
            test_db_session.commit()

        test_db_session.rollback()

        # Missing role_title (nullable=False)
        with pytest.raises((IntegrityError, TypeError)):
            job = Job(job_id="missing-title", job_website="test-site")
            test_db_session.add(job)
            test_db_session.commit()

        test_db_session.rollback()

        # Missing job_website (nullable=False)
        with pytest.raises((IntegrityError, TypeError)):
            job = Job(job_id="missing-website", role_title="Engineer")
            test_db_session.add(job)
            test_db_session.commit()
