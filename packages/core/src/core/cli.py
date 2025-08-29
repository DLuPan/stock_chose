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
    adjust: str = "hfq",
    max_workers: int = 5,  # 新增参数，默认并发数为5
):
    """
    Sync historical stock data.
    """
    from core.sync import sync_stock_zh_a_hist_all

    typer.echo("Starting historical stock data synchronization...")
    sync_stock_zh_a_hist_all(period, start_date, end_date, adjust, max_workers)
    typer.echo("Historical stock data synchronization completed.")


@app.command()
def generate_stock_report(
    adjust: Annotated[
        str, typer.Option("--adjust", "-a", help="Adjustment type (default: qfq)")
    ] = "hfq",
    output_dir: Annotated[
        str, typer.Option("--out-html", "-o", help="Output HTML file path")
    ] = "stock_report",
):
    """
    Generate a stock report based on the provided parameters.
    """
    from core.report import generate_report

    generate_report(adjust, output_dir)
    typer.echo(f"Stock report generated at {output_dir}")


if __name__ == "__main__":
    app()
