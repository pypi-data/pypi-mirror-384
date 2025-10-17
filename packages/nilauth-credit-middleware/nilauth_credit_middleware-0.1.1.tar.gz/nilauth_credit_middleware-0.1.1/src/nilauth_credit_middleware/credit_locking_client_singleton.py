from typing import Optional
from nilauth_credit_middleware.credit_locking_client import CreditLockingClient
import logging

logger = logging.getLogger(__name__)


class CreditClientSingleton:
    """
    Singleton class for managing the CreditLockingClient instance.

    Initialize once with configure(), then access via get_client().
    """

    _credit_client: Optional[CreditLockingClient] = None

    @classmethod
    def configure(cls, base_url: str, api_token: str, timeout: float = 10.0) -> None:
        """
        Configure and initialize the singleton credit client.

        Args:
            base_url: Base URL of the nilauth-credit service
            api_token: API token for authentication
            timeout: Request timeout in seconds
        """
        if cls._credit_client is None:
            cls._credit_client = CreditLockingClient(
                base_url=base_url, api_token=api_token, timeout=timeout
            )
            logger.info(f"Initialized credit client with base_url={base_url}")
        else:
            logger.warning("Credit client already configured, ignoring reconfiguration")

    @classmethod
    def get_client(cls) -> CreditLockingClient:
        """
        Get the singleton credit client instance.

        Returns:
            The configured CreditLockingClient instance

        Raises:
            RuntimeError: If the client hasn't been configured yet
        """
        if cls._credit_client is None:
            raise RuntimeError(
                "CreditClientSingleton not configured. "
                "Call CreditClientSingleton.configure(base_url, api_token) before using @metered"
            )
        return cls._credit_client
