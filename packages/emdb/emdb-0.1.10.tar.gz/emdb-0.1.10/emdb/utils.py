import functools
import time

import requests
from emdb.exceptions import (
    EMDBAPIError, EMDBNotFoundError, EMDBRateLimitError, EMDBNetworkError
)


def fixed_sleep_rate_limit(min_interval_seconds: float):
    last_call = [0]

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < min_interval_seconds:
                time.sleep(min_interval_seconds - elapsed)
            result = func(*args, **kwargs)
            last_call[0] = time.time()
            return result
        return wrapper
    return decorator


def make_request(endpoint: str, params=None, restype="json", retries=3):
    url = f"https://www.ebi.ac.uk/emdb/api{endpoint}"

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 404:
                raise EMDBNotFoundError("Entry not found", 404, url)
            elif response.status_code == 429:
                raise EMDBRateLimitError("Rate limit exceeded", 429, url)
            elif response.status_code >= 500:
                raise EMDBAPIError("Server error", response.status_code, url)

            response.raise_for_status()
            if restype == "csv":
                return response.text.strip()
            else:
                return response.json()

        except requests.Timeout:
            if attempt < retries:
                time.sleep(attempt)
                continue
            raise EMDBNetworkError(f"Request timed out while accessing {url}")

        except requests.exceptions.RequestException as e:
            raise EMDBNetworkError(f"Network error while accessing {url}: {e}")

        except Exception as e:
            raise EMDBAPIError(f"An unexpected error occurred: {str(e)}", url=url)


