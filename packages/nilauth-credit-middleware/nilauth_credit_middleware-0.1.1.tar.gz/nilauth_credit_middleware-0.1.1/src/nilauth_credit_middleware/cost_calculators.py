from typing import TypeAlias
from fastapi import Request, Response
from pydantic import BaseModel


class LLMCost(BaseModel):
    prompt_tokens_price: float
    completion_tokens_price: float

    @staticmethod
    def default() -> "LLMCost":
        return LLMCost(prompt_tokens_price=0.0, completion_tokens_price=0.0)

    def total_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (
            self.prompt_tokens_price * prompt_tokens
            + self.completion_tokens_price * completion_tokens
        )


LLMCostDict: TypeAlias = dict[str, LLMCost]


# Helper functions for cost calculation
class CostCalculators:
    """Common cost calculation patterns"""

    @staticmethod
    def fixed_cost(amount: float):
        """Always charge a fixed cost"""

        async def calculator(request: Request, response: Response) -> float:
            return amount

        return calculator

    @staticmethod
    def by_response_size(base_cost: float = 0.1, per_kb: float = 0.01):
        """Calculate cost based on response size"""

        async def calculator(request: Request, response: Response) -> float:
            content_length = 0
            if hasattr(response, "body"):
                content_length = len(response.body)
            elif "content-length" in response.headers:
                content_length = int(response.headers["content-length"])

            size_kb = content_length / 1024.0
            return base_cost + (size_kb * per_kb)

        return calculator

    @staticmethod
    def by_processing_time(base_cost: float = 0.1, per_second: float = 0.5):
        """Calculate cost based on processing time"""
        import time

        async def calculator(request: Request, response: Response) -> float:
            start_time = getattr(request.state, "start_time", None)
            if start_time is None:
                return base_cost

            duration = time.time() - start_time
            return base_cost + (duration * per_second)

        return calculator

    # @staticmethod
    # def llm_cost_calculator(llm_cost_dict: dict[str, LLMCost]):
    #     async def calculator(request: Request, response: Response) -> float:
    #         model_name = getattr(request.state, 'model_name', 'default')
    #         llm_cost = llm_cost_dict.get(model_name, LLMCost.default())
    #         total_cost = 0.0
    #         response_body = response.content if hasattr(response, 'content') else ""
    #         import json
    #         response_data = json.loads(response_body)
    #         prompt_tokens = response_data.get("prompt_tokens", 0)
    #         completion_tokens = response_data.get("completion_tokens", 0)
    #         total_cost += llm_cost.total_cost(prompt_tokens, completion_tokens)
    #         return total_cost
    #     return calculator
