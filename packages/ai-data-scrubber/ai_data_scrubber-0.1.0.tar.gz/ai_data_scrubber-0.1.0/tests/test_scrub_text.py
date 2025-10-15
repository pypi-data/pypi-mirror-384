#!/usr/bin/env python3
"""
Tests for ai_data_scrubber package

"""

from ai_data_scrubber import scrub_text
from ai_data_scrubber.scrub_text import create_regex_patterns


class TestCreateRegexPatterns:
    """Test the create_regex_patterns function."""

    def test_returns_list_of_tuples(self):
        """Test that the function returns a list of tuples."""
        patterns = create_regex_patterns()
        assert isinstance(patterns, list)
        assert all(
            isinstance(pattern, tuple) and len(pattern) == 2 for pattern in patterns
        )

    def test_contains_expected_patterns(self):
        """Test that all expected pattern types are present."""
        patterns = create_regex_patterns()
        replacements = [pattern[1] for pattern in patterns]

        # Check that expected replacements are present
        assert "[EMAIL]" in replacements
        assert "[URL]" in replacements
        assert "[PHONE]" in replacements
        assert "[ADDRESS]" in replacements
        assert "[UNIT]" in replacements
        assert "[ZIP_CODE]" in replacements
        assert "[LICENSE_PLATE]" in replacements


class TestScrubText:
    """Test the scrub_text function."""

    def test_email_scrubbing(self):
        """Test that email addresses are scrubbed."""
        text = "Contact me at test@example.com"
        result = scrub_text(text)

        assert "test@example.com" not in result
        assert "[EMAIL]" in result

    def test_phone_scrubbing(self):
        """Test that phone numbers are scrubbed."""
        text = "Call 123-456-7890 for more information or (553) 123-4567 or 2064569843"
        result = scrub_text(text)

        assert "123-456-7890" not in result
        assert "2064569843" not in result
        assert "(553) 123-4567" not in result
        assert "[PHONE]" in result

    def test_address_scrubbing(self):
        """Test that addresses are scrubbed."""
        text = "I live at 123 Main Street"
        result = scrub_text(text)

        assert "123 Main Street" not in result
        assert "[ADDRESS]" in result

    def test_zip_code_scrubbing(self):
        """Test that ZIP codes are scrubbed."""
        text = "New York, NY 10001"
        result = scrub_text(text)

        assert "10001" not in result

    def test_comprehensive_scrubbing(self):
        """Test comprehensive scrubbing of multiple data types."""
        text = """
        John Smith lives at 123 Main Street, Apt 4B, New York, NY 10001.
        Contact: john.smith@email.com or (555) 123-4567
        Visit https://johnsmith.com for portfolio
        LinkedIn: linkedin.com/in/johnsmith
        """

        result = scrub_text(text)

        # Check that original data is not present
        assert "John Smith" not in result
        assert "john.smith@email.com" not in result
        assert "(555) 123-4567" not in result
        assert "123 Main Street" not in result
        assert "10001" not in result
        assert "https://johnsmith.com" not in result
        assert "linkedin.com/in/johnsmith" not in result

        # Check that replacement tags are present
        assert "[NAME]" in result
        assert "[EMAIL]" in result
        assert "[PHONE]" in result
        assert "[ADDRESS]" in result
        assert "[URL]" in result

    def test_url_scrubbing(self):
        """Test that URLs are scrubbed."""
        text = "Visit https://example.com or www.test.org or linkedin.com/in/username for more info"
        result = scrub_text(text)

        assert "https://example.com" not in result
        assert "www.test.org" not in result
        assert "linkedin.com/in/username" not in result
        assert "[URL]" in result

    def test_case_insensitive_scrubbing(self):
        """Test that scrubbing is case insensitive."""
        text = "Email: TEST@EXAMPLE.COM"
        result = scrub_text(text)

        assert "TEST@EXAMPLE.COM" not in result

    def test_address_true_positives(self):
        """Test that various address formats are correctly scrubbed."""
        address_test_cases = [
            "100 S Broadway",
            "200 N Main",
            "300 E Oak",
            "400 W Pine",
            "500 NE Cedar",
            "600 SW Maple",
            "700 North First",
            "800 South Second",
            "900 East Third",
            "1000 West Fourth",
        ]

        for test_case in address_test_cases:
            result = scrub_text(test_case)

            # These should be scrubbed as addresses
            assert "[ADDRESS]" in result, f"Expected address scrubbing for: {test_case}"
            assert test_case not in result, (
                f"Original text should not be present for: {test_case}"
            )

    def test_address_false_positives(self):
        """Test that time-related expressions are NOT scrubbed as addresses."""
        false_positive_test_cases = [
            "3 days after",
            "5 years experience",
            "10 minutes later",
            "2 hours ago",
        ]

        for test_case in false_positive_test_cases:
            result = scrub_text(test_case)

            # These should NOT be scrubbed (false positives)
            assert test_case in result, f"Text should remain unchanged for: {test_case}"
            assert "[ADDRESS]" not in result, (
                f"Should not be scrubbed as address: {test_case}"
            )

    def test_license_plate_scrubbing(self):
        """Test that US license plate numbers are scrubbed."""
        license_plate_test_cases = [
            "ARY6056",
            "ABC123",
            "Z1234",
            "A1BC12",
            "XYZ999",
        ]

        for test_case in license_plate_test_cases:
            result = scrub_text(test_case)

            # These should be scrubbed as license plates
            assert "[LICENSE_PLATE]" in result, (
                f"Expected license plate scrubbing for: {test_case}"
            )
            assert test_case not in result, (
                f"Original text should not be present for: {test_case}"
            )

    def test_license_plate_false_positives(self):
        """Test that non-license plate patterns are NOT scrubbed."""
        false_positive_test_cases = [
            "abc123",  # lowercase letters
            "ABC",  # letters only
            "123",  # digits only
            "AB-123",  # with hyphen
            "AB 123",  # with space
        ]

        for test_case in false_positive_test_cases:
            result = scrub_text(test_case)

            # These should NOT be scrubbed as license plates
            assert test_case in result, f"Text should remain unchanged for: {test_case}"
            assert "[LICENSE_PLATE]" not in result, (
                f"Should not be scrubbed as license plate: {test_case}"
            )
