from unittest import mock

from django.core.cache import cache
from django.core.management import call_command

from queuebie.settings import get_queuebie_cache_key


def test_clear_queuebie_registry_command():
    # Set initial cache values for testing
    cache.set(get_queuebie_cache_key(), "some_value")

    # Ensure cache keys exist before running the command
    assert cache.get(get_queuebie_cache_key()) == "some_value"

    # Mock the logger to verify log output
    with mock.patch("queuebie.logger.get_logger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value

        # Run the management command
        call_command("clear_queuebie_registry")

        # Check if cache keys are deleted
        assert cache.get(get_queuebie_cache_key()) is None

        # Verify logger was called with expected message
        mock_logger.info.assert_called_once_with("Queuebie registry cleared.")
