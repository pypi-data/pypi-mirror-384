from flask import request
from functools import wraps
from .detector import is_llm_request

def llm_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        ua = request.headers.get("User-Agent", "")
        if is_llm_request(ua, request.headers):
            return func(*args, **kwargs)
        return ""
    return wrapper
