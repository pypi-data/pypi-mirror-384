"""Tool execution context."""

from typing import Optional

from fastapi import Request


class Context:
    """Context passed to tools during execution."""

    def __init__(self, token: Optional[str] = None, request: Optional[Request] = None):
        self.token = token
        self.request = request
