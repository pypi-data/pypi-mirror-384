from typing import Any, Dict, Optional, Union
import os
import httpx
import logging
from . import utils as _u

BASE_URL = os.getenv("GRID_CORTEX_BASE_URL", "https://cortex-prod.generalrobotics.dev/cortex")

# Remove basicConfig, as library logging should not configure root logger
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CortexAPIError(Exception):
    """Custom exception for API errors."""

    def __init__(
        self, status_code: int, message: str, details: Optional[Dict[str, Any]] = None
    ):  # Added details
        self.status_code = status_code
        self.message = message
        self.details = details  # Store details
        super().__init__(
            f"API Error {status_code}: {message} {details if details else ''}"
        )  # Optionally include details in main message


class CortexNetworkError(Exception):
    """Custom exception for network issues."""

    pass


class HTTPClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,  # Added base_url parameter
        timeout: float = 60.0,
    ):
        headers = {}
        if api_key is None:
            api_key = os.getenv("GRID_CORTEX_API_KEY")
            if not api_key:
                logger.warning(
                    "GRID_CORTEX_API_KEY environment variable not set. Client might not authenticate if API requires a key."
                )
                # Allow client to be initialized without API key if base_url is for a public/local service not requiring it
                # raise ValueError("GRID_CORTEX_API_KEY is not set. Please provide it or set the environment variable.")
            else:
                headers["x-api-key"] = api_key
        else:  # api_key is provided directly
            headers["x-api-key"] = api_key

        # Determine the final base URL
        final_base_url = base_url or os.getenv(
            "GRID_CORTEX_BASE_URL", "https://cortex-prod.generalrobotics.dev/cortex"
        )
        logger.info(f"HTTPClient initialized for base URL: {final_base_url}")

        self._client = httpx.Client(
            base_url=final_base_url, timeout=timeout, headers=headers
        )

    def post(
        self,
        path: str,
        *,
        json: Any = None,
        data: Union[Dict[str, Any], bytes, None] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,  # Added timeout parameter
    ) -> Dict[str, Any]:
        logger.info(f"POST {path}")
        try:
            # Pass timeout to httpx client's post method.
            # If timeout is None here, httpx will use the client's default timeout.
            if isinstance(data, bytes):
                # Assume msgpack – set header if not overridden
                headers = headers or {}
                headers.setdefault("Content-Type", "application/msgpack")
                resp = self._client.post(path, content=data, headers=headers, timeout=timeout)
            else:
                # JSON fall-back (legacy)
                headers = headers or {"Content-Type": "application/json"}
                resp = self._client.post(path, json=json, data=data, headers=headers, timeout=timeout)
            resp.raise_for_status()
            logger.info(f"POST {path} successful ({resp.status_code})")
            ctype = resp.headers.get("content-type", "")
            if "msgpack" in ctype or "octet-stream" in ctype:
                return _u.unpackb(resp.content)
            else:
                return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP Status Error for {path}: {e.response.status_code} - {e.response.text}"
            )
            error_details_dict: Optional[Dict[str, Any]] = None
            try:
                error_details_dict = e.response.json()

                # Use 'detail' key if present, otherwise use the full JSON or raw text
                error_message = error_details_dict.get(
                    "detail", str(error_details_dict)
                )  # Use str(error_details_dict) if 'detail' is missing
            except ValueError:  # If response is not JSON
                error_message = e.response.text
            raise CortexAPIError(
                status_code=e.response.status_code,
                message=error_message,
                details=error_details_dict,
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Request Error for {path}: {e}")
            raise CortexNetworkError(
                f"Network request to {e.request.url} failed: {e}"
            ) from e

    def close(self) -> None:
        logger.info("Closing HTTPClient.")
        self._client.close()
