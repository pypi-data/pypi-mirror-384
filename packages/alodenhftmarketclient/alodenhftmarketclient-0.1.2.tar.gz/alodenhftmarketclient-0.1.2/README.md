# market-client (Python)

A high‑level Python client for the HFT Simulator gateway (server/) that mirrors the website's behavior but hides the server details.
- Automatically performs handshake and login
- Keeps a persistent CMD WebSocket session
- Optionally auto-subscribes to the MD stream and maintains simple in‑memory state (symbols, book snapshots)
- Provides high‑level helpers (get_symbols, get_book, place_order, list_orders)
- Minimizes HTTP usage: performs requests over a persistent CMD WebSocket session
- MD-driven book maintenance and candle aggregation with minimal refreshes
- Optional in‑memory transactions ring buffer that records CMD `event` messages, with simple hooks and accessors

## Install

This package depends on `httpx` and `websockets`.

- With pip (editable for local dev):

```
python3 -m venv .venv
. .venv/bin/activate
pip install -e ./market-client
```

Or install directly:

```
pip install httpx>=0.24 websockets>=10
```

## Quickstart (high‑level)

```python
import asyncio
from market_client import MarketClient

async def main():
    # One call connects: handshake -> CMD -> login -> MD
    client = await MarketClient.connect("http://localhost:8000", connect_md=True)

    # High-level helpers
    symbols = await client.get_symbols()
    print("symbols:", symbols[:3])

    book = await client.get_book(symbols[0]["sym"], depth=10)
    print("book:", book)

    # Candles: configure and read
    await client.configure_candles(symbols[0]["sym"], interval_ms=1000, depth=50)
    print("candles:", client.get_candles(symbols[0]["sym"])[:3])

    # Orders
    # await client.place_order(sym, side="buy", price="100.00", qty=1)
    # orders = await client.list_orders()
    # print("orders:", orders)

    await client.aclose()

asyncio.run(main())
```

See `examples/simple.py` for a runnable sample.

## Notes
- The client auto-fills the JSON envelope (`type`, `ver`, `msg_id`, `ts`) and matches responses by `corr_id`.
- Tokens are handled automatically by `connect()`.
- When `connect_md=True`, the client starts a background task to process MD events and keeps a simple book snapshot per symbol. Future iterations can extend this to persistent candles, etc.
- CMD `event` messages are recorded into an in‑memory ring buffer by default (capacity 1000). You can adjust capacity, clear, and read back recent transactions; and register a global event hook that is called for each event.

## API

- `await MarketClient.connect(base_url, connect_md=True, on_md_event=None, on_cmd_event=None)`
  - Performs handshake, opens CMD, logs in, and optionally subscribes to MD.
- High‑level methods
  - `await get_symbols(force_refresh=False)` -> list of `{ sym, tick, min_qty, lot, status }`
  - `await get_book(sym, depth=20)` -> `{ sym, seq, bids, asks }` (arrays)
  - `await configure_candles(sym, interval_ms=1000, depth=50)` -> seeds window; MD updates candles
  - `get_candles(sym)` -> list of OHLC entries suitable for charting
  - `await send(op, payload={}, as_role=None, timeout=5.0)` -> generic WS request/response helper
  - `await place_order(sym, side, price, qty, tif='GTC')` -> payload dict
  - `await cancel_order(order_id)` -> payload dict
  - `await list_orders()` -> list of order dicts
  - `book_snapshot(sym, depth=20)` -> current in-memory book from MD
  - `best_bid_ask(sym)` -> dict with top-of-book `{bid, ask}`
  - Transactions (CMD events):
    - `configure_transactions(capacity=1000)` -> set ring buffer size (preserves newest up to capacity)
    - `get_transactions(limit=None)` -> list of recent events (raw JSON); `limit` keeps last N
    - `clear_transactions()` -> empty the buffer
    - `set_event_hook(handler)` -> register a global handler called for every CMD `event` (sync or async)

Low‑level access (still available if needed):
- `handshake()`, `api_request()`, `open_cmd()`, `open_md()`

### Transactions buffer usage

```python
from alodenhftmarketclient import MarketClient

client = MarketClient("http://localhost:8000")
hs = await client.handshake()  # obtain token first

# Optional: adjust capacity to 5000 events
client.configure_transactions(capacity=5000)

# Optional: register a global event hook
def on_evt(evt):
    # evt is the raw JSON event object from CMD
    kind = evt.get("event") or evt.get("op")
    print("event:", kind)

client.set_event_hook(on_evt)

# Open CMD; events are recorded automatically and fan-out to hooks
cmd = await client.open_cmd()

# ... run your flow ...

# Read back recent transactions
recent = client.get_transactions(limit=100)

# Clear if needed
client.clear_transactions()
```

Request session class
- `RequestSession`: alias of the request-capable CMD WebSocket session used internally for minimal-latency requests.

## Server assumptions
- Matches the FastAPI server under `server/` with routes:
  - `POST /auth/handshake`
  - `POST /api/request`
  - `WS /ws/cmd`
  - `WS /ws/md`
