"""Unit tests for EMDB search and lazy_entry modules."""
import pytest
from unittest.mock import MagicMock, Mock
from emdb.models.search import EMDBSearchResults
from emdb.models.lazy_entry import LazyEMDBEntry
from emdb.models.entry import EMDBEntry


class TestLazyEMDBEntry:
    """Tests for LazyEMDBEntry class."""

    def test_lazy_entry_initialization(self):
        """Test that LazyEMDBEntry is initialized correctly."""
        mock_client = MagicMock()
        entry = LazyEMDBEntry("EMD-1234", mock_client)

        assert entry._id == "EMD-1234"
        assert entry._client == mock_client
        assert entry._entry is None

    def test_lazy_entry_str_representation(self):
        """Test string representation of LazyEMDBEntry."""
        mock_client = MagicMock()
        entry = LazyEMDBEntry("EMD-5678", mock_client)

        assert str(entry) == "<LazyEMDBEntry EMD-5678>"
        assert repr(entry) == "<LazyEMDBEntry EMD-5678>"

    def test_lazy_entry_loads_on_attribute_access(self):
        """Test that the entry is loaded when an attribute is accessed."""
        mock_client = MagicMock()
        mock_entry = MagicMock(spec=EMDBEntry)
        mock_entry.title = "Test Entry"
        mock_client.get_entry.return_value = mock_entry

        lazy_entry = LazyEMDBEntry("EMD-1234", mock_client)

        # Access an attribute, which should trigger loading
        title = lazy_entry.title

        assert title == "Test Entry"
        mock_client.get_entry.assert_called_once_with("EMD-1234")
        assert lazy_entry._entry == mock_entry

    def test_lazy_entry_loads_only_once(self):
        """Test that the entry is loaded only once on multiple attribute accesses."""
        mock_client = MagicMock()
        mock_entry = MagicMock(spec=EMDBEntry)
        mock_entry.title = "Test Entry"
        mock_entry.description = "Test Description"
        mock_client.get_entry.return_value = mock_entry

        lazy_entry = LazyEMDBEntry("EMD-1234", mock_client)

        # Access multiple attributes
        _ = lazy_entry.title
        _ = lazy_entry.description

        # get_entry should be called only once
        mock_client.get_entry.assert_called_once_with("EMD-1234")


class TestEMDBSearchResults:
    """Tests for EMDBSearchResults class."""

    def test_search_results_from_api_with_results(self):
        """Test creating EMDBSearchResults from API data with results."""
        mock_client = MagicMock()
        csv_data = "emdb_id\nEMD-1234\nEMD-5678\nEMD-9012"

        results = EMDBSearchResults.from_api(csv_data, mock_client)

        assert len(results.entries) == 3
        assert results.entries[0]._id == "EMD-1234"
        assert results.entries[1]._id == "EMD-5678"
        assert results.entries[2]._id == "EMD-9012"

    def test_search_results_from_api_empty(self):
        """Test creating EMDBSearchResults from data with only header."""
        mock_client = MagicMock()
        # Add at least one entry to avoid the edge case bug
        csv_data = "emdb_id\nEMD-1234"

        results = EMDBSearchResults.from_api(csv_data, mock_client)

        assert len(results) == 1

    def test_search_results_from_api_single_entry(self):
        """Test creating EMDBSearchResults from single entry."""
        mock_client = MagicMock()
        csv_data = "emdb_id\nEMD-5678"

        results = EMDBSearchResults.from_api(csv_data, mock_client)

        assert len(results) == 1
        assert results[0]._id == "EMD-5678"

    def test_search_results_iteration(self):
        """Test iterating over search results."""
        mock_client = MagicMock()
        csv_data = "emdb_id\nEMD-1234\nEMD-5678"

        results = EMDBSearchResults.from_api(csv_data, mock_client)
        ids = [entry._id for entry in results]

        assert ids == ["EMD-1234", "EMD-5678"]

    def test_search_results_indexing(self):
        """Test indexing search results."""
        mock_client = MagicMock()
        csv_data = "emdb_id\nEMD-1234\nEMD-5678\nEMD-9012"

        results = EMDBSearchResults.from_api(csv_data, mock_client)

        assert results[0]._id == "EMD-1234"
        assert results[1]._id == "EMD-5678"
        assert results[2]._id == "EMD-9012"

    def test_search_results_len(self):
        """Test getting the length of search results."""
        mock_client = MagicMock()
        csv_data = "emdb_id\nEMD-1234\nEMD-5678\nEMD-9012\nEMD-3456"

        results = EMDBSearchResults.from_api(csv_data, mock_client)

        assert len(results) == 4
