"""Stub to satisfy `mcp`'s top-level import of uvicorn.

The MCP Python SDK has an optional dependency on uvicorn but still imports it
at module scope (see mcp/server/fastmcp/server.py). We never call
`run_sse_async`, so this empty module is enough to make the import succeed
inside Cloudflare's Pyodide-based Python Workers (which use `asgi.py` for
request dispatch instead of uvicorn).
"""
