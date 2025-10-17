from typing import Callable, Any, Optional, AsyncGenerator
from fastapi import Request, HTTPException
from nilauth_credit_middleware.credit_locking_client_singleton import (
    CreditClientSingleton,
)
from nilauth_credit_middleware.credit_locking_client import CreditLockingClient
from nilauth_credit_middleware.api_model import MeteringConfig
import logging

logger = logging.getLogger(__name__)


class MeteringContext:
    """Context object yielded by metering dependency."""

    def __init__(self, request: Request, user_id: str, lock_id: str):
        self.request = request
        self.user_id = user_id
        self.lock_id = lock_id
        self.response_data: Optional[Any] = None

    def set_response(self, response_data: Any) -> None:
        """Set the response data for cost calculation."""
        self.response_data = response_data


class MeteringDependency:
    """
    FastAPI dependency for metering API endpoints using yield pattern.

    Example:
        metering = MeteringDependency(
            config=MeteringConfig(
                user_id_extractor=lambda r: r.headers.get("X-User-ID"),
                estimated_cost=5.0,
                cost_calculator=lambda r, data: len(str(data)) * 0.01
            )
        )

        @app.post("/process")
        async def process_data(
            data: dict,
            meter: MeteringContext = Depends(metering)
        ):
            result = {"result": "processed"}
            meter.set_response(result)
            return result
    """

    def __init__(self, config: MeteringConfig):
        self.config = config

    async def __call__(self, request: Request) -> AsyncGenerator[MeteringContext, None]:
        """Lock funds, yield context, then unlock with actual cost."""
        credit_client = self._get_credit_client()
        user_credential = await self._extract_user_id(request)  # Validate user_id extraction works
        user_id, lock_id = await self._lock_funds(credit_client, user_credential)

        request.state.user_id = user_id
        request.state.lock_id = lock_id

        meter = MeteringContext(request, user_id, lock_id)

        try:
            yield meter
        except Exception:
            await self._refund_funds(credit_client, lock_id, user_id)
            raise
        else:
            actual_cost = await self._calculate_cost(request, meter.response_data)
            await self._unlock_funds(credit_client, lock_id, user_id, actual_cost)

    def _get_credit_client(self) -> CreditLockingClient:
        """Get the credit client singleton."""
        try:
            return CreditClientSingleton.get_client()
        except RuntimeError as e:
            logger.error(f"Credit client not initialized: {e}")
            raise HTTPException(status_code=500, detail="Credit service unavailable")

    async def _extract_user_id(self, request: Request) -> str:
        """Extract and validate user ID from request."""
        try:
            user_id = await self.config.credential_extractor(request)
            if not user_id:
                raise HTTPException(status_code=401, detail="User ID not found")
            return user_id
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User ID extraction failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid authentication")

    async def _lock_funds(self, client: CreditLockingClient, user_id: str) -> tuple[str, str]:
        """Lock funds and return (user_id, lock_id) tuple."""
        try:
            response = await client.lock_funds(
                credential=user_id,
                amount=self.config.estimated_cost,
                use_public_endpoint=self.config.public_identifiers,
            )
            logger.info(
                f"Locked ${self.config.estimated_cost} for user {user_id} with lock {response.lock_id}"
            )
            return (user_id, response.lock_id)
        except Exception as e:
            logger.error(f"Fund locking failed: {e}")
            raise HTTPException(status_code=402, detail="Insufficient funds")

    async def _calculate_cost(
        self, request: Request, response_data: Optional[Any]
    ) -> float:
        """Calculate actual cost or return estimated cost."""
        if not self.config.cost_calculator or response_data is None:
            # If no cost calculator is provided, or the response data is None, return the estimated cost
            # response_data is None when the endpoint interrupted before returning a response
            logger.info(f"No cost calculator provided, using {self.config.default_cost_percentage * 100}% of estimated cost: {self.config.estimated_cost * self.config.default_cost_percentage}")
            return self.config.estimated_cost * self.config.default_cost_percentage

        try:
            final_cost: float = await self.config.cost_calculator(request, response_data)
            if final_cost < 0 or final_cost > self.config.estimated_cost:
                logger.warning(f"Cost calculation yields invalid value, using estimate: {final_cost}")
                return self.config.estimated_cost
            return final_cost
        except Exception as e:
            logger.warning(f"Cost calculation failed, using estimate: {e}")
            return self.config.estimated_cost

    async def _unlock_funds(
        self, client: CreditLockingClient, lock_id: str, user_id: str, cost: float
    ) -> None:
        """Unlock funds with actual cost."""
        await client.unlock_funds(lock_id, cost)
        logger.info(f"Charged ${cost} to user {user_id}")

    async def _refund_funds(
        self, client: CreditLockingClient, lock_id: str, user_id: str
    ) -> None:
        """Refund all locked funds on error."""
        try:
            await client.unlock_funds(lock_id, 0.0)
            logger.info(f"Refunded user {user_id} due to error")
        except Exception as e:
            logger.error(f"Refund failed for user {user_id}: {e}")


def create_metering_dependency(
    credential_extractor: Callable[[Request], Any],
    estimated_cost: float = 1.0,
    cost_calculator: Optional[Callable[[Request, Any], Any]] = None,
    default_cost_percentage: Optional[float] = 0.1,
    public_identifiers: bool = False,
) -> MeteringDependency:
    """
    Factory function to create a MeteringDependency instance.

    Args:
        credential_extractor: Async function that extracts user_id from request
        credential: Credential key for locking funds
        estimated_cost: The estimated cost to lock upfront (default: 1.0)
        cost_calculator: Optional async function to calculate actual cost
        default_cost_percentage: Default cost percentage (default: 0.1)
        public_identifiers: If True, uses public lock endpoint (default: False)

    Returns:
        MeteringDependency instance ready to use with Depends()

    Example:
        async def get_user(request: Request) -> str:
            return request.headers.get("X-User-ID")

        async def calc_cost(request: Request, response_data: Any) -> float:
            return 0.1 + len(str(response_data)) / 1000 * 0.01

        metering = create_metering_dependency(
            credential_extractor=get_user,
            credential="cred_user1_private",
            estimated_cost=10.0,
            cost_calculator=calc_cost
        )

        @app.post("/process")
        async def endpoint(
            data: dict,
            meter: MeteringContext = Depends(metering)
        ):
            result = {"result": "processed"}
            meter.set_response(result)
            return result
    """
    config = MeteringConfig(
        credential_extractor=credential_extractor,
        estimated_cost=estimated_cost,
        cost_calculator=cost_calculator,
        default_cost_percentage=default_cost_percentage,
        public_identifiers=public_identifiers,
    )
    return MeteringDependency(config)
