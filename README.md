# rentora MCP

A simple Python [Model Context Protocol](https://modelcontextprotocol.io/) server hosted on
[Cloudflare Workers](https://workers.cloudflare.com/). It exposes a single tool, `name_value`,
that scores a string by summing the alphabetic value of each letter (A=1, B=2, ..., Z=26).
Non-letter characters are ignored; matching is case-insensitive.

```text
name_value("Cat")            -> {"input": "Cat",            "letters_counted": 3,  "total": 24}
name_value("Hello, World!")  -> {"input": "Hello, World!",  "letters_counted": 10, "total": 124}
name_value("Cloudflare")     -> {"input": "Cloudflare",     "letters_counted": 10, "total": 97}
```

## How it works

| Layer | What it does |
| --- | --- |
| `src/name_value.py` | Pure letter-sum function (zero Worker/Pyodide imports, fully unit-tested) |
| `src/worker.py` | Defines the FastMCP server, registers `name_value` as a tool, wires the ASGI app into a Durable Object |
| `src/asgi.py` | Vendored shim that bridges Cloudflare's JS Request/Response objects to Python's ASGI protocol |
| `src/exceptions.py`, `src/logger.py`, `src/uvicorn.py` | Small support modules required by the FastMCP/Workers combo |
| `wrangler.jsonc` | Worker config: Python compatibility flag, Durable Object binding, sqlite migration |

The MCP traffic flows: `MCP client → Worker fetch handler → Durable Object → FastMCP ASGI app → name_value tool`.

## Requirements

- **Cloudflare Workers Paid plan (~$5/mo).** The Python + FastMCP bundle is ~10 MB of
  vendored modules, which exceeds the 3 MB free-tier Worker size limit. Local
  development with `pywrangler dev` works fine without a paid plan; only the
  `deploy` step requires it.
- [`uv`](https://docs.astral.sh/uv/) for Python dependency management.
- Node.js (for `wrangler`, installed automatically via `npm install`).

## Local development

```bash
# 1. Install Python deps (creates .venv/) and Node deps (for wrangler)
uv sync
npm install

# 2. Start the local Worker on http://localhost:8787
uv run pywrangler dev

# 3. (in another terminal) Smoke-test it via the MCP SSE transport
uv run python scripts/verify_local.py
```

You can also point the official [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
at the running server:

```bash
npx @modelcontextprotocol/inspector@latest
# In the Inspector UI, choose transport "SSE" and URL http://localhost:8787/sse
```

## Tests, lint, format

```bash
uv run pytest tests          # 30 unit tests over the pure logic
uv run ruff check .          # lint
uv run ruff format .         # auto-format
```

## Deploy

```bash
uv run pywrangler deploy
```

After deploy, the server is live at `https://rentora-mcp.<your-account>.workers.dev/sse`.
The first deploy provisions the `NameValueServer` Durable Object class via the migration in
`wrangler.jsonc`.

### Connect a remote MCP client

For clients that don't speak remote MCP natively (e.g. Claude Desktop), use the
[`mcp-remote`](https://www.npmjs.com/package/mcp-remote) local proxy:

```jsonc
// claude_desktop_config.json
{
  "mcpServers": {
    "rentora": {
      "command": "npx",
      "args": ["mcp-remote", "https://rentora-mcp.<your-account>.workers.dev/sse"]
    }
  }
}
```

## Transport choice: why SSE, not Streamable HTTP

The current MCP spec recommends the newer Streamable HTTP transport, and FastMCP
exposes it via `mcp.streamable_http_app()`. That app relies on a single,
long-lived `StreamableHTTPSessionManager.run()` task group that must outlive
every request.

Cloudflare's Python Workers `asgi.py` shim runs the ASGI lifespan
startup/shutdown around each individual request, which would call
`session_manager.run()` more than once and crash on the second request. Until
the shim grows persistent-lifespan support, the SSE transport is the verified,
working path - and it is what Cloudflare's own demo uses
([cloudflare/ai/demos/python-workers-mcp](https://github.com/cloudflare/ai/tree/main/demos/python-workers-mcp)).

When the shim catches up, switching is a one-line change in `setup_server()`:
swap `mcp.sse_app()` for `mcp.streamable_http_app()`.

## Project layout

```
.
├── pyproject.toml          # uv-managed deps + ruff/pytest config
├── package.json            # wrangler + dev/deploy scripts
├── wrangler.jsonc          # Cloudflare Worker config
├── README.md
├── src/
│   ├── worker.py           # entrypoint + Durable Object + FastMCP setup
│   ├── name_value.py       # pure letter-sum logic
│   ├── asgi.py             # vendored ASGI <-> Workers bridge
│   ├── exceptions.py       # Starlette exception handler
│   ├── logger.py           # structlog config
│   └── uvicorn.py          # stub to satisfy mcp's optional uvicorn import
├── tests/
│   └── test_name_value.py  # 30 tests over the pure logic
└── scripts/
    └── verify_local.py     # end-to-end MCP smoke test against pywrangler dev
```

## License

MIT (do whatever you want).
