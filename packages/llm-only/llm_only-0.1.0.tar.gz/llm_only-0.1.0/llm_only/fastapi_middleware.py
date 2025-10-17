from starlette.middleware.base import BaseHTTPMiddleware
from .detector import is_llm_request

class LLMOnlyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        ua = request.headers.get("user-agent", "")
        if is_llm_request(ua, request.headers):
            request.state.is_llm = True
        else:
            request.state.is_llm = False
        response = await call_next(request)
        return response
