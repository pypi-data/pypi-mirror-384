"""Test module for grant permission error handling integration tests."""

import unittest
from unittest.mock import Mock, patch
import re

# Conditional imports for dbt dependencies
try:
    from dbt_common.exceptions import DbtRuntimeError
except ImportError:
    # Create a mock for testing when dbt is not available
    class DbtRuntimeError(Exception):
        pass


class MockSetuStatement:
    """Mock Setu Statement for testing."""
    
    def __init__(self, statement_id="test_statement_001", state="FINISHED"):
        self.statement_id = statement_id
        self.state = state
        self.output = Mock()
        self.output.raise_for_status = Mock()
        self.output.json = {"data": "test_data"}


class MockSetuStatementCursor:
    """Mock Setu Statement Cursor for testing."""
    
    def __init__(self, statement):
        self.statement = statement
    
    def execute(self):
        """Execute method with grant permission error handling."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(
            "Setu Statement {} state is : {}".format(
                self.statement.statement_id, self.statement.state
            )
        )
        try:
            self.statement.output.raise_for_status()
        except DbtRuntimeError as e:
            error_message = str(e)
            # Use regex to check for the specific non-fatal error message
            if re.search(r"User .* is in too many groups already and cannot be added to more", error_message):
                logger.warning(
                    f"Non-fatal error during Setu Statement {self.statement.statement_id} execution: {error_message}"
                    " This error is being treated as non-fatal as per requirements."
                )
                return self.statement.output
            else:
                raise e
        except Exception as e:
            raise DbtRuntimeError(
                f"An unexpected error occurred during Setu Statement {self.statement.statement_id} status check: {e}"
            )
        
        return self.statement.output


class TestSetuSessionCursor(unittest.TestCase):
    """Integration test cases for Setu Session Cursor error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.statement = MockSetuStatement()
        self.cursor = MockSetuStatementCursor(self.statement)

    @patch('logging.getLogger')
    def test_execute_success_no_error(self, mock_logger):
        """Test successful execution with no errors."""
        mock_log_instance = Mock()
        mock_logger.return_value = mock_log_instance
        
        # Mock successful execution
        self.statement.output.raise_for_status.side_effect = None
        
        result = self.cursor.execute()
        
        # Verify the result and logging
        self.assertEqual(result, self.statement.output)
        mock_log_instance.info.assert_called_once()
        mock_log_instance.warning.assert_not_called()

    @patch('logging.getLogger')
    def test_execute_grant_permission_error_handled(self, mock_logger):
        """Test that grant permission error is handled as non-fatal."""
        mock_log_instance = Mock()
        mock_logger.return_value = mock_log_instance
        
        # Mock the specific grant permission error
        error_message = "User john.doe@example.com is in too many groups already and cannot be added to more"
        self.statement.output.raise_for_status.side_effect = DbtRuntimeError(error_message)
        
        result = self.cursor.execute()
        
        # Verify the error was handled gracefully
        self.assertEqual(result, self.statement.output)
        mock_log_instance.info.assert_called_once()
        mock_log_instance.warning.assert_called_once()
        
        # Verify the warning message contains expected content
        warning_call_args = mock_log_instance.warning.call_args[0][0]
        self.assertIn("Non-fatal error", warning_call_args)
        self.assertIn("john.doe@example.com", warning_call_args)


if __name__ == '__main__':
    unittest.main()
