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
    Sync historical stock data for all symbols.
    """
    from core.sync import sync_stock_zh_a_hist_all

    typer.echo("Starting historical stock data synchronization...")
    sync_stock_zh_a_hist_all(period, start_date, end_date, adjust, max_workers)
    typer.echo("Historical stock data synchronization completed.")


@app.command()
def sync_business_composition(
    symbol: str = typer.Argument(
        ...,
        help="Stock symbol to sync, e.g., SH688041, SZ000001, BJ838169, 688041, 000001, 838169",
    ),
):
    """
    Sync business composition data for a specific stock symbol.
    Supports multiple formats:
    - With market prefix: SH688041, SZ000001, BJ838169
    - Without market prefix: 688041 (SH), 000001 (SZ), 838169 (BJ)

    Market prefix rules:
    - SH: Shanghai Exchange (6xxxxx)
    - SZ: Shenzhen Exchange (0xxxxx, 3xxxxx)
    - BJ: Beijing Exchange (4xxxxx, 8xxxxx)
    """
    from core.sync import sync_stock_business_composition

    typer.echo(
        f"Starting business composition data synchronization for symbol: {symbol}..."
    )
    sync_stock_business_composition(symbol)
    typer.echo("Business composition data synchronization completed.")


@app.command()
def sync_financial_debt(
    symbol: str = typer.Argument(
        ...,
        help="Stock symbol to sync, e.g., SH688041, SZ000001, BJ838169, 688041, 000001, 838169",
    ),
):
    """
    Sync financial debt data (balance sheet) for a specific stock symbol from THS (同花顺).
    Supports multiple formats:
    - With market prefix: SH688041, SZ000001, BJ838169
    - Without market prefix: 688041 (SH), 000001 (SZ), 838169 (BJ)

    Market prefix rules:
    - SH: Shanghai Exchange (6xxxxx)
    - SZ: Shenzhen Exchange (0xxxxx, 3xxxxx)
    - BJ: Beijing Exchange (4xxxxx, 8xxxxx)
    """
    from core.sync import sync_stock_financial_debt

    typer.echo(
        f"Starting financial debt data synchronization for symbol: {symbol}..."
    )
    sync_stock_financial_debt(symbol)
    typer.echo("Financial debt data synchronization completed.")


@app.command()
def sync_all_financial_debts(
    max_workers: int = typer.Option(
        5, "--max-workers", "-w", help="Maximum number of concurrent workers"
    ),
):
    """
    Sync financial debt data (balance sheet) for all stocks from THS (同花顺).
    """
    from core.sync import sync_all_stock_financial_debts

    typer.echo("Starting financial debt data synchronization for all stocks...")
    sync_all_stock_financial_debts(max_workers)
    typer.echo("Financial debt data synchronization for all stocks completed.")


@app.command()
def sync_research_report(
    symbol: str = typer.Argument(
        ...,
        help="Stock symbol to sync, e.g., SH688041, SZ000001, BJ838169, 688041, 000001, 838169",
    ),
):
    """
    Sync research report data for a specific stock symbol from EM (东方财富).
    Supports multiple formats:
    - With market prefix: SH688041, SZ000001, BJ838169
    - Without market prefix: 688041 (SH), 000001 (SZ), 838169 (BJ)

    Market prefix rules:
    - SH: Shanghai Exchange (6xxxxx)
    - SZ: Shenzhen Exchange (0xxxxx, 3xxxxx)
    - BJ: Beijing Exchange (4xxxxx, 8xxxxx)
    """
    from core.sync import sync_stock_research_report

    typer.echo(
        f"Starting research report data synchronization for symbol: {symbol}..."
    )
    sync_stock_research_report(symbol)
    typer.echo("Research report data synchronization completed.")


@app.command()
def sync_all_research_reports(
    max_workers: int = typer.Option(
        5, "--max-workers", "-w", help="Maximum number of concurrent workers"
    ),
):
    """
    Sync research report data for all stocks from EM (东方财富).
    """
    from core.sync import sync_all_stock_research_reports

    typer.echo("Starting research report data synchronization for all stocks...")
    sync_all_stock_research_reports(max_workers)
    typer.echo("Research report data synchronization for all stocks completed.")


@app.command()
def sync_financial_abstract(
    symbol: str = typer.Argument(
        ...,
        help="Stock symbol to sync, e.g., SH688041, SZ000001, BJ838169, 688041, 000001, 838169",
    ),
):
    """
    Sync financial abstract data (key indicators) for a specific stock symbol from THS (同花顺).
    Supports multiple formats:
    - With market prefix: SH688041, SZ000001, BJ838169
    - Without market prefix: 688041 (SH), 000001 (SZ), 838169 (BJ)

    Market prefix rules:
    - SH: Shanghai Exchange (6xxxxx)
    - SZ: Shenzhen Exchange (0xxxxx, 3xxxxx)
    - BJ: Beijing Exchange (4xxxxx, 8xxxxx)
    """
    from core.sync import sync_stock_financial_abstract

    typer.echo(
        f"Starting financial abstract data synchronization for symbol: {symbol}..."
    )
    sync_stock_financial_abstract(symbol)
    typer.echo("Financial abstract data synchronization completed.")


@app.command()
def sync_all_financial_abstracts(
    max_workers: int = typer.Option(
        5, "--max-workers", "-w", help="Maximum number of concurrent workers"
    ),
):
    """
    Sync financial abstract data (key indicators) for all stocks from THS (同花顺).
    """
    from core.sync import sync_all_stock_financial_abstracts

    typer.echo("Starting financial abstract data synchronization for all stocks...")
    sync_all_stock_financial_abstracts(max_workers)
    typer.echo("Financial abstract data synchronization for all stocks completed.")


@app.command()
def sync_financial_analysis(
    symbol: str = typer.Argument(
        ...,
        help="Stock symbol to sync, e.g., SH688041, SZ000001, BJ838169, 688041, 000001, 838169",
    ),
    start_year: str = typer.Option(
        None, "--start-year", "-y", help="Start year for financial data (default: 10 years ago)"
    ),
):
    """
    Sync financial analysis data (financial indicators) for a specific stock symbol from Sina (新浪财经).
    Supports multiple formats:
    - With market prefix: SH688041, SZ000001, BJ838169
    - Without market prefix: 688041 (SH), 000001 (SZ), 838169 (BJ)

    Market prefix rules:
    - SH: Shanghai Exchange (6xxxxx)
    - SZ: Shenzhen Exchange (0xxxxx, 3xxxxx)
    - BJ: Beijing Exchange (4xxxxx, 8xxxxx)
    """
    from core.sync import sync_stock_financial_analysis

    typer.echo(
        f"Starting financial analysis data synchronization for symbol: {symbol}..."
    )
    sync_stock_financial_analysis(symbol, start_year)
    typer.echo("Financial analysis data synchronization completed.")


@app.command()
def sync_all_financial_analyses(
    max_workers: int = typer.Option(
        5, "--max-workers", "-w", help="Maximum number of concurrent workers"
    ),
    start_year: str = typer.Option(
        None, "--start-year", "-y", help="Start year for financial data (default: 10 years ago)"
    ),
):
    """
    Sync financial analysis data (financial indicators) for all stocks from Sina (新浪财经).
    """
    from core.sync import sync_all_stock_financial_analyses

    typer.echo("Starting financial analysis data synchronization for all stocks...")
    sync_all_stock_financial_analyses(max_workers, start_year)
    typer.echo("Financial analysis data synchronization for all stocks completed.")


@app.command()
def sync_gdhs(
    symbol: str = typer.Argument(
        ...,
        help="Stock symbol to sync, e.g., SH688041, SZ000001, BJ838169, 688041, 000001, 838169",
    ),
):
    """
    Sync gdhs data (股东户数详情) for a specific stock symbol from EM (东方财富).
    Supports multiple formats:
    - With market prefix: SH688041, SZ000001, BJ838169
    - Without market prefix: 688041 (SH), 000001 (SZ), 838169 (BJ)

    Market prefix rules:
    - SH: Shanghai Exchange (6xxxxx)
    - SZ: Shenzhen Exchange (0xxxxx, 3xxxxx)
    - BJ: Beijing Exchange (4xxxxx, 8xxxxx)
    """
    from core.sync import sync_stock_gdhs

    typer.echo(
        f"Starting gdhs data synchronization for symbol: {symbol}..."
    )
    sync_stock_gdhs(symbol)
    typer.echo("Gdhs data synchronization completed.")


@app.command()
def sync_all_gdhs(
    max_workers: int = typer.Option(
        5, "--max-workers", "-w", help="Maximum number of concurrent workers"
    ),
):
    """
    Sync gdhs data (股东户数详情) for all stocks from EM (东方财富).
    """
    from core.sync import sync_all_stock_gdhs

    typer.echo("Starting gdhs data synchronization for all stocks...")
    sync_all_stock_gdhs(max_workers)
    typer.echo("Gdhs data synchronization for all stocks completed.")


@app.command()
def sync_main_holder(
    symbol: str = typer.Argument(
        ...,
        help="Stock symbol to sync, e.g., SH688041, SZ000001, BJ838169, 688041, 000001, 838169",
    ),
):
    """
    Sync main holder data (主要股东) for a specific stock symbol from Sina (新浪财经).
    Supports multiple formats:
    - With market prefix: SH688041, SZ000001, BJ838169
    - Without market prefix: 688041 (SH), 000001 (SZ), 838169 (BJ)

    Market prefix rules:
    - SH: Shanghai Exchange (6xxxxx)
    - SZ: Shenzhen Exchange (0xxxxx, 3xxxxx)
    - BJ: Beijing Exchange (4xxxxx, 8xxxxx)
    """
    from core.sync import sync_stock_main_holder

    typer.echo(
        f"Starting main holder data synchronization for symbol: {symbol}..."
    )
    sync_stock_main_holder(symbol)
    typer.echo("Main holder data synchronization completed.")


@app.command()
def sync_all_main_holders(
    max_workers: int = typer.Option(
        5, "--max-workers", "-w", help="Maximum number of concurrent workers"
    ),
):
    """
    Sync main holder data (主要股东) for all stocks from Sina (新浪财经).
    """
    from core.sync import sync_all_stock_main_holders

    typer.echo("Starting main holder data synchronization for all stocks...")
    sync_all_stock_main_holders(max_workers)
    typer.echo("Main holder data synchronization for all stocks completed.")


@app.command()
def sync_stock_all_data(
    symbol: str = typer.Argument(
        ...,
        help="Stock symbol to sync all data for, e.g., SH688041, SZ000001, BJ838169, 688041, 000001, 838169",
    ),
):
    """
    Sync all data for a specific stock symbol.
    Supports multiple formats:
    - With market prefix: SH688041, SZ000001, BJ838169
    - Without market prefix: 688041 (SH), 000001 (SZ), 838169 (BJ)

    Market prefix rules:
    - SH: Shanghai Exchange (6xxxxx)
    - SZ: Shenzhen Exchange (0xxxxx, 3xxxxx)
    - BJ: Beijing Exchange (4xxxxx, 8xxxxx)
    
    This command will sync all available data for the specified stock including:
    - Spot data
    - Historical data (last year, hfq)
    - Business composition
    - Financial debt (balance sheet)
    - Research reports
    - Financial abstract (key indicators)
    - Financial analysis (financial indicators)
    - Gdhs (股东户数详情)
    - Main holders (主要股东)
    """
    from core.sync import (
        sync_stock_zh_a_spot_em,
        sync_stock_zh_a_hist,
        sync_stock_business_composition,
        sync_stock_financial_debt,
        sync_stock_research_report,
        sync_stock_financial_abstract,
        sync_stock_financial_analysis,
        sync_stock_gdhs,
        sync_stock_main_holder
    )
    from datetime import datetime, timedelta
    import traceback

    typer.echo(f"Starting full data synchronization for symbol: {symbol}...")
    
    # Format symbol
    formatted_symbol = symbol
    if not symbol.startswith(("SH", "SZ", "BJ")):
        if symbol.startswith("6"):
            formatted_symbol = f"SH{symbol}"
        elif symbol.startswith(("0", "3")):
            formatted_symbol = f"SZ{symbol}"
        elif symbol.startswith(("4", "8")):
            formatted_symbol = f"BJ{symbol}"
        else:
            formatted_symbol = f"SH{symbol}"  # Default to SH
    
    success_count = 0
    fail_count = 0
    
    # Sync spot data
    try:
        sync_stock_zh_a_spot_em()
        success_count += 1
        typer.echo("✓ Spot data synchronized")
    except Exception as e:
        fail_count += 1
        typer.echo(f"✗ Failed to sync spot data: {e}")
        typer.echo(f"Details: {traceback.format_exc()}")

    # Sync historical data (last year, hfq)
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        sync_stock_zh_a_hist(formatted_symbol, "daily", start_date, end_date, "hfq")
        success_count += 1
        typer.echo("✓ Historical data synchronized")
    except Exception as e:
        fail_count += 1
        typer.echo(f"✗ Failed to sync historical data: {e}")
        typer.echo(f"Details: {traceback.format_exc()}")

    # Sync business composition
    try:
        sync_stock_business_composition(formatted_symbol)
        success_count += 1
        typer.echo("✓ Business composition data synchronized")
    except Exception as e:
        fail_count += 1
        typer.echo(f"✗ Failed to sync business composition data: {e}")
        typer.echo(f"Details: {traceback.format_exc()}")

    # Sync financial debt
    try:
        sync_stock_financial_debt(formatted_symbol)
        success_count += 1
        typer.echo("✓ Financial debt data synchronized")
    except Exception as e:
        fail_count += 1
        typer.echo(f"✗ Failed to sync financial debt data: {e}")
        typer.echo(f"Details: {traceback.format_exc()}")

    # Sync research report
    try:
        sync_stock_research_report(formatted_symbol)
        success_count += 1
        typer.echo("✓ Research report data synchronized")
    except Exception as e:
        fail_count += 1
        typer.echo(f"✗ Failed to sync research report data: {e}")
        typer.echo(f"Details: {traceback.format_exc()}")

    # Sync financial abstract
    try:
        sync_stock_financial_abstract(formatted_symbol)
        success_count += 1
        typer.echo("✓ Financial abstract data synchronized")
    except Exception as e:
        fail_count += 1
        typer.echo(f"✗ Failed to sync financial abstract data: {e}")
        typer.echo(f"Details: {traceback.format_exc()}")

    # Sync financial analysis
    try:
        sync_stock_financial_analysis(formatted_symbol)
        success_count += 1
        typer.echo("✓ Financial analysis data synchronized")
    except Exception as e:
        fail_count += 1
        typer.echo(f"✗ Failed to sync financial analysis data: {e}")
        typer.echo(f"Details: {traceback.format_exc()}")

    # Sync gdhs
    try:
        sync_stock_gdhs(formatted_symbol)
        success_count += 1
        typer.echo("✓ Gdhs data synchronized")
    except Exception as e:
        fail_count += 1
        typer.echo(f"✗ Failed to sync gdhs data: {e}")
        typer.echo(f"Details: {traceback.format_exc()}")

    # Sync main holder
    try:
        sync_stock_main_holder(formatted_symbol)
        success_count += 1
        typer.echo("✓ Main holder data synchronized")
    except Exception as e:
        fail_count += 1
        typer.echo(f"✗ Failed to sync main holder data: {e}")
        typer.echo(f"Details: {traceback.format_exc()}")

    typer.echo(f"Full data synchronization completed for {symbol}.")
    typer.echo(f"Successful operations: {success_count}, Failed operations: {fail_count}")


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