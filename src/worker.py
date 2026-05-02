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

from calculators.simulation import run_simulation
from models import (
    HelocInput,
    HouseInput,
    InflationInput,
    InvestmentInput,
    LocationInput,
    RentInput,
)


def setup_server():
    from mcp.server.fastmcp import FastMCP
    from starlette.middleware.cors import CORSMiddleware

    from exceptions import HTTPException, http_exception

    mcp = FastMCP("rentora")

    @mcp.tool()
    def rent_vs_buy(
        location: LocationInput,
        rent: RentInput,
        house: HouseInput,
        inflation: InflationInput,
        investments: InvestmentInput,
        heloc: HelocInput,
        years_to_simulate: int = 30,
    ) -> dict:
        """Calculates the financial projection of renting vs buying a house over a number of years.

        This tool provides purely mathematical projections based on the provided inputs.
        It does NOT provide financial advice.

        Args:
            location: The location details (country, zip code)
            rent: The rental parameters
            house: The home purchase parameters
            inflation: The inflation parameters
            investments: The investment parameters
            heloc: The Home Equity Line of Credit parameters
            years_to_simulate: Number of years to run the calculation (default 30)

        Returns:
            A year-by-year breakdown of costs, net worths, break-even point, and best option.
        """
        return run_simulation(
            location=location,
            rent=rent,
            house=house,
            inflation=inflation,
            investments=investments,
            heloc=heloc,
            years_to_simulate=years_to_simulate,
        )

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
