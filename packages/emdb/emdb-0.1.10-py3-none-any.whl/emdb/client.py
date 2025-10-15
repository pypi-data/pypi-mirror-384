import traceback
import pandas

from io import StringIO

from emdb.exceptions import EMDBInvalidIDError, EMDBNotFoundError, EMDBAPIError
from emdb.models.annotations import EMDBAnnotations
from emdb.models.entry import EMDBEntry
from emdb.models.search import EMDBSearchResults
from emdb.models.validation import EMDBValidation
from emdb.utils import make_request, fixed_sleep_rate_limit


class EMDB:
    """
    High-level EMDB API client.

    Usage:
        client = EMDB()
        entry = client.get_entry("EMD-1234")
    """

    @fixed_sleep_rate_limit(0.4)
    def get_entry(self, emdb_id: str) -> EMDBEntry:
        """
        Retrieve an EMDB entry by its ID.

        :param emdb_id: The EMDB ID of the entry to retrieve.
        :return: A dictionary containing the EMDB entry data.
        :raises EMDBNotFoundError: If the entry is not found.
        :raises EMDBInvalidIDError: If the provided EMDB ID is invalid.
        :raises EMDBAPIError: For other API-related errors.
        """
        if not emdb_id.startswith("EMD-"):
            raise EMDBInvalidIDError(emdb_id)

        endpoint = f"/entry/{emdb_id}"
        try:
            data = make_request(endpoint)
            return EMDBEntry.from_api(data, client=self)
        except EMDBNotFoundError as e:
            raise e
        except Exception as e:
            raise EMDBAPIError(f"Failed to retrieve entry {emdb_id}: {str(e)}")

    @fixed_sleep_rate_limit(0.4)
    def get_validation(self, emdb_id: str) -> "EMDBValidation":
        """
        Retrieve the validation data for a given EMDB entry.

        :param emdb_id: The EMDB ID of the entry to retrieve validation data for.
        :return: An EMDBValidation object containing the validation data.
        :raises EMDBNotFoundError: If the entry is not found.
        :raises EMDBAPIError: For API-related errors.
        """
        endpoint = f"/analysis/{emdb_id}"
        params = {"information": "all"}
        try:
            data = make_request(endpoint, params=params)
            return EMDBValidation.from_api(emdb_id, data, self)
        except EMDBNotFoundError as e:
            raise e
        except Exception as e:
            raise EMDBAPIError(f"Failed to retrieve validation for {emdb_id}: {str(e)}")

    @fixed_sleep_rate_limit(0.5)
    def get_annotations(self, emdb_id: str) -> EMDBAnnotations:
        """
        Retrieve annotations for a given EMDB entry.

        :param emdb_id: The EMDB ID of the entry to retrieve annotations for.
        :return: A dictionary containing the annotations data.
        :raises EMDBNotFoundError: If the entry is not found.
        :raises EMDBAPIError: For API-related errors.
        """
        endpoint = f"/annotations/{emdb_id}"
        try:
            data = make_request(endpoint)
            return EMDBAnnotations.from_api(data, self)
        except EMDBNotFoundError as e:
            raise e
        except Exception as e:
            raise EMDBAPIError(f"Failed to retrieve annotations for {emdb_id}: {str(e)}")

    def search(self, query: str) -> "EMDBSearchResults":
        """
        Search for EMDB entries using a query string.

        :param query: The search query string.
        :return: An EMDBSearchResults object containing the search results.
        :raises EMDBAPIError: For API-related errors.
        """
        endpoint = f"/search/{query}"
        params = {
            "rows": 1000000,
            "fl": "emdb_id",
            "wt": "csv",
            "download": "false"
        }
        try:
            data = make_request(endpoint, params=params, restype="csv")
            return EMDBSearchResults.from_api(data, self)
        except Exception as e:
            raise EMDBAPIError(f"Search failed: {str(e)}")

    @fixed_sleep_rate_limit(0.5)
    def csv_search(self, query: str, fields: str = "emdb_id,structure_determination_method,resolution") -> "pandas.DataFrame":
        """
        Perform a search returning the results in a CSV table (Pandas dataframe).

        :param query: The search query string.
        :param fields: Comma-separated list of fields to return.
        :return: A DataFrame containing the search results.
        :raises EMDBAPIError: For API-related errors.
        """
        endpoint = f"/search/{query}"
        params = {
            "rows": 1000000,
            "wt": "csv",
            "download": "false"
        }
        if fields:
            params["fl"] = fields

        try:
            data = make_request(endpoint, params=params, restype="csv")
            return pandas.read_csv(StringIO(data))
        except Exception as e:
            raise EMDBAPIError(f"Raw search failed: {str(e)}")


