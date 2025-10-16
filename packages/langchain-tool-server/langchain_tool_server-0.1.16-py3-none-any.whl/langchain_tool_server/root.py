from fastapi import APIRouter
from typing_extensions import TypedDict

from langchain_tool_server._version import __version__


class InfoResponse(TypedDict):
    """Get information about the server."""

    version: str


class RootResponse(TypedDict):
    """Root endpoint response."""

    name: str
    version: str


class OkResponse(TypedDict):
    """Health check response."""

    ok: bool


router = APIRouter()


@router.get("/")
def index() -> RootResponse:
    """Get server name and version."""
    return {"name": "LangChain Tool Server", "version": __version__}


@router.get("/info")
def get_info() -> InfoResponse:
    """Get information about the server."""
    return {"version": __version__}


@router.get("/health")
def health() -> dict:
    """Are we OK?"""
    return {"status": "OK"}


@router.get("/ok")
def ok() -> OkResponse:
    """Simple health check endpoint."""
    return {"ok": True}
