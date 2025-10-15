#!/usr/bin/env python3
"""
Tests for scrubbing of sample documents

These tests verify that all personal information is properly removed from
sample documents like resumes and lease agreements.
"""

import os
from pathlib import Path
import pytest

from ai_data_scrubber.scrub_text import scrub_file, scrub_text


@pytest.fixture
def scrubbed_resume():
    """Load and return scrubbed resume content."""
    resume_path = Path(__file__).parent / "sample_resume.txt"
    with open(resume_path, "r") as f:
        resume_content = f.read()
    return scrub_text(resume_content)


@pytest.fixture
def scrubbed_lease():
    """Return scrubbed lease agreement content."""
    lease_path = Path(__file__).parent / "sample_lease_agreement.txt"
    with open(lease_path, "r") as f:
        lease_content = f.read()
    return scrub_text(lease_content)


class TestResumeScrubbing:
    """Test scrubbing of the sample resume."""

    def test_resume_personal_names_removed(self, scrubbed_resume):
        """Test that personal names are scrubbed in resume."""
        # Check that personal names are removed
        assert "Sarah Elizabeth Martinez" not in scrubbed_resume
        assert "Sarah" not in scrubbed_resume
        assert "Elizabeth" not in scrubbed_resume
        assert "Martinez" not in scrubbed_resume

        # Check that names are replaced with [NAME]
        assert "[NAME]" in scrubbed_resume

    def test_resume_contact_info_removed(self, scrubbed_resume):
        """Test that contact information is scrubbed in resume."""
        # Check that email is removed
        assert "sarah.martinez@email.com" not in scrubbed_resume
        assert "[EMAIL]" in scrubbed_resume

        # Check that phone number is removed
        assert "(555) 123-4567" not in scrubbed_resume
        assert "[PHONE]" in scrubbed_resume

        # Check that address is removed
        assert "1234 Maple Street" not in scrubbed_resume
        assert "Apt 2B" not in scrubbed_resume
        assert "Seattle, WA 98101" not in scrubbed_resume
        assert "[ADDRESS]" in scrubbed_resume
        assert "[UNIT]" in scrubbed_resume

        # Check that LinkedIn is removed
        assert "linkedin.com/in/sarahmartinez" not in scrubbed_resume

    def test_resume_company_names_preserved(self, scrubbed_resume):
        """Test that company names are preserved (not scrubbed)."""
        # Company names should be preserved
        assert "TechCorp Solutions" in scrubbed_resume
        assert "InnovateSoft Inc." in scrubbed_resume
        assert "University of Washington" in scrubbed_resume

    def test_resume_technical_terms_preserved(self, scrubbed_resume):
        """Test that technical terms and CamelCase are preserved."""
        # Technical terms should be preserved
        assert "Python" in scrubbed_resume
        assert "JavaScript" in scrubbed_resume
        assert "React" in scrubbed_resume
        # assert "Django" in scrubbed_resume
        assert "PostgreSQL" in scrubbed_resume
        assert "AWS" in scrubbed_resume
        assert "Git" in scrubbed_resume
        assert "Docker" in scrubbed_resume
        # assert "Node.js" in scrubbed_resume
        assert "MongoDB" in scrubbed_resume
        assert "WebSockets" in scrubbed_resume
        assert "PWA" in scrubbed_resume
        assert "CI/CD" in scrubbed_resume
        assert "GitHub" in scrubbed_resume


class TestLeaseAgreementScrubbing:
    """Test scrubbing of the sample lease agreement."""

    def test_lease_personal_names_removed(self, scrubbed_lease):
        """Test that personal names are scrubbed in lease agreement."""
        # Check that personal names are removed
        assert "Robert James Thompson" not in scrubbed_lease
        assert "Emily Christine Davis" not in scrubbed_lease
        assert "Sarah Johnson" not in scrubbed_lease
        assert "Michael Davis" not in scrubbed_lease
        assert "Jennifer Thompson" not in scrubbed_lease
        assert "David Wilson" not in scrubbed_lease
        assert "Lisa Anderson" not in scrubbed_lease

        # Check that names are replaced with [NAME]
        assert "[NAME]" in scrubbed_lease

    def test_lease_contact_info_removed(self, scrubbed_lease):
        """Test that contact information is scrubbed in lease agreement."""
        # Check that emails are removed
        assert "robert.thompson@email.com" not in scrubbed_lease
        assert "emily.davis@email.com" not in scrubbed_lease
        assert "david.wilson@pacificpm.com" not in scrubbed_lease
        assert "lisa.anderson@statefarm.com" not in scrubbed_lease
        assert "[EMAIL]" in scrubbed_lease

        # Check that phone numbers are removed
        assert "(206) 555-1234" not in scrubbed_lease
        assert "(425) 555-6789" not in scrubbed_lease
        assert "(206) 555-9876" not in scrubbed_lease
        assert "(206) 555-4321" not in scrubbed_lease
        assert "[PHONE]" in scrubbed_lease

    def test_lease_addresses_removed(self, scrubbed_lease):
        """Test that addresses are scrubbed in lease agreement."""
        # Check that addresses are removed
        assert "1234 Pine Street" not in scrubbed_lease
        assert "5678 Cedar Lane" not in scrubbed_lease
        assert "7890 Maple Avenue" not in scrubbed_lease
        assert "9012 Oak Drive" not in scrubbed_lease
        assert "3456 5th Avenue" not in scrubbed_lease

        # Check that apartment/unit numbers are removed
        assert "Apt 5B" not in scrubbed_lease
        assert "Unit 3C" not in scrubbed_lease
        assert "Suite 200" not in scrubbed_lease
        assert "Suite 301" not in scrubbed_lease

        # Check that ZIP codes are removed
        assert "98102" not in scrubbed_lease
        assert "98004" not in scrubbed_lease
        assert "98103" not in scrubbed_lease
        assert "98052" not in scrubbed_lease
        assert "98101" not in scrubbed_lease

        # Check that replacement tags are present
        assert "[ADDRESS]" in scrubbed_lease
        assert "[UNIT]" in scrubbed_lease

    def test_lease_business_names_preserved(self, scrubbed_lease):
        """Test that business names are preserved (not scrubbed)."""
        # Business names should be preserved
        assert "Pacific Property Management LLC" in scrubbed_lease
        assert "State Farm Insurance" in scrubbed_lease
        assert "Seattle City Light" in scrubbed_lease
        assert "Puget Sound Energy" in scrubbed_lease
        assert "Comcast" in scrubbed_lease


class TestFileScrubbing:
    """Test the file scrubbing function."""

    def test_file_scrubbing_default_output(self):
        """Test that scrub_file creates default output filename."""
        resume_path = Path(__file__).parent / "sample_resume.txt"

        try:
            scrub_file(str(resume_path))

            # Check that default output file was created
            default_output = resume_path.parent / "sample_resume_scrubbed.txt"
            assert default_output.exists()

            # Check that content was scrubbed
            with open(default_output, "r") as f:
                content = f.read()
            assert "Sarah Elizabeth Martinez" not in content
            assert "[NAME]" in content
            assert "sarah.martinez@email.com" not in content
            assert "[EMAIL]" in content

        finally:
            # Clean up
            default_output = resume_path.parent / "sample_resume_scrubbed.txt"
            if default_output.exists():
                os.unlink(default_output)


if __name__ == "__main__":
    pytest.main([__file__])
