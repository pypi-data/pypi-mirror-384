"""
AII API Module - HTTP Server for programmatic access.

Provides:
- RESTful API for function execution
- WebSocket streaming for real-time responses
- API key authentication
- Rate limiting per key
- OpenAPI documentation
"""

from aii.api.server import APIServer, generate_api_key

__all__ = ["APIServer", "generate_api_key"]
