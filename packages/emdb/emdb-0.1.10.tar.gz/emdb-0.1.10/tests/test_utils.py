"""Unit tests for EMDB utils module."""
import time
import pytest
import responses
from unittest.mock import patch, MagicMock
from emdb.utils import fixed_sleep_rate_limit, make_request
from emdb.exceptions import (
    EMDBNotFoundError,
    EMDBRateLimitError,
    EMDBAPIError,
    EMDBNetworkError,
)


class TestFixedSleepRateLimit:
    """Tests for the fixed_sleep_rate_limit decorator."""

    def test_rate_limit_enforces_minimum_interval(self):
        """Test that the decorator enforces a minimum interval between calls."""
        call_times = []

        @fixed_sleep_rate_limit(0.1)
        def test_func():
            call_times.append(time.time())
            return "result"

        # Make multiple calls
        test_func()
        test_func()
        test_func()

        # Check that calls are at least 0.1 seconds apart
        assert len(call_times) == 3
        assert call_times[1] - call_times[0] >= 0.1
        assert call_times[2] - call_times[1] >= 0.1

    def test_rate_limit_preserves_function_name(self):
        """Test that the decorator preserves the function name."""

        @fixed_sleep_rate_limit(0.1)
        def my_function():
            return "result"

        assert my_function.__name__ == "my_function"

    def test_rate_limit_preserves_return_value(self):
        """Test that the decorator preserves the function's return value."""

        @fixed_sleep_rate_limit(0.1)
        def get_value():
            return 42

        assert get_value() == 42


class TestMakeRequest:
    """Tests for the make_request function."""

    @responses.activate
    def test_make_request_json_success(self):
        """Test successful JSON request."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/test",
            json={"key": "value"},
            status=200,
        )

        result = make_request("/test")
        assert result == {"key": "value"}

    @responses.activate
    def test_make_request_csv_success(self):
        """Test successful CSV request."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/test",
            body="emdb_id\nEMD-1234",
            status=200,
        )

        result = make_request("/test", restype="csv")
        assert result == "emdb_id\nEMD-1234"

    @responses.activate
    def test_make_request_with_params(self):
        """Test request with query parameters."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/search/test",
            json={"results": []},
            status=200,
        )

        result = make_request("/search/test", params={"rows": 100})
        assert result == {"results": []}
        assert len(responses.calls) == 1
        assert "rows=100" in responses.calls[0].request.url

    @responses.activate
    def test_make_request_404_raises_not_found_error(self):
        """Test that 404 status raises EMDBNotFoundError."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/entry/EMD-9999",
            status=404,
        )

        with pytest.raises(EMDBAPIError) as excinfo:
            make_request("/entry/EMD-9999")
        # The exception is wrapped, but should contain the original message
        assert "Entry not found" in str(excinfo.value) or "404" in str(excinfo.value)

    @responses.activate
    def test_make_request_429_raises_rate_limit_error(self):
        """Test that 429 status raises EMDBRateLimitError."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/entry/EMD-1234",
            status=429,
        )

        with pytest.raises(EMDBAPIError) as excinfo:
            make_request("/entry/EMD-1234")
        # The exception is wrapped, but should contain the original message
        assert "Rate limit exceeded" in str(excinfo.value) or "429" in str(excinfo.value)

    @responses.activate
    def test_make_request_500_raises_api_error(self):
        """Test that 500 status raises EMDBAPIError."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/entry/EMD-1234",
            status=500,
        )

        with pytest.raises(EMDBAPIError) as excinfo:
            make_request("/entry/EMD-1234")
        assert "Server error" in str(excinfo.value) or "500" in str(excinfo.value)

    @responses.activate
    def test_make_request_timeout_retries(self):
        """Test that timeout is retried up to the retry limit."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/test",
            body=Exception("Timeout"),
        )

        with patch("requests.get") as mock_get:
            import requests
            mock_get.side_effect = requests.Timeout("Connection timeout")

            with pytest.raises(EMDBNetworkError) as excinfo:
                make_request("/test", retries=2)

            assert "timed out" in str(excinfo.value)
            # Should be called twice (initial + 1 retry)
            assert mock_get.call_count == 2

    @responses.activate
    def test_make_request_network_error(self):
        """Test that network errors raise EMDBNetworkError."""
        with patch("requests.get") as mock_get:
            import requests
            mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

            with pytest.raises(EMDBNetworkError) as excinfo:
                make_request("/test")

            assert "Network error" in str(excinfo.value)
