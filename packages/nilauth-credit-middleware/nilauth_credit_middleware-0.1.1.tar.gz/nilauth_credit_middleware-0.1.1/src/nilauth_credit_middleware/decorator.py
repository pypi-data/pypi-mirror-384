from typing import Callable, Any
from fastapi import Request, HTTPException
from functools import wraps
from nilauth_credit_middleware.credit_locking_client_singleton import (
    CreditClientSingleton,
)

from nilauth_credit_middleware.api_model import MeteringConfig
import logging

logger = logging.getLogger(__name__)


# Decorator for marking endpoints as metered
def metered(config: MeteringConfig):
    """
    Decorator to mark an endpoint as metered.

    Args:
            config.user_id_extractor: Async function that extracts user_id from the request.
                            Signature: async def extract_user_id(request: Request) -> str
            config.estimated_cost: The estimated cost to lock upfront (default: 1.0)
            config.cost_calculator: Optional async function to calculate actual cost after processing.
                            Signature: async def calculate_cost(request: Request, response: Response) -> float
                            If not provided, the estimated_cost will be charged.

    Example:
        async def get_user_from_header(request: Request) -> str:
            return request.headers.get("X-User-ID")

        async def calc_cost(request: Request, response: Response) -> float:
            # Calculate cost based on response size, processing time, etc.
            content_length = len(response.body) if hasattr(response, 'body') else 0
            return 0.1 + (content_length / 1000) * 0.01

        @app.post("/api/process")
        @metered(
            metering_config=MeteringConfig(
                user_id_extractor=get_user_from_header,
                estimated_cost=5.0,
                cost_calculator=calc_cost
            )
        )
        async def process_data(data: dict):
            return {"result": "processed"}
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Find the Request object in the arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break

            if request is None:
                raise ValueError("Request object not found in metered endpoint")

            # Get the singleton credit client
            try:
                credit_client = CreditClientSingleton.get_client()
            except RuntimeError as e:
                logger.error(f"Credit client not initialized: {e}")
                raise HTTPException(status_code=500, detail=str(e))

            # Extract user ID
            try:
                user_id = await config.credential_extractor(request)
                if not user_id:
                    raise HTTPException(
                        status_code=401, detail="User ID could not be determined"
                    )
                request.state.user_id = user_id
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to extract user ID: {e}")
                raise HTTPException(
                    status_code=401, detail=f"Failed to extract user ID: {str(e)}"
                )

            # Lock funds
            lock_response = None
            try:
                lock_response = await credit_client.lock_funds(
                    credential=user_id,
                    amount=config.estimated_cost,
                    use_public_endpoint=config.public_identifiers,
                )
                logger.info(
                    f"Locked {config.estimated_cost}$ for user {user_id}: {lock_response.lock_id}"
                )
                request.state.lock_id = lock_response.lock_id
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to lock funds: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to lock funds: {str(e)}"
                )

            # Execute the endpoint
            actual_cost = config.estimated_cost

            try:
                # Call the actual endpoint function
                result = await func(*args, **kwargs)
            except Exception as e:
                # On error in user function, unlock with 0 cost (full refund) and re-raise
                if lock_response:
                    try:
                        await credit_client.unlock_funds(lock_response.lock_id, 0.0)
                        logger.info(
                            f"Refunded full amount for lock {lock_response.lock_id} due to error"
                        )
                    except Exception as unlock_error:
                        logger.error(
                            f"Error unlocking funds after failure: {unlock_error}"
                        )
                raise e

            # Calculate actual cost if we have a cost calculator
            if config.cost_calculator:
                try:
                    actual_cost = await config.cost_calculator(request, result)
                    logger.info(f"Actual cost: {actual_cost}")
                except Exception as e:
                    logger.warning(f"Cost calculation failed: {e}")
                    actual_cost = config.estimated_cost
            else:
                logger.info(
                    f"No cost calculator provided, using estimated cost: {config.estimated_cost}"
                )
            # Unlock with actual cost
            logger.info(
                f"Unlocking funds for lock {request.state.lock_id} with cost {actual_cost}"
            )
            await credit_client.unlock_funds(request.state.lock_id, actual_cost)
            logger.info(
                f"Unlocked funds for lock {request.state.lock_id} with cost {actual_cost}"
            )

            return result

        # Store metering config as function attribute for inspection (optional, for introspection)
        setattr(wrapper, "_metering_config", config)

        return wrapper

    return decorator
