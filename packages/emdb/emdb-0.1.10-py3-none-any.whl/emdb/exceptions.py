class EMDBError(Exception):
    """Base exception for all EMDB wrapper errors."""
    pass


class EMDBAPIError(EMDBError):
    """Raised when there is an error with the EMDB API call."""
    def __init__(self, message: str, status_code: int = None, url: str = None):
        self.message = message
        self.status_code = status_code
        self.url = url
        full_msg = f"EMDB API Error: {message}"
        if status_code:
            full_msg += f" (Status code: {status_code})"
        if url:
            full_msg += f" [URL: {url}]"
        super().__init__(full_msg)


class EMDBNotFoundError(EMDBAPIError):
    """Raised when the requested EMDB entry is not found (404)."""
    pass


class EMDBInvalidIDError(EMDBError):
    """Raised when an invalid EMDB ID is provided."""
    def __init__(self, emdb_id: str):
        super().__init__(f"Invalid EMDB ID: {emdb_id}")


class EMDBNetworkError(EMDBError):
    """Raised for network-related issues (e.g., timeout, DNS failure)."""
    pass


class EMDBRateLimitError(EMDBAPIError):
    """Raised when the API rate limit is exceeded."""
    pass


class EMDBFileNotFoundError(EMDBError):
    """Raised when a requested file in an EMDB entry is not found."""
    def __init__(self, emdb_id: str, filename: str):
        super().__init__(f"File '{filename}' not found in EMDB entry {emdb_id}.")
        self.emdb_id = emdb_id
        self.filename = filename
