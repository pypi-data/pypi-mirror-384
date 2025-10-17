from typing import Optional
import httpx
from fastapi import HTTPException

from nilauth_credit_middleware.api_model import (
    LockFundsRequest,
    LockFundsResponse,
    UnlockFundsRequest,
    SummaryResponse,
)


class CreditLockingClient:
    """Client for interacting with the nilauth-credit service"""

    def __init__(self, base_url: str, api_token: str, timeout: float = 10.0):
        """
        Initialize the credit locking client.

        Args:
            base_url: Base URL of the nilauth-credit service (e.g., "http://localhost:3000")
            api_token: API token for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client"""
        return self._get_client()

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
            self._client.headers.update({"Authorization": f"Bearer {self.api_token}"})
        return self._client

    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def health(self) -> bool:
        """
        Check the health of the credit service.
        """
        client = self.client
        url = f"{self.base_url}/v1/health"
        response = await client.get(url)
        return response.status_code == 200

    async def summary(self) -> SummaryResponse:
        """
        Get the summary of the credit service.
        """
        client = self.client
        url = f"{self.base_url}/v1/summary"
        response = await client.get(url)
        return SummaryResponse(**response.json())

    async def lock_funds(
        self, credential: str, amount: float, use_public_endpoint: bool = False
    ) -> LockFundsResponse:
        """
        Lock funds using a credential.

        Args:
            credential: The credential key (private or public)
            amount: The amount to lock (estimated cost)
            use_public_endpoint: If True, uses the public lock endpoint

        Returns:
            The lock response with user_id and lock_id

        Raises:
            HTTPException: If the lock fails
        """
        client = self.client
        endpoint = "public" if use_public_endpoint else "private"
        url = f"{self.base_url}/v1/balance/lock/{endpoint}"

        request = LockFundsRequest(credential=credential, amount=amount)

        try:
            response = await client.post(
                url,
                json=request.model_dump(),
            )

            print(response.json())

            if response.status_code == 200:
                parsed_response = LockFundsResponse(**response.json())
                return parsed_response
            elif response.status_code == 404:
                error = response.json()
                raise HTTPException(
                    status_code=404, detail=f"User not found: {error.get('error')}"
                )
            elif response.status_code == 400:
                error = response.json()
                raise HTTPException(
                    status_code=402,
                    detail=f"Insufficient balance: {error.get('error')}",
                )
            else:
                error = response.json()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to lock funds: {error.get('error', 'Unknown error')}",
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"Credit service unavailable: {str(e)}"
            )

    async def unlock_funds(self, lock_id: str, real_cost: float) -> None:
        """
        Unlock funds and charge the real cost.

        Args:
            lock_id: The lock ID (UUID string)
            real_cost: The actual cost to charge

        Raises:
            HTTPException: If the unlock fails
        """
        client = self.client
        url = f"{self.base_url}/v1/balance/unlock"

        request = UnlockFundsRequest(lock_id=lock_id, real_cost=real_cost)

        try:
            response = await client.post(
                url,
                json=request.model_dump(),
            )

            if response.status_code == 200:
                return
            elif response.status_code == 404:
                error = response.json()
                raise HTTPException(
                    status_code=404, detail=f"Lock not found: {error.get('error')}"
                )
            elif response.status_code == 400:
                error = response.json()
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid unlock operation: {error.get('error')}",
                )
            else:
                error = response.json()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to unlock funds: {error.get('error', 'Unknown error')}",
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"Credit service unavailable: {str(e)}"
            )
