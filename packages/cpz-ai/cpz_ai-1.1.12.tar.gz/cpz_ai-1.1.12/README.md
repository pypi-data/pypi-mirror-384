<a href="https://www.cpz-lab.com/">
  <img src="https://drive.google.com/uc?id=1JY-PoPj9GHmpq3bZLC7WyJLbGuT1L3hN" alt="CPZ Lab" width="150">
</a>

# CPZ AI — Python SDK

[![Coverage](https://img.shields.io/badge/coverage-85%25%2B-brightgreen.svg)](https://github.com/CPZ-Lab/cpz-py)
[![Python](https://img.shields.io/badge/python-3.9%20|%203.10%20|%203.11%20|%203.12-blue.svg)](https://www.python.org/)

## Install

```bash
pip install cpz-ai
```

## 60-second Quickstart (Sync)

> ⚠️ **IMPORTANT**: All trading operations are now routed through CPZ AI. You **do not** need to provide broker credentials directly. Broker credentials are securely managed in your CPZ AI account.

### Trading
```python
import cpz
from cpz.execution.models import OrderSubmitRequest
from cpz.execution.enums import OrderSide, OrderType, TimeInForce

# Only CPZ AI credentials needed
client = cpz.clients.sync.CPZClient()

# Single account setup
client.execution.use_broker("alpaca", environment="paper")

# Multi-account setup (if you have multiple accounts with same broker)
# Tip: when account_id is provided, environment is optional — the SDK
# will select the exact account and its associated environment.
# client.execution.use_broker("alpaca", account_id="your-account-id")

order = client.execution.submit_order(OrderSubmitRequest(
    symbol="AAPL",
    side=OrderSide.BUY,
    qty=10,
    order_type=OrderType.MARKET,
    time_in_force=TimeInForce.DAY,
    strategy_id="your-strategy-uuid-here",  # REQUIRED
))
print(order.id, order.status)
```



## Execution Architecture

```
CPZClient.execution  -->  BrokerRouter  -->  CPZ AI API  -->  Trading Credentials  -->  AlpacaAdapter
                              |                  |                     |                     ^
                              |                  v                     v                     |
                              |              Orders Table         Broker Execution    +---- future brokers (IBKR, Tradier, ...)
                              |                  |                     |
                              |                  v                     v
                              |              Audit Trail          Order Updates
```

### Flow
1. **Order Creation**: All orders are first written to CPZ AI's `orders` table with full audit trail
2. **Credential Resolution**: Trading credentials are fetched securely from CPZ AI (never from environment). The SDK now prefers the private endpoint `trading_credentials_private` when your key has the `trading_credentials` scope, with safe fallbacks for older deployments.
3. **Broker Execution**: Orders are placed at the broker using resolved credentials
4. **Status Updates**: Order status and broker responses are updated in CPZ AI

## Configuration (.env)

> ⚠️ **Authentication Change**: Only CPZ AI credentials are needed. **Do not** set broker credentials (ALPACA_* etc.) - they are managed in your CPZ AI account.

### Required Settings

| Key | Description | Example |
| --- | --- | --- |
| **CPZ_AI_API_KEY** | Your CPZ AI API Key | cpz_... |
| **CPZ_AI_API_SECRET** | Your CPZ AI API Secret | cpz_secret_... |

### Optional Settings

| Key | Description | Default | When to Change |
| --- | --- | --- | --- |
| CPZ_AI_URL | CPZ AI API Endpoint | https://api-ai.cpz-lab.com/cpz | Custom deployments only |
| CPZ_ENV | SDK environment | production | Development/debugging |
| CPZ_LOG_LEVEL | Log level | INFO | Debugging issues |
| CPZ_REQUEST_TIMEOUT_SECONDS | Default request timeout | 30 | Slow connections |

### Getting Your CPZ AI Keys

1. **Get API Keys**: [https://ai.cpz-lab.com/profile-settings?tab=api-keys](https://ai.cpz-lab.com/profile-settings?tab=api-keys)
2. **Add Trading Accounts**: [https://ai.cpz-lab.com/profile-settings?tab=trading-accounts](https://ai.cpz-lab.com/profile-settings?tab=trading-accounts)
3. Generate your `CPZ_AI_API_KEY` and `CPZ_AI_API_SECRET`
4. Add your broker credentials (Alpaca, etc.) to enable trading

## Usage

### Selecting a broker
```python
# Single account (most common)
client.execution.use_broker("alpaca", environment="paper")
client.execution.use_broker("alpaca", environment="live")

# Multi-account: Use account_id to pick a specific account
client.execution.use_broker("alpaca", account_id="account-1")   # env optional when account specified
client.execution.use_broker("alpaca", account_id="account-2")
client.execution.use_broker("alpaca", environment="live", account_id="main-live-account")  # explicit env also supported
```

**When to use `account_id`:**
- You have multiple accounts with the same broker (e.g., Alpaca)
- Want to target a specific account; the SDK resolves the right env from credentials
- Without `account_id`, the SDK uses your default/primary account; use `environment` to choose paper/live

### Submit / cancel / replace order (sync)
```python
from cpz.execution.models import OrderSubmitRequest, OrderReplaceRequest
from cpz.execution.enums import OrderSide, OrderType, TimeInForce

req = OrderSubmitRequest(
    symbol="AAPL", 
    side=OrderSide.BUY, 
    qty=1,
    order_type=OrderType.MARKET, 
    time_in_force=TimeInForce.DAY,
    strategy_id="your-strategy-uuid-here"  # REQUIRED
)
order = client.execution.submit_order(req)
client.execution.cancel_order(order.id)
client.execution.replace_order(order.id, OrderReplaceRequest(qty=2))
```

### Async + Streaming
```python
import asyncio
from cpz.clients.async_ import AsyncCPZClient

async def main():
    client = AsyncCPZClient()
    await client.execution.use_broker("alpaca", environment="paper")
    async for q in client.execution.stream_quotes(["AAPL", "MSFT"]):
        print(q.symbol, q.bid, q.ask)
        break

asyncio.run(main())
```

### Get account / positions
```python
acct = client.execution.get_account()
positions = client.execution.get_positions()
```

### CPZ AI - Strategies & Files

Access your CPZ AI platform data including strategies and files:

```python
from cpz.common.cpz_ai import CPZAIClient

# Connect to CPZ AI
client = CPZAIClient.from_env()

# Get your strategies (user-specific by default)
strategies = client.get_strategies()
print(f"Your strategies: {[s.get('title', 'Unknown') for s in strategies]}")

# Create a new strategy (automatically assigned to your user_id)
new_strategy = client.create_strategy({
    "title": "My Trading Bot",
    "description": "Automated trading strategy",
    "strategy_type": "momentum",
    "status": "active"
})
```

#### User-Specific Access Control

The CPZ AI client automatically handles user isolation:

- **Regular Users**: Only see and manage their own strategies, files, orders, and trading data
- **Admins**: Can access all strategies, files, orders, and trading data across all users

#### API Permissions & Data Access

Your CPZ AI credentials provide access to:

✅ **Strategies** - Read/write your trading strategies  
✅ **Data Files** - Upload/download files and datasets  
✅ **Storage** - File storage and management  
✅ **Orders** - Read/write order history and execution data  
✅ **Trading Credentials** - Access to your configured broker accounts  
✅ **Metadata** - Strategy metadata, performance metrics, and analytics

```python
# Recommended: Use environment variables (automatic user resolution)
client = CPZAIClient.from_env()  # User-specific access based on your CPZ AI credentials

# Manual instantiation (if needed for special cases)  
client = CPZAIClient(
    url="https://api-ai.cpz-lab.com/cpz",
    api_key="your_api_key", 
    secret_key="your_secret_key"
    # User identity and permissions are auto-resolved from your credentials
)

# Environment variables (in .env file):
# CPZ_AI_API_KEY=your_api_key
# CPZ_AI_API_SECRET=your_secret_key
# User ID and admin permissions are auto-resolved from your CPZ AI account
```

#### File Operations & DataFrames

Upload, download, and manage files with pandas DataFrame support:

```python
import pandas as pd

# Create a sample DataFrame
df = pd.DataFrame({
    'symbol': ['AAPL', 'GOOGL', 'MSFT'],
    'price': [150.25, 2750.80, 310.45],
    'volume': [1000000, 500000, 800000]
})

# Upload DataFrame as CSV
client.upload_dataframe("data-bucket", "stocks.csv", df, format="csv")

# Upload DataFrame as JSON
client.upload_dataframe("data-bucket", "stocks.json", df, format="json")

# Upload DataFrame as Parquet
client.upload_dataframe("data-bucket", "stocks.parquet", df, format="parquet")

# Download CSV and load to DataFrame
downloaded_df = client.download_csv_to_dataframe("data-bucket", "stocks.csv")

# Download JSON and load to DataFrame
downloaded_df = client.download_json_to_dataframe("data-bucket", "stocks.json")

# Download Parquet and load to DataFrame
downloaded_df = client.download_parquet_to_dataframe("data-bucket", "stocks.parquet")

# List files in a bucket
files = client.list_files_in_bucket("data-bucket", prefix="stocks")

# Delete files
client.delete_file("data-bucket", "stocks.csv")
```

#### Load User Strategies to DataFrame

```python
from cpz.common.cpz_ai import CPZAIClient
import pandas as pd

# Load your strategies (user-specific, auto-resolved from CPZ AI credentials)
client = CPZAIClient.from_env()  # Uses CPZ_AI_API_KEY and CPZ_AI_API_SECRET from .env

# Get your strategies as DataFrame
strategies_df = pd.DataFrame(client.get_strategies())
print(f"Found {len(strategies_df)} strategies")
print(strategies_df.head())
```

**Note**: The CPZ AI client connects to your API endpoint at `api-ai.cpz-lab.com/cpz`. Users only need to provide their CPZ AI API keys.

## 🚨 Breaking Changes & Migration

### Version 2.0+ Updates

**Authentication**: 
- ✅ **Only CPZ AI keys** (`CPZ_AI_API_KEY`, `CPZ_AI_API_SECRET`)
- ❌ **No broker keys** (ALPACA_*, IBKR_*, etc.)

**Order Submission**:
- ✅ **`strategy_id` required** for all orders
- ✅ **Client-side idempotency** with `client_order_id`
- ✅ **Full audit trail** through CPZ AI

**Broker Configuration**:
- ✅ `use_broker("alpaca", environment="paper", account_id="optional")`
- ❌ `use_broker("alpaca", env="paper")` (old style)

**Migration Steps**:
1. Remove all `ALPACA_*` environment variables
2. Set `CPZ_AI_API_KEY` and `CPZ_AI_API_SECRET`
3. Add broker credentials to your CPZ AI account (Settings → Trading Accounts)
4. Add `strategy_id` to all `OrderSubmitRequest` calls
5. Update `use_broker()` calls to use `environment` parameter

### CLI

> ⚠️ **Authentication**: The CLI uses your CPZ AI credentials from environment variables or `.env` file. No broker credentials needed.

```bash
# List available brokers
cpz broker list

# Configure broker (credentials auto-resolved from CPZ AI)
cpz broker use alpaca --env paper
cpz broker use alpaca --env live --account-id "your-account-id"  # Multi-account

# Submit orders (strategy-id is required)
cpz order submit --symbol AAPL --side buy --qty 10 --type market --tif day --strategy-id "your-uuid"

# Manage orders
cpz order get --id <order-id>
cpz order cancel --id <order-id>
cpz order replace --id <order-id> --qty 20

# Get account info
cpz positions
cpz-ai positions
cpz-ai stream quotes --symbols AAPL,MSFT
```

## Error handling

Catch `cpz.common.errors.CPZBrokerError`. Broker errors are mapped to CPZ errors.

## Logging & Redaction

Structured JSON logging via `structlog`, with redaction of `Authorization`, `ALPACA_API_SECRET_KEY`, and similar.
Configure level via `CPZ_LOG_LEVEL`.

## Testing & Quality

- `make test` (coverage goal ≥ 85%)
- `mypy --strict`

## Python Compatibility

This package is tested and compatible with:
- **Python 3.9** ✅
- **Python 3.10** ✅  
- **Python 3.11** ✅
- **Python 3.12** ✅

### Compatibility Features
- Uses `from __future__ import annotations` for forward-compatible type hints
- Compatible type annotation syntax across all supported versions
- No version-specific syntax that would break older Python versions
- Continuous integration testing on all supported Python versions

## Contributing

Style: ruff/black/isort, pre-commit, branch naming. See `CONTRIBUTING.md`.

## Versioning & Release

Bump version in `pyproject.toml`, build, and publish to PyPI.

## Roadmap

Next brokers: IBKR, Tradier, …

## Security

See `SECURITY.md`. No LICENSE file is included intentionally.
