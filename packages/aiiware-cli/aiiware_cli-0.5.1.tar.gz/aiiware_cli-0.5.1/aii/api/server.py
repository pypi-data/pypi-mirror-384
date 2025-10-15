"""
FastAPI-based HTTP server for AII API mode.

Features:
- RESTful API for function execution
- WebSocket streaming for real-time responses
- API key authentication
- Rate limiting per key
- CORS support for web integrations
- OpenAPI documentation
"""

from fastapi import FastAPI, HTTPException, Depends, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import logging
from typing import Optional
from datetime import datetime
import secrets

logger = logging.getLogger(__name__)

from aii.core.engine import AIIEngine
from aii.core.models import ExecutionResult
from aii.config.manager import ConfigManager
from aii.cli.output_mode_formatter import OutputMode
from aii.api.models import (
    ExecuteRequest, ExecuteResponse,
    FunctionsResponse, FunctionInfo,
    StatusResponse, MCPStatusRequest
)


def format_completion_metadata(result: ExecutionResult) -> dict:
    """
    Extract token metadata from ExecutionResult for API completion responses.

    Ensures parity between REST and WebSocket API metadata structure.
    Resolves AII-CLI-WS-001: WebSocket token metadata bug.

    Args:
        result: ExecutionResult from function execution

    Returns:
        dict: Formatted metadata with tokens, cost, model, execution_time

    Example:
        >>> result = ExecutionResult(...)
        >>> metadata = format_completion_metadata(result)
        >>> metadata
        {
            "tokens": {"input": 245, "output": 182},
            "cost": 0.0042,
            "model": "gemini-2.0-flash-exp",
            "execution_time": 3.94
        }
    """
    # Initialize metadata dict
    metadata = {
        "execution_time": getattr(result, "execution_time", None)
    }

    # Extract result data (functions store token info in result.data dict)
    result_data = result.data if result.data else {}

    # Extract token usage from result.data
    # Functions store tokens as 'input_tokens' and 'output_tokens'
    input_tokens = result_data.get("input_tokens")
    output_tokens = result_data.get("output_tokens")

    # Add tokens if available (both must be present)
    if input_tokens is not None and output_tokens is not None:
        metadata["tokens"] = {
            "input": int(input_tokens) if input_tokens is not None else 0,
            "output": int(output_tokens) if output_tokens is not None else 0
        }
    else:
        metadata["tokens"] = None

    # Extract cost (may be in result.data or calculated separately)
    cost = result_data.get("cost") or result_data.get("estimated_cost")
    metadata["cost"] = float(cost) if cost is not None else None

    # Extract model name
    model = result_data.get("model") or result_data.get("provider")
    if model:
        metadata["model"] = str(model)

    # Extract confidence (optional, if available)
    confidence = result_data.get("confidence")
    if confidence is not None:
        metadata["confidence"] = float(confidence)

    return metadata


app = FastAPI(
    title="AII API",
    description="AI-powered command-line assistant API",
    version="0.5.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for web integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Make configurable via config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class APIKeyAuth:
    """API key authentication handler."""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.api_keys = self._load_api_keys()

    def _load_api_keys(self) -> set[str]:
        """Load API keys from config."""
        keys = self.config.get("api.keys", [])
        return set(keys)

    def verify_key(self, api_key: str) -> bool:
        """Verify API key is valid."""
        return api_key in self.api_keys

    def add_key(self, api_key: str):
        """Add new API key and persist to config."""
        self.api_keys.add(api_key)

        # Persist to config
        keys = list(self.api_keys)
        self.config.set("api.keys", keys)


class RateLimiter:
    """Rate limiter per API key."""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.limits: Dict[str, tuple[int, datetime]] = {}  # api_key -> (count, window_start)
        self.max_requests = config.get("api.rate_limit.max_requests", 100)
        self.window_seconds = config.get("api.rate_limit.window_seconds", 60)

    def allow(self, api_key: str) -> bool:
        """Check if request is allowed under rate limit."""
        now = datetime.now()

        if api_key not in self.limits:
            self.limits[api_key] = (1, now)
            return True

        count, window_start = self.limits[api_key]

        # Check if window expired
        if (now - window_start).total_seconds() > self.window_seconds:
            # Reset window
            self.limits[api_key] = (1, now)
            return True

        # Check if limit exceeded
        if count >= self.max_requests:
            return False

        # Increment count
        self.limits[api_key] = (count + 1, window_start)
        return True

    def get_remaining(self, api_key: str) -> int:
        """Get remaining requests in current window."""
        if api_key not in self.limits:
            return self.max_requests

        count, window_start = self.limits[api_key]
        now = datetime.now()

        # Window expired
        if (now - window_start).total_seconds() > self.window_seconds:
            return self.max_requests

        return max(0, self.max_requests - count)


class APIServer:
    """
    HTTP server for AII API mode.

    Lifecycle:
    1. Initialize with AIIEngine and ConfigManager
    2. Start server with uvicorn
    3. Handle requests with authentication and rate limiting
    4. Shutdown gracefully

    Security:
    - API key authentication via AII-API-Key header
    - Rate limiting per key (100 req/min default)
    - Request/response logging
    - CORS configuration
    """

    def __init__(self, engine: AIIEngine, config: ConfigManager, initialization_status: dict = None):
        self.engine = engine
        self.config = config
        self.rate_limiter = RateLimiter(config)
        self.auth = APIKeyAuth(config)
        self.start_time = datetime.now()
        self.server: Optional[uvicorn.Server] = None
        # Track initialization status for client guidance
        self.initialization_status = initialization_status or {
            "llm_provider": True,  # Assume initialized by default
            "llm_error": None,
            "web_search": False,
            "web_error": None
        }

    async def start_server(self, host: str = "0.0.0.0", port: int = 8080):
        """Start HTTP server with uvicorn."""
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        self.server = uvicorn.Server(config)

        # Start server
        await self.server.serve()

    async def shutdown(self):
        """Graceful shutdown."""
        if self.server:
            self.server.should_exit = True

    def get_uptime(self) -> float:
        """Get server uptime in seconds."""
        return (datetime.now() - self.start_time).total_seconds()


# Global server instance (set by start_api_server)
server: Optional[APIServer] = None


def generate_api_key() -> str:
    """Generate random API key with strong entropy."""
    return f"aii_sk_{secrets.token_urlsafe(32)}"


# Authentication middleware
async def verify_api_key(aii_api_key: str = Header(None, alias="AII-API-Key")) -> str:
    """Verify API key from AII-API-Key header."""
    if not aii_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include AII-API-Key header."
        )

    if not server or not server.auth.verify_key(aii_api_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return aii_api_key


# Rate limiting middleware
async def check_rate_limit(api_key: str = Depends(verify_api_key)):
    """Check rate limit for API key."""
    if not server:
        return

    if not server.rate_limiter.allow(api_key):
        remaining = server.rate_limiter.get_remaining(api_key)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. {remaining} requests remaining.",
            headers={
                "X-RateLimit-Limit": str(server.rate_limiter.max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(server.rate_limiter.window_seconds)
            }
        )


# POST /api/execute - Execute function
@app.post("/api/execute", response_model=ExecuteResponse)
async def execute_function(
    request: ExecuteRequest,
    api_key: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Execute AII function with parameters.

    Example:
    ```bash
    curl -X POST http://localhost:16169/api/execute \\
      -H "Content-Type: application/json" \\
      -H "AII-API-Key: aii_sk_..." \\
      -d '{
        "function": "translate",
        "params": {"text": "hello", "to": "spanish"}
      }'
    ```

    Response:
    ```json
    {
      "success": true,
      "result": "hola",
      "metadata": {
        "tokens": {"input": 145, "output": 28},
        "cost": 0.0004,
        "execution_time": 1.23
      }
    }
    ```
    """

    if not server:
        raise HTTPException(status_code=500, detail="Server not initialized")

    try:
        # For API mode, use function name directly from request
        # API clients specify the function explicitly, no need for intent recognition
        from aii.core.models import RecognitionResult, RouteSource

        function_name = request.function
        parameters = request.params or {}

        # Validate function exists
        if function_name not in server.engine.function_registry.plugins:
            raise HTTPException(
                status_code=404,
                detail=f"Function '{function_name}' not found"
            )

        # Create recognition result for API execution
        recognition_result = RecognitionResult(
            intent=function_name,
            confidence=1.0,  # API clients explicitly specify function
            parameters=parameters,
            function_name=function_name,
            requires_confirmation=False,  # API execution doesn't require confirmation
            reasoning="Direct API invocation",
            source=RouteSource.DIRECT_MATCH
        )

        # Execute function via execution engine
        result = await server.engine.execution_engine.execute_function(
            recognition_result=recognition_result,
            user_input=request.get_formatted_input(),
            chat_context=None,
            config=server.engine.config,
            llm_provider=server.engine.llm_provider,
            web_client=server.engine.web_client,
            mcp_client=server.engine.mcp_client,
            offline_mode=False
        )

        return ExecuteResponse(
            success=result.success,
            result=result.data if result.success else None,
            error=result.message if not result.success else None,
            metadata=format_completion_metadata(result)
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


# GET /api/functions - List available functions
@app.get("/api/functions", response_model=FunctionsResponse)
async def list_functions(
    api_key: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    List all available AII functions.

    Response:
    ```json
    {
      "functions": [
        {
          "name": "translate",
          "description": "Translate text to another language",
          "parameters": {...},
          "safety": "safe",
          "default_output_mode": "clean"
        }
      ]
    }
    ```
    """

    if not server:
        raise HTTPException(status_code=500, detail="Server not initialized")

    # Get all registered plugins
    plugins = server.engine.function_registry.plugins.values()

    functions_list = []
    for f in plugins:
        # Handle different attribute names (function_name vs name)
        name = getattr(f, 'function_name', None) or getattr(f, 'name', 'unknown')
        description = getattr(f, 'function_description', None) or getattr(f, 'description', '')

        # Get default output mode safely
        default_mode = None
        if hasattr(f, 'default_output_mode'):
            mode_attr = getattr(f, 'default_output_mode', None)
            if mode_attr and hasattr(mode_attr, 'value'):
                default_mode = mode_attr.value

        functions_list.append(FunctionInfo(
            name=name,
            description=description,
            parameters=f.get_parameters_schema() if hasattr(f, 'get_parameters_schema') else {},
            safety=f.get_function_safety().value if hasattr(f, 'get_function_safety') else 'unknown',
            default_output_mode=default_mode
        ))

    return FunctionsResponse(functions=functions_list)


# GET /api/status - Server status (no auth required)
@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """
    Get server health status.

    No authentication required for status endpoint.

    Response:
    ```json
    {
      "status": "healthy",
      "version": "0.4.12",
      "uptime": 3600.5,
      "mcp_servers": {
        "total": 7,
        "enabled": 7
      }
    }
    ```
    """

    if not server:
        return StatusResponse(
            status="initializing",
            version="0.5.1",
            uptime=0.0
        )

    mcp_info = None
    try:
        # Load MCP server config from mcp_servers.json
        from pathlib import Path
        import json

        mcp_config_path = Path.home() / ".aii" / "mcp_servers.json"
        if mcp_config_path.exists():
            with open(mcp_config_path, "r") as f:
                config = json.load(f)
                servers = config.get("mcpServers", {})

                # Count total and enabled servers
                total = len(servers)
                enabled = sum(1 for s in servers.values() if s.get("enabled", True))

                mcp_info = {
                    "total": total,
                    "enabled": enabled
                }
    except Exception as e:
        # Silently fail for status endpoint
        logger.debug(f"Failed to load MCP server info: {e}")
        pass

    return StatusResponse(
        status="healthy",
        version="0.5.1",
        uptime=server.get_uptime(),
        mcp_servers=mcp_info,
        initialization=server.initialization_status
    )


# POST /api/mcp/status - Get MCP server health
@app.post("/api/mcp/status")
async def mcp_status(
    request: MCPStatusRequest,
    api_key: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Get health status for MCP servers.

    Request:
    ```json
    {
      "server_name": "github"  // optional, null for all
    }
    ```
    """

    if not server:
        raise HTTPException(status_code=500, detail="Server not initialized")

    # Execute mcp_status function if available
    try:
        result = await server.engine.process_input(
            user_input=f"mcp status {request.server_name or ''}",
            context=None
        )

        if result.success:
            return result.data
        else:
            raise HTTPException(status_code=500, detail=result.message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for streaming
@app.websocket("/ws/execute")
async def websocket_execute(websocket: WebSocket):
    """
    WebSocket endpoint for streaming function execution.

    Protocol:
    ```
    Client → Server: {"api_key": "...", "function": "translate", "params": {...}}
    Server → Client: {"type": "token", "data": "h"}
    Server → Client: {"type": "token", "data": "o"}
    Server → Client: {"type": "token", "data": "l"}
    Server → Client: {"type": "token", "data": "a"}
    Server → Client: {"type": "complete", "metadata": {...}}
    ```

    Error handling:
    ```
    Server → Client: {"type": "error", "message": "..."}
    ```
    """

    await websocket.accept()

    try:
        # Receive request
        data = await websocket.receive_json()

        # Verify API key
        api_key = data.get("api_key")
        if not api_key or not server or not server.auth.verify_key(api_key):
            await websocket.send_json({
                "type": "error",
                "message": "Invalid or missing API key"
            })
            await websocket.close()
            return

        # Check rate limit
        if not server.rate_limiter.allow(api_key):
            await websocket.send_json({
                "type": "error",
                "message": "Rate limit exceeded"
            })
            await websocket.close()
            return

        # Format input from WebSocket request (same as REST API)
        from aii.core.models import RecognitionResult, RouteSource

        function_name = data.get("function", "")
        parameters = data.get("params", {})

        # Validate function exists
        if function_name not in server.engine.function_registry.plugins:
            await websocket.send_json({
                "type": "error",
                "message": f"Function '{function_name}' not found"
            })
            return

        # Check if LLM provider is required but not initialized
        if not server.initialization_status.get("llm_provider"):
            # Check if this function requires LLM
            function_plugin = server.engine.function_registry.plugins.get(function_name)
            requires_llm = hasattr(function_plugin, 'requires_llm') and function_plugin.requires_llm

            # Most functions require LLM, so assume yes unless explicitly stated
            if requires_llm or not hasattr(function_plugin, 'requires_llm'):
                llm_error = server.initialization_status.get("llm_error", "Unknown error")
                await websocket.send_json({
                    "type": "error",
                    "message": "Prerequisites not met: LLM provider required",
                    "details": {
                        "reason": "LLM provider not initialized",
                        "error": llm_error,
                        "guidance": "To set up AII, run: aii config init\n(Takes ~2 minutes)"
                    }
                })
                await websocket.close()
                return

        # Create recognition result for direct API invocation
        recognition_result = RecognitionResult(
            intent=function_name,
            confidence=1.0,
            parameters=parameters,
            function_name=function_name,
            requires_confirmation=False,
            reasoning="Direct WebSocket invocation",
            source=RouteSource.DIRECT_MATCH
        )

        # Create streaming callback for real-time token delivery
        async def streaming_callback(token: str):
            """Send each token immediately to the client"""
            try:
                await websocket.send_json({
                    "type": "token",
                    "data": token
                })
            except Exception as e:
                # WebSocket may have disconnected
                print(f"Failed to send token via WebSocket: {e}")

        # Pass streaming callback to execution engine
        # The engine will use it for LLM streaming if available
        result = await server.engine.execution_engine.execute_function(
            recognition_result=recognition_result,
            user_input=f"{function_name} {parameters}",
            chat_context=None,
            config=server.engine.config,
            llm_provider=server.engine.llm_provider,
            web_client=server.engine.web_client,
            mcp_client=server.engine.mcp_client,
            offline_mode=False,
            streaming_callback=streaming_callback  # Enable real streaming
        )

        # Send completion with full metadata (v0.5.1 fix for AII-CLI-WS-001)
        await websocket.send_json({
            "type": "complete",
            "success": result.success,
            "function_name": function_name,  # Add function name for debugging
            "metadata": format_completion_metadata(result)
        })

    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        # Send error
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass

    finally:
        # Close connection
        try:
            await websocket.close()
        except:
            pass
