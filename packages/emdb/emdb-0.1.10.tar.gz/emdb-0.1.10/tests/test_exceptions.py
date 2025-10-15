"""Unit tests for EMDB exceptions module."""
import pytest
from emdb.exceptions import (
    EMDBError,
    EMDBAPIError,
    EMDBNotFoundError,
    EMDBInvalidIDError,
    EMDBNetworkError,
    EMDBRateLimitError,
    EMDBFileNotFoundError,
)


class TestEMDBError:
    """Tests for the base EMDBError exception."""

    def test_emdb_error_message(self):
        """Test that EMDBError can be raised with a message."""
        with pytest.raises(EMDBError) as excinfo:
            raise EMDBError("Test error message")
        assert "Test error message" in str(excinfo.value)


class TestEMDBAPIError:
    """Tests for EMDBAPIError exception."""

    def test_api_error_with_message_only(self):
        """Test EMDBAPIError with just a message."""
        error = EMDBAPIError("API error occurred")
        assert error.message == "API error occurred"
        assert error.status_code is None
        assert error.url is None
        assert "EMDB API Error: API error occurred" in str(error)

    def test_api_error_with_status_code(self):
        """Test EMDBAPIError with message and status code."""
        error = EMDBAPIError("Server error", status_code=500)
        assert error.message == "Server error"
        assert error.status_code == 500
        assert "Status code: 500" in str(error)

    def test_api_error_with_all_parameters(self):
        """Test EMDBAPIError with all parameters."""
        error = EMDBAPIError(
            "Not found", status_code=404, url="https://www.ebi.ac.uk/emdb/api/entry/EMD-1234"
        )
        assert error.message == "Not found"
        assert error.status_code == 404
        assert error.url == "https://www.ebi.ac.uk/emdb/api/entry/EMD-1234"
        assert "Status code: 404" in str(error)
        assert "https://www.ebi.ac.uk/emdb/api/entry/EMD-1234" in str(error)


class TestEMDBNotFoundError:
    """Tests for EMDBNotFoundError exception."""

    def test_not_found_error(self):
        """Test EMDBNotFoundError inherits from EMDBAPIError."""
        error = EMDBNotFoundError("Entry not found", 404, "https://www.ebi.ac.uk/emdb/api/entry/EMD-9999")
        assert isinstance(error, EMDBAPIError)
        assert error.status_code == 404


class TestEMDBInvalidIDError:
    """Tests for EMDBInvalidIDError exception."""

    def test_invalid_id_error(self):
        """Test EMDBInvalidIDError with an invalid ID."""
        error = EMDBInvalidIDError("1234")
        assert "Invalid EMDB ID: 1234" in str(error)

    def test_invalid_id_error_inherits_from_emdb_error(self):
        """Test that EMDBInvalidIDError inherits from EMDBError."""
        error = EMDBInvalidIDError("XYZ")
        assert isinstance(error, EMDBError)


class TestEMDBNetworkError:
    """Tests for EMDBNetworkError exception."""

    def test_network_error(self):
        """Test EMDBNetworkError can be raised with a message."""
        with pytest.raises(EMDBNetworkError) as excinfo:
            raise EMDBNetworkError("Network connection failed")
        assert "Network connection failed" in str(excinfo.value)


class TestEMDBRateLimitError:
    """Tests for EMDBRateLimitError exception."""

    def test_rate_limit_error(self):
        """Test EMDBRateLimitError inherits from EMDBAPIError."""
        error = EMDBRateLimitError("Too many requests", 429, "https://www.ebi.ac.uk/emdb/api/entry/EMD-1234")
        assert isinstance(error, EMDBAPIError)
        assert error.status_code == 429


class TestEMDBFileNotFoundError:
    """Tests for EMDBFileNotFoundError exception."""

    def test_file_not_found_error_attributes(self):
        """Test EMDBFileNotFoundError stores emdb_id and filename."""
        error = EMDBFileNotFoundError("EMD-1234", "test_file.map")
        assert error.emdb_id == "EMD-1234"
        assert error.filename == "test_file.map"
        assert "File 'test_file.map' not found in EMDB entry EMD-1234" in str(error)

    def test_file_not_found_error_inherits_from_emdb_error(self):
        """Test that EMDBFileNotFoundError inherits from EMDBError."""
        error = EMDBFileNotFoundError("EMD-5678", "another_file.mrc")
        assert isinstance(error, EMDBError)
