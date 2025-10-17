from typing import Awaitable, Callable
from fastapi import Request
from nuc.envelope import NucTokenEnvelope


# Helper function to create a user_id extractor from various sources
class UserIdExtractors:
    """Common user ID extraction patterns"""

    @staticmethod
    def from_nuc_bearer_token() -> Callable[[Request], Awaitable[str]]:
        """Extract user ID from a NUC ID"""

        async def extractor(request: Request) -> str:
            auth_header: str | None = request.headers.get("Authorization", None)
            if not auth_header or not auth_header.startswith("Bearer "):
                raise ValueError("No Bearer token found")

            # Remove the Bearer prefix
            token_str: str = auth_header.replace("Bearer ", "")
            # Parse the token
            token = NucTokenEnvelope.parse(token_str)

            # Returns the issuer of the token
            return str(token.token.token.issuer)

        return extractor

    @staticmethod
    def from_nuc_bearer_root_token() -> Callable[[Request], Awaitable[str]]:
        """Extract user ID from a NUC root token"""

        async def extractor(request: Request) -> str:
            auth_header: str | None = request.headers.get("Authorization", None)
            if not auth_header or not auth_header.startswith("Bearer "):
                raise ValueError("No Bearer token found")

            # Remove the Bearer prefix
            token_str: str = auth_header.replace("Bearer ", "")
            # Parse the token
            token = NucTokenEnvelope.parse(token_str)
            # Returns the issuer of the token
            return str(token.proofs[-1].token.issuer)

        return extractor

    @staticmethod
    def from_header(
        header_name: str = "X-User-ID",
    ) -> Callable[[Request], Awaitable[str]]:
        """Extract user ID from a header"""

        async def extractor(request: Request) -> str:
            user_id = request.headers.get(header_name)
            if not user_id:
                raise ValueError(f"Header {header_name} not found")
            return user_id

        return extractor

    @staticmethod
    def from_query(query_name: str = "user_id") -> Callable[[Request], Awaitable[str]]:
        """Extract user ID from a query parameter"""

        async def extractor(request: Request) -> str:
            user_id = request.query_params.get(query_name) or request.path_params.get(
                query_name
            )
            if not user_id:
                raise ValueError(f"Query parameter {query_name} not found")
            return user_id

        return extractor

    @staticmethod
    def from_body(body_name: str = "user_id") -> Callable[[Request], Awaitable[str]]:
        """Extract user ID from a body parameter"""

        async def extractor(request: Request) -> str:
            body = await request.json()
            user_id = body.get(body_name)
            if not user_id:
                raise ValueError(f"Body parameter {body_name} not found")
            print(f"Extracted user ID from body: {user_id}")
            return user_id

        return extractor
