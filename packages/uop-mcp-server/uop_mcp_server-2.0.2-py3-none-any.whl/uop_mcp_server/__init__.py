"""
Unified Offer Protocol MCP Server - HTTP Client

This package provides a Python client for the UOP MCP Server.
The server runs as an HTTP endpoint - no local installation required.
"""

from .client import UOPMCPClient, MCP_ENDPOINT

__version__ = "2.0.0"
__all__ = ["UOPMCPClient", "MCP_ENDPOINT"]
