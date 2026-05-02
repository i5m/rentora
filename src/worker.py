"""Cloudflare Python Worker entrypoint for the rentora MCP server.

Architecture:
- FastMCP defines the tool surface and produces an ASGI app that serves the
  SSE transport (`GET /sse` for the long-lived stream, `POST /messages/`
  for client-to-server JSON-RPC).
- The ASGI app lives inside a Durable Object so requests for a given logical
  server are pinned to a single actor (this is the Cloudflare-supported
  pattern for Python MCP today).
- The Workers `asgi.py` shim translates between the JS Request/Response
  objects and the Python ASGI protocol.

Why SSE only (not Streamable HTTP) for now?
  The newer Streamable HTTP transport in `mcp` relies on a single, long-lived
  `StreamableHTTPSessionManager.run()` task group that must outlive every
  request. Cloudflare's `asgi.py` shim runs the ASGI lifespan
  startup/shutdown around each request, which calls `.run()` more than once
  per session manager and crashes. Until the shim grows persistent-lifespan
  support, SSE is the verified, working transport for Python MCP on
  Workers - it is what Cloudflare's own demo uses
  (cloudflare/ai/demos/python-workers-mcp).
"""

from workers import DurableObject

from name_value import compute_name_value


def setup_server():
    from mcp.server.fastmcp import FastMCP
    from starlette.middleware.cors import CORSMiddleware

    from exceptions import HTTPException, http_exception

    mcp = FastMCP("rentora")

    @mcp.tool()
    def name_value(name: str) -> dict:
        """Sum the alphabetic values of letters in `name` (A=1, B=2, ..., Z=26).

        Non-letter characters (digits, whitespace, punctuation, accented or
        non-ASCII letters) are ignored. Matching is case-insensitive.

        Args:
            name: The string to score.

        Returns:
            A dict with the original input, the count of letters scored, and
            the total numeric value.
        """
        return dict(compute_name_value(name))

    app = mcp.sse_app()
    app.add_exception_handler(HTTPException, http_exception)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id"],
    )

    return mcp, app


class NameValueServer(DurableObject):
    """Durable Object that owns the FastMCP ASGI app for one logical server."""

    def __init__(self, ctx, env):
        self.ctx = ctx
        self.env = env
        self.mcp, self.app = setup_server()

    async def on_fetch(self, request, env, ctx):
        import asgi

        return await asgi.fetch(self.app, request, self.env, self.ctx)


async def on_fetch(request, env):
    obj_id = env.ns.idFromName("singleton")
    obj = env.ns.get(obj_id)
    return await obj.fetch(request)
