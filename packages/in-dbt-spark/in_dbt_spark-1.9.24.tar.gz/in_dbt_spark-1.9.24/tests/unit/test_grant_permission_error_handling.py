"""Test module for grant permission error handling logic."""

import unittest
import re


class TestGrantPermissionErrorHandling(unittest.TestCase):
    """Test cases for grant permission error handling regex pattern and logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.regex_pattern = r"User .* is in too many groups already and cannot be added to more"

    def test_regex_pattern_matches_basic_error(self):
        """Test that the regex pattern matches the basic error message."""
        error_message = "User john.doe is in too many groups already and cannot be added to more"
        self.assertTrue(re.search(self.regex_pattern, error_message))

    def test_regex_pattern_matches_with_email_user(self):
        """Test that the regex pattern matches when user is an email address."""
        error_message = "User user@example.com is in too many groups already and cannot be added to more"
        self.assertTrue(re.search(self.regex_pattern, error_message))

    def test_regex_pattern_matches_with_special_characters(self):
        """Test that the regex pattern matches when user has special characters."""
        error_message = "User user-name_123@domain.com is in too many groups already and cannot be added to more"
        self.assertTrue(re.search(self.regex_pattern, error_message))

    def test_regex_pattern_does_not_match_different_error(self):
        """Test that the regex pattern does not match different error messages."""
        error_message = "User john.doe has insufficient permissions"
        self.assertFalse(re.search(self.regex_pattern, error_message))

    def test_regex_pattern_does_not_match_partial_message(self):
        """Test that the regex pattern does not match partial error messages."""
        error_message = "User john.doe is in too many groups"
        self.assertFalse(re.search(self.regex_pattern, error_message))

    def test_regex_pattern_case_sensitive(self):
        """Test that the regex pattern is case sensitive."""
        error_message = "user john.doe is in too many groups already and cannot be added to more"
        self.assertFalse(re.search(self.regex_pattern, error_message))

    def test_regex_pattern_with_multiline_message(self):
        """Test that the regex pattern works with multiline error messages."""
        error_message = """
        Database error occurred:
        User john.doe is in too many groups already and cannot be added to more
        Please contact administrator.
        """
        self.assertTrue(re.search(self.regex_pattern, error_message))


if __name__ == '__main__':
    unittest.main()