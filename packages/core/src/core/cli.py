# 用于指令
from typing import Annotated
import typer
import akshare as ak

from core.version import VERSION


app = typer.Typer()


@app.command()
def version():
    """
    Print the version of the Stock Chose Service CLI.
    """
    typer.echo(f"Stock Chose Service CLI version: {VERSION}")


@app.command()
def sync_all():
    """
    Sync all stock data.
    """
    from core.sync import sync_stock_zh_a_spot_em

    typer.echo("Starting stock data synchronization...")
    sync_stock_zh_a_spot_em()
    typer.echo("Stock data synchronization completed.")


@app.command()
def sync_hist(
    symbol: str = "000001",
    period: str = "daily",
    start_date: str = "19700101",
    end_date: str = "20500101",
    adjust: str = "",
):
    """
    Sync historical stock data.
    """
    from core.sync import sync_stock_zh_a_hist

    typer.echo(f"Starting historical data synchronization for symbol: {symbol}...")
    sync_stock_zh_a_hist(symbol, period, start_date, end_date, adjust)
    typer.echo("Historical data synchronization completed.")


@app.command()
def sync_hist_all(
    period: str = "daily",
    start_date: str = "19700101",
    end_date: str = "20500101",
    adjust: str = "",
):
    """
    Sync historical stock data.
    """
    from core.sync import sync_stock_zh_a_hist_all

    typer.echo("Starting historical stock data synchronization...")
    sync_stock_zh_a_hist_all(period, start_date, end_date, adjust)
    typer.echo("Historical stock data synchronization completed.")


if __name__ == "__main__":
    app()
