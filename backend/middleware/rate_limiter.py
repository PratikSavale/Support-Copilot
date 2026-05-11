"""
Rate Limiter
Implements rate limiting for API endpoints.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

def setup_rate_limiter(app: FastAPI):
    """Setup rate limiting for the FastAPI app."""
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": 429,
                    "message": "Rate limit exceeded. Please try again later.",
                    "type": "rate_limit_error",
                }
            },
        )
    
    # Apply default rate limit to all endpoints
    # More specific limits can be applied per-endpoint
    DEFAULT_RATE_LIMIT = "100/minute"
