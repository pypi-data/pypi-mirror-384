import time
import requests
from typing import Dict, Optional

from .exceptions import (
    TsPayError,
    AuthenticationError,
    TransactionNotFound,
    InvalidRequestError,
    NetworkError,
    ServerError,
)


class TsPayClient:
    """Official Python client for TsPay (works with merchant access_token only)"""

    BASE_URL = "https://tspay.uz/api/v1"

    def __init__(
        self,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 3.0,
    ):
        """
        :param base_url: Base API URL
        :param max_retries: Number of retry attempts when 429 is returned
        :param retry_delay: Wait time (in seconds) before retrying
        """
        self.base_url = base_url or self.BASE_URL
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    # ---------------------
    #  Private helpers
    # ---------------------

    def _get_headers(self, access_token: str = None) -> Dict[str, str]:
        """Generate request headers that Cloudflare won’t block"""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "Origin": "https://tspay.uz",
            "Referer": "https://tspay.uz/",
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    def _handle_response(self, response: requests.Response):
        """Validate response and raise detailed exceptions"""
        status = response.status_code

        if status == 401:
            raise AuthenticationError(status_code=401, details=response.text)
        if status == 404:
            raise TransactionNotFound(status_code=404, details=response.text)
        if status == 400:
            raise InvalidRequestError(status_code=400, details=response.text)
        if status >= 500:
            raise ServerError(status_code=status, details=response.text)
        if status == 429:
            raise TsPayError("Cloudflare rate-limited this request (429 Too Many Requests)", status_code=429)

        try:
            return response.json()
        except ValueError:
            raise InvalidRequestError("Invalid JSON response", details={"raw": response.text})

    # ---------------------
    #  Public methods
    # ---------------------

    def create_transaction(
        self,
        amount: float,
        access_token: str,
        redirect_url: str = "",
        comment: str = ""
    ) -> Dict:
        """Create a new transaction using the merchant access_token"""
        url = f"{self.base_url}/transactions/create/"

        if not access_token:
            raise AuthenticationError("Missing merchant access_token")

        data = {
            "amount": amount,
            "redirect_url": redirect_url,
            "comment": comment,
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(url, json=data)

                # Retry on Cloudflare 429
                if response.status_code == 429 and attempt < self.max_retries:
                    print(f"⚠️ 429 Too Many Requests – retrying in {self.retry_delay}s (attempt {attempt}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                    continue

                result = self._handle_response(response)
                if not result.get("transaction"):
                    raise TsPayError("Transaction data missing in response", details=result)
                return result["transaction"]

            except requests.RequestException as e:
                raise NetworkError(f"Network error while creating transaction: {str(e)}")

        raise TsPayError("Max retry attempts reached (429)", status_code=429)

    def check_transaction(self, access_token: str, cheque_id: str) -> Dict:
        """Check transaction status (by cheque_id)"""
        if not cheque_id:
            raise InvalidRequestError("Missing cheque_id")

        url = f"{self.base_url}/transactions/{cheque_id}/"

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(url, headers=self._get_headers(access_token))

                if response.status_code == 429 and attempt < self.max_retries:
                    print(f"⚠️ 429 Too Many Requests – retrying in {self.retry_delay}s (attempt {attempt}/{self.max_retries})")
                    time.sleep(self.retry_delay)
                    continue

                return self._handle_response(response)

            except requests.RequestException as e:
                raise NetworkError(f"Network error while checking transaction: {str(e)}")

        raise TsPayError("Max retry attempts reached (429)", status_code=429)