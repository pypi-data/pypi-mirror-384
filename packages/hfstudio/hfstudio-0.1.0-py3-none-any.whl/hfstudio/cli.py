import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel

console = Console()

def main(
    port: int = typer.Option(11110, "--port", "-p", help="Port to run the server on"),
    host: str = typer.Option("0.0.0.0", "--host", help="Host to run the server on"),
    dev: bool = typer.Option(False, "--dev", help="Run in development mode"),
):
    """Start the HFStudio server"""
    
    console.print(Panel.fit(
        "[bold green]HFStudio Server[/bold green]\n"
        f"Running on http://{host if host != '0.0.0.0' else 'localhost'}:{port}\n"
        f"API docs: http://localhost:{port}/docs",
        title="🎙️ HFStudio",
        border_style="green"
    ))
    
    uvicorn.run(
        "hfstudio.server:app",
        host=host,
        port=port,
        reload=dev,
        log_level="info" if not dev else "debug"
    )

if __name__ == "__main__":
    typer.run(main)