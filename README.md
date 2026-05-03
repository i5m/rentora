# rentora MCP

A Python [Model Context Protocol](https://modelcontextprotocol.io/) server hosted on
[Cloudflare Workers](https://workers.cloudflare.com/) that exposes a single tool,
`rent_vs_buy`, which projects the year-by-year financial outcome of renting vs buying
a home. It returns a per-year breakdown, the break-even year (if any), and which
option ends up ahead at the end of the simulation.

> The tool returns purely mathematical projections from the inputs you give it. It
> is not financial advice.

## Agent Skill

Some MCP clients do not surface **`prompts/get`** reliably. This repo ships an **[Agent Skill](https://agentskills.io)** alongside the server MCP prompt **`rent_vs_buy_guide`**—same workflow in portable form:

- Skill folder: [`skills/rentora/`](skills/rentora/) (`SKILL.md` plus `references/` and `assets/sample-request.json`).
- **Validate** layout and golden JSON against [`src/models.py`](src/models.py):

  ```bash
  uv run python scripts/validate_rentora_skill.py
  ```

- Optional ([agentskills validation](https://agentskills.io/specification)): `skills-ref validate ./skills/rentora` when `skills-ref` is installed.

Some Cursor workspaces load project skills from **`.cursor/skills/`** only—symlink or copy this folder there if needed.

## Tool surface

```text
rent_vs_buy(location, rent, house, inflation, investments, heloc, years_to_simulate=30)
```

Inputs (all defined in [`src/models.py`](src/models.py)):

| Group | Field | Notes |
| --- | --- | --- |
| `location` | `country`, `zip_code` | Tagged onto the response, not used in the math today. |
| `rent` | `monthly_rent`, `monthly_utilities`, `yoy_increase_percentage`, `annual_insurance_amount` | Rent grows at `yoy_increase_percentage`; utilities/insurance grow at `inflation.annual_increase_percentage`. |
| `house` | `total_cost`, `mortgage_interest_rate`, `mortgage_years`, `monthly_utilities`, `yoy_appreciation_percentage`, `closing_cost`, `down_payment_percentage`, `annual_insurance`, `property_tax_percentage`, `pmi` | Standard amortizing mortgage. PMI only applied when LTV > 80% of original price. |
| `inflation` | `annual_increase_percentage` | Drives utilities, insurance, and assessed-value growth on both sides. |
| `investments` | `annual_increase_percentage` | Annual return on un-tied capital. |
| `heloc` | `interest_rate_percentage`, `loan_length_years`, `after_years`, `ltv_cap` | Buyer takes a HELOC at `after_years` for the remaining equity up to `ltv_cap` (default 0.80) and reinvests the proceeds. |
| (top-level) | `years_to_simulate` | Default 30. |

Output shape (per year, plus top-level `break_even_year` and `best_option_at_end`):

```jsonc
{
  "year": 0,
  "rent_cost": 26100.0,
  "renter_investment_principal": 88000.0,
  "renter_investment_total": 94160.0,
  "renter_net_worth": 94160.0,
  "buy_cost": 28800.0,
  "home_value": 400000.0,
  "mortgage_balance": 316900.0,
  "heloc_balance": 0.0,
  "buyer_investment_principal": 0.0,
  "buyer_investment_total": 0.0,
  "buyer_net_worth": 83100.0,
  "networth_difference_absolute": -11060.0,
  "networth_difference_percentage": -11.7
}
```

## How it works

| Layer | What it does |
| --- | --- |
| [`src/worker.py`](src/worker.py) | Worker entrypoint, Durable Object, FastMCP wiring, `rent_vs_buy` tool definition. |
| [`src/models.py`](src/models.py) | Pydantic input models with field-level validation. |
| [`src/calculators/simulation.py`](src/calculators/simulation.py) | Orchestrator: ticks each calculator one year at a time and assembles the response. |
| [`src/calculators/rent_calculator.py`](src/calculators/rent_calculator.py) | Annual rent + utilities + renter's insurance, with year-over-year growth. |
| [`src/calculators/buy_calculator.py`](src/calculators/buy_calculator.py) | Mortgage amortization, property tax, insurance, utilities, PMI, home appreciation. |
| [`src/calculators/heloc_calculator.py`](src/calculators/heloc_calculator.py) | Optional HELOC: borrow at year *N*, amortize over its own term. |
| [`src/calculators/investment_calculator.py`](src/calculators/investment_calculator.py) | End-of-year contribution model: existing capital compounds first, new contributions land at year-end and start earning the following year. |
| [`src/asgi.py`](src/asgi.py) | Vendored shim that bridges Workers JS Request/Response to Python's ASGI protocol. |
| [`src/exceptions.py`](src/exceptions.py), [`src/logger.py`](src/logger.py), [`src/uvicorn.py`](src/uvicorn.py) | Small support modules. |
| [`wrangler.jsonc`](wrangler.jsonc) | Worker config: Python compatibility flag, Durable Object binding, sqlite migration. |

The MCP traffic flows: `MCP client → Worker fetch handler → Durable Object → FastMCP ASGI app → rent_vs_buy tool`.

### Simulation semantics

Per simulated year the orchestrator does, in order:

1. Compute the renter's annual cash outflow.
2. Compute the buyer's annual cash outflow (mortgage, taxes, insurance, utilities, PMI).
3. If the HELOC trigger year matches, borrow the maximum equity (capped at `ltv_cap`) and add it to the buyer's investments at the *start* of the year.
4. Compound both sides' existing investments for the year.
5. Add the cash-flow surplus (whichever side spent less) as new principal to the other side. New principal is added at year-end, so it doesn't earn returns the year it's contributed.
6. Score net worth: `renter_net_worth = invested capital`, `buyer_net_worth = home_value - mortgage_balance - heloc_balance + invested capital`. The first year `buyer_net_worth > renter_net_worth` is recorded as `break_even_year`.

The renter starts with seed capital equal to what the buyer would have paid out of pocket on day one (`down_payment + closing_cost`) — that's the "smart renter" comparison.

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
uv run pytest tests          # unit + integration tests over the calculators and simulation
uv run ruff check .          # lint
uv run ruff format .         # auto-format
```

Iterate on the math without spinning up the Worker:

```bash
uv run python scripts/test_sim.py
```

## Deploy

```bash
uv run pywrangler deploy
```

After deploy, the server is live at `https://rentora-mcp.<your-account>.workers.dev/sse`.
The first deploy provisions the `RentoraServer` Durable Object class via the migration
in `wrangler.jsonc`. (The class is named `RentoraServer` for backwards-compat with the
initial deployment; renaming it would require a `renamed_classes` migration.)

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
├── pyproject.toml              # uv-managed deps + ruff/pytest config
├── package.json                # wrangler + dev/deploy scripts
├── wrangler.jsonc              # Cloudflare Worker config
├── README.md
├── skills/
│   └── rentora/    # Agent Skill (workflow + references + sample JSON)
├── src/
│   ├── worker.py               # entrypoint + Durable Object + FastMCP setup
│   ├── models.py               # Pydantic input models
│   ├── asgi.py                 # vendored ASGI <-> Workers bridge
│   ├── exceptions.py           # Starlette exception handler
│   ├── logger.py               # structlog config
│   ├── uvicorn.py              # stub to satisfy mcp's optional uvicorn import
│   └── calculators/
│       ├── simulation.py       # orchestrator
│       ├── rent_calculator.py
│       ├── buy_calculator.py
│       ├── investment_calculator.py
│       └── heloc_calculator.py
├── tests/
│   ├── test_models.py
│   ├── test_rent_calculator.py
│   ├── test_buy_calculator.py
│   ├── test_investment_calculator.py
│   ├── test_heloc_calculator.py
│   └── test_simulation.py
└── scripts/
    ├── verify_local.py              # end-to-end MCP smoke test against pywrangler dev
    ├── validate_rentora_skill.py    # validate Agent Skill package + sample-request.json
    └── test_sim.py                  # local sanity check that runs run_simulation directly
```

## License

MIT (do whatever you want).
