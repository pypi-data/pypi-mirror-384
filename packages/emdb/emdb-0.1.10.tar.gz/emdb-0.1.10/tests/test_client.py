"""Unit tests for EMDB client module."""
import pytest
import responses
from unittest.mock import patch, MagicMock
from emdb.client import EMDB
from emdb.exceptions import (
    EMDBInvalidIDError,
    EMDBNotFoundError,
    EMDBAPIError,
)
from emdb.models.entry import EMDBEntry
from emdb.models.validation import EMDBValidation
from emdb.models.annotations import EMDBAnnotations
from emdb.models.search import EMDBSearchResults


class TestEMDBClient:
    """Tests for the EMDB client class."""

    def test_emdb_client_initialization(self):
        """Test that EMDB client can be initialized."""
        client = EMDB()
        assert client is not None

    @responses.activate
    def test_get_entry_success(self):
        """Test successfully retrieving an entry."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/entry/EMD-1234",
            json={"id": "EMD-1234", "title": "Test Entry"},
            status=200,
        )

        client = EMDB()
        with patch.object(EMDBEntry, 'from_api') as mock_from_api:
            mock_entry = MagicMock(spec=EMDBEntry)
            mock_from_api.return_value = mock_entry

            entry = client.get_entry("EMD-1234")

            assert entry == mock_entry
            mock_from_api.assert_called_once()

    def test_get_entry_invalid_id(self):
        """Test that invalid EMDB ID raises EMDBInvalidIDError."""
        client = EMDB()

        with pytest.raises(EMDBInvalidIDError) as excinfo:
            client.get_entry("1234")

        assert "Invalid EMDB ID: 1234" in str(excinfo.value)

    def test_get_entry_invalid_id_missing_prefix(self):
        """Test that ID without EMD- prefix raises EMDBInvalidIDError."""
        client = EMDB()

        with pytest.raises(EMDBInvalidIDError):
            client.get_entry("12345")

    @responses.activate
    def test_get_entry_not_found(self):
        """Test that 404 response raises EMDBAPIError."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/entry/EMD-9999",
            status=404,
        )

        client = EMDB()

        with pytest.raises(EMDBAPIError):
            client.get_entry("EMD-9999")

    @responses.activate
    def test_get_validation_success(self):
        """Test successfully retrieving validation data."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/analysis/EMD-1234",
            json={"1234": {"resolution": {"value": 3.5}}},
            status=200,
        )

        client = EMDB()
        with patch.object(EMDBValidation, 'from_api') as mock_from_api:
            mock_validation = MagicMock(spec=EMDBValidation)
            mock_from_api.return_value = mock_validation

            validation = client.get_validation("EMD-1234")

            assert validation == mock_validation
            mock_from_api.assert_called_once()

    @responses.activate
    def test_get_validation_not_found(self):
        """Test that 404 response in validation raises EMDBAPIError."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/analysis/EMD-9999",
            status=404,
        )

        client = EMDB()

        with pytest.raises(EMDBAPIError):
            client.get_validation("EMD-9999")

    @responses.activate
    def test_get_annotations_success(self):
        """Test successfully retrieving annotations."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/annotations/EMD-1234",
            json={"samples": []},
            status=200,
        )

        client = EMDB()
        with patch.object(EMDBAnnotations, 'from_api') as mock_from_api:
            mock_annotations = MagicMock(spec=EMDBAnnotations)
            mock_from_api.return_value = mock_annotations

            annotations = client.get_annotations("EMD-1234")

            assert annotations == mock_annotations
            mock_from_api.assert_called_once()

    @responses.activate
    def test_get_annotations_not_found(self):
        """Test that 404 response in annotations raises EMDBAPIError."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/annotations/EMD-9999",
            status=404,
        )

        client = EMDB()

        with pytest.raises(EMDBAPIError):
            client.get_annotations("EMD-9999")

    @responses.activate
    def test_search_success(self):
        """Test successfully searching for entries."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/search/test_query",
            body="emdb_id\nEMD-1234\nEMD-5678",
            status=200,
        )

        client = EMDB()
        results = client.search("test_query")

        assert isinstance(results, EMDBSearchResults)
        assert len(results) == 2

    @responses.activate
    def test_search_with_params(self):
        """Test that search sends correct parameters."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/search/query",
            body="emdb_id\nEMD-1234",
            status=200,
        )

        client = EMDB()
        results = client.search("query")

        # Check that the correct parameters were sent
        assert len(responses.calls) == 1
        request_url = responses.calls[0].request.url
        assert "rows=1000000" in request_url
        assert "fl=emdb_id" in request_url
        assert "wt=csv" in request_url

    @responses.activate
    def test_csv_search_success(self):
        """Test successfully performing a CSV search."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/search/test_query",
            body="emdb_id,resolution\nEMD-1234,3.5\nEMD-5678,4.2",
            status=200,
        )

        client = EMDB()
        df = client.csv_search("test_query", fields="emdb_id,resolution")

        assert len(df) == 2
        assert "emdb_id" in df.columns
        assert "resolution" in df.columns
        assert df.iloc[0]["emdb_id"] == "EMD-1234"

    @responses.activate
    def test_csv_search_with_custom_fields(self):
        """Test CSV search with custom fields."""
        responses.add(
            responses.GET,
            "https://www.ebi.ac.uk/emdb/api/search/query",
            body="emdb_id,title\nEMD-1234,Test",
            status=200,
        )

        client = EMDB()
        df = client.csv_search("query", fields="emdb_id,title")

        # Check that the correct parameters were sent
        assert len(responses.calls) == 1
        request_url = responses.calls[0].request.url
        assert "fl=emdb_id%2Ctitle" in request_url or "fl=emdb_id,title" in request_url
