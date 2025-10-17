from __future__ import annotations

import asyncio
from typing import Iterable, Optional

import click

from .clients.async_ import AsyncCPZClient
from .clients.sync import CPZClient
from .common.cpz_ai import CPZAIClient
from .execution.enums import OrderSide, OrderType, TimeInForce
from .execution.models import OrderReplaceRequest, OrderSubmitRequest


@click.group()
def main() -> None:
    """cpz command-line interface."""


@main.group()
def broker() -> None:
    """Broker management commands."""


@broker.command("list")
def broker_list() -> None:
    client = CPZClient()
    names = client.execution.router.list_brokers()
    if not names:
        click.echo("No brokers registered. Try: cpz broker use alpaca --env paper")
        return
    for name in names:
        click.echo(name)


@broker.command("use")
@click.argument("name", type=str)
@click.option("--env", type=click.Choice(["paper", "live"]), default="paper")
@click.option("--account-id", type=str, help="Account ID for multi-account setups")
def broker_use(name: str, env: str, account_id: Optional[str]) -> None:
    client = CPZClient()
    try:
        client.execution.use_broker(name, environment=env, account_id=account_id)
    except Exception as exc:  # noqa: BLE001
        click.echo(
            f"Failed to use broker '{name}': {exc}\nExample: cpz broker use alpaca --env paper\nNote: Credentials are managed through your CPZ AI account",
            err=True,
        )
        raise SystemExit(1)
    click.echo(f"Using broker: {name} ({env}){f' account: {account_id}' if account_id else ''}")


@main.group()
def order() -> None:
    """Order commands."""


@order.command("submit")
@click.option("--symbol", required=True, type=str)
@click.option("--side", required=True, type=click.Choice(["buy", "sell"]))
@click.option("--qty", required=True, type=float)
@click.option("--type", "order_type", required=True, type=click.Choice(["market", "limit"]))
@click.option("--strategy-id", required=True, type=str, help="Strategy ID (required for all orders)")
@click.option("--limit-price", type=float, default=None)
@click.option("--tif", type=click.Choice(["day", "gtc", "fok", "ioc"]), default="day")
def order_submit(
    symbol: str, side: str, qty: float, order_type: str, strategy_id: str, limit_price: Optional[float], tif: str
) -> None:
    client = CPZClient()
    req = OrderSubmitRequest(
        symbol=symbol,
        side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
        qty=qty,
        order_type=OrderType.MARKET if order_type == "market" else OrderType.LIMIT,
        strategy_id=strategy_id,
        limit_price=limit_price,
        time_in_force=TimeInForce(tif.upper()),
    )
    order = client.execution.submit_order(req)
    click.echo(order.model_dump_json())


@order.command("get")
@click.option("--id", "order_id", required=True, type=str)
def order_get(order_id: str) -> None:
    client = CPZClient()
    order = client.execution.get_order(order_id)
    click.echo(order.model_dump_json())


@order.command("cancel")
@click.option("--id", "order_id", required=True, type=str)
def order_cancel(order_id: str) -> None:
    client = CPZClient()
    order = client.execution.cancel_order(order_id)
    click.echo(order.model_dump_json())


@order.command("replace")
@click.option("--id", "order_id", required=True, type=str)
@click.option("--qty", type=float)
@click.option("--limit-price", type=float)
def order_replace(order_id: str, qty: Optional[float], limit_price: Optional[float]) -> None:
    client = CPZClient()
    req = OrderReplaceRequest(qty=qty, limit_price=limit_price)
    order = client.execution.replace_order(order_id, req)
    click.echo(order.model_dump_json())


@main.command("positions")
def positions() -> None:
    client = CPZClient()
    pos = client.execution.get_positions()
    click.echo("\n".join(p.model_dump_json() for p in pos))


@main.command("stream")
@click.option("--symbols", required=True, type=str, help="Comma-separated symbols")
@click.option("--broker", default="alpaca", type=str, help="Broker name")
@click.option("--env", default="paper", type=click.Choice(["paper", "live"]), help="Environment")
@click.argument("channel", type=click.Choice(["quotes"]))
def stream(channel: str, symbols: str, broker: str, env: str) -> None:
    async def _run(sym_list: Iterable[str]) -> None:
        client = AsyncCPZClient()
        await client.execution.use_broker(broker, environment=env)
        if channel == "quotes":
            async for q in client.execution.stream_quotes(sym_list):
                click.echo(q.model_dump_json())
                break

    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    asyncio.run(_run(sym_list))


@main.group()
def platform() -> None:
    """CPZ platform utilities (wrapped)."""


@platform.command("health")
@click.option("--url", envvar="SUPABASE_URL", required=False)
@click.option("--anon", envvar="SUPABASE_ANON_KEY", required=False)
@click.option("--service", envvar="SUPABASE_SERVICE_ROLE_KEY", required=False)
def platform_health(url: Optional[str], anon: Optional[str], service: Optional[str]) -> None:
    client = CPZClient()
    client.platform.configure(url=url, anon=anon, service=service)
    click.echo({"health": client.platform.health()})


@platform.command("echo")
@click.option("--url", envvar="SUPABASE_URL", required=False)
@click.option("--anon", envvar="SUPABASE_ANON_KEY", required=False)
@click.option("--service", envvar="SUPABASE_SERVICE_ROLE_KEY", required=False)
def platform_echo(url: Optional[str], anon: Optional[str], service: Optional[str]) -> None:
    client = CPZClient()
    client.platform.configure(url=url, anon=anon, service=service)
    out = {
        "echo": client.platform.echo(),
        "tables": client.platform.list_tables(),
    }
    click.echo(out)


@main.group()
def diag() -> None:
    """Diagnostics and troubleshooting."""


@diag.command("order-path")
def diag_order_path() -> None:
    """Check gateway health, metadata, and orders insert path."""
    sb = CPZAIClient.from_env()
    results = {
        "health": False,
        "tables_contains_orders": False,
        "orders_probe": None,
    }
    try:
        results["health"] = sb.health()
    except Exception as exc:  # noqa: BLE001
        results["health_error"] = str(exc)
    try:
        tables = sb.list_tables()
        results["tables_contains_orders"] = "orders" in (tables or [])
        results["tables"] = tables
    except Exception as exc:  # noqa: BLE001
        results["tables_error"] = str(exc)
    # Probe insert with minimal payload but do not abort on failure
    try:
        probe = sb.record_order(
            order_id="probe",
            symbol="PROBE",
            side="buy",
            qty=0.0,
            type="market",
            time_in_force="DAY",
            broker="probe",
            env="paper",
            strategy_id=None,
            status="pending",
        )
        results["orders_probe"] = bool(probe)
    except Exception as exc:  # noqa: BLE001
        results["orders_probe_error"] = str(exc)
    click.echo(results)
