# 用于指令
from typing import Annotated
import typer
import akshare as ak
from trading_grid.version import VERSION


app = typer.Typer()


@app.command()
def version():
    """
    Print the version of the Stock Chose Tradinig Grid Service CLI.
    """
    typer.echo(f"Stock Chose Tradinig Grid Service CLI version: {VERSION}")


@app.command()
def start(
    host: str = typer.Option("127.0.0.1", help="Host to run the service on"),
    port: int = typer.Option(8000, help="Port to run the service on"),
):
    """
    Start the FastAPI service for Stock Chose Trading Grid.
    """
    import uvicorn
    from trading_grid.api.app import app as fastapi_app

    typer.echo(f"Starting Stock Chose Trading Grid Service on {host}:{port}")
    uvicorn.run(fastapi_app, host=host, port=port)