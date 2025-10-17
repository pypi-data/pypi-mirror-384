"""
MCPlaywright CLI

Command-line interface for the MCPlaywright MCP server.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

from __init__ import __version__
from server import app, main as server_main

console = Console()

def setup_logging(level: str = "INFO") -> None:
    """Set up rich logging"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(name)s - %(message)s",
        handlers=[RichHandler(console=console, show_path=False)]
    )

@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version information")
@click.pass_context
def main(ctx: click.Context, version: bool) -> None:
    """
    MCPlaywright - Python Playwright MCP Server
    
    Advanced browser automation with video recording, request monitoring, and UI customization.
    """
    if version:
        console.print(f"MCPlaywright v{__version__}")
        return
        
    if ctx.invoked_subcommand is None:
        console.print(Panel.fit(
            f"[bold blue]MCPlaywright v{__version__}[/bold blue]\n\n"
            "Python Playwright MCP Server with advanced features:\n"
            "• Smart video recording with multiple modes\n" 
            "• HTTP request monitoring and analysis\n"
            "• Browser UI customization\n"
            "• Session-based automation\n\n"
            "Use [bold]mcplaywright --help[/bold] to see available commands.",
            title="MCPlaywright MCP Server"
        ))

@main.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", type=int, default=8000, help="Port to bind to") 
@click.option("--log-level", default="INFO", help="Logging level")
@click.option("--dev", is_flag=True, help="Development mode with hot reload")
def serve(host: str, port: int, log_level: str, dev: bool) -> None:
    """Start the MCPlaywright MCP server"""
    
    setup_logging(log_level)
    
    console.print(Panel(
        f"[bold green]Starting MCPlaywright MCP Server[/bold green]\n\n"
        f"Host: [blue]{host}[/blue]\n"
        f"Port: [blue]{port}[/blue]\n" 
        f"Log Level: [blue]{log_level}[/blue]\n"
        f"Development Mode: [blue]{'Yes' if dev else 'No'}[/blue]",
        title="Server Configuration"
    ))
    
    try:
        if dev:
            # Development mode with uvicorn hot reload
            import uvicorn
            uvicorn.run(
                "mcplaywright.server:app",
                host=host,
                port=port,
                log_level=log_level.lower(),
                reload=True,
                reload_dirs=["src/mcplaywright"]
            )
        else:
            # Production mode
            sys.argv = [
                "mcplaywright", 
                "--host", host,
                "--port", str(port),
                "--log-level", log_level
            ]
            server_main()
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Server shutdown requested[/yellow]")
    except Exception as e:
        console.print(f"[red]Server failed to start: {str(e)}[/red]")
        sys.exit(1)

@main.command()
@click.option("--browser", default="chromium", help="Browser to test (chromium, firefox, webkit)")
async def test_playwright(browser: str) -> None:
    """Test Playwright installation and browser availability"""
    
    setup_logging()
    
    console.print("[blue]Testing Playwright installation...[/blue]")
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Create test table
            table = Table(title="Playwright Browser Test Results")
            table.add_column("Browser", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Executable", style="dim")
            
            browsers = [
                ("chromium", p.chromium),
                ("firefox", p.firefox),
                ("webkit", p.webkit)
            ]
            
            for browser_name, browser_type in browsers:
                try:
                    executable = browser_type.executable_path
                    if Path(executable).exists():
                        table.add_row(
                            browser_name.title(),
                            "[green]✓ Available[/green]", 
                            str(executable)
                        )
                    else:
                        table.add_row(
                            browser_name.title(),
                            "[red]✗ Not Found[/red]",
                            "Not installed"
                        )
                except Exception as e:
                    table.add_row(
                        browser_name.title(),
                        "[red]✗ Error[/red]",
                        str(e)
                    )
            
            console.print(table)
            
            # Test launching the specified browser
            if browser in ["chromium", "firefox", "webkit"]:
                console.print(f"\n[blue]Testing {browser} launch...[/blue]")
                
                browser_type = getattr(p, browser)
                test_browser = await browser_type.launch(headless=True)
                page = await test_browser.new_page()
                await page.goto("data:text/html,<h1>Playwright Test</h1>")
                title = await page.title()
                await test_browser.close()
                
                console.print(f"[green]✓ {browser.title()} launched successfully[/green]")
                console.print(f"[dim]Page title: {title}[/dim]")
            
    except ImportError:
        console.print("[red]✗ Playwright not installed[/red]")
        console.print("Install with: [blue]playwright install[/blue]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Test failed: {str(e)}[/red]")
        sys.exit(1)

@main.command()
async def health() -> None:
    """Check server health (requires running server)"""
    
    setup_logging()
    
    try:
        import httpx
        
        console.print("[blue]Checking server health...[/blue]")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/health_check",
                json={"method": "health_check", "params": {}},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                table = Table(title="Server Health Status")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                for key, value in data.items():
                    table.add_row(key.replace("_", " ").title(), str(value))
                
                console.print(table)
            else:
                console.print(f"[red]Health check failed: HTTP {response.status_code}[/red]")
                
    except ImportError:
        console.print("[red]httpx not installed (required for health checks)[/red]")
        console.print("Install with: [blue]pip install httpx[/blue]")
    except Exception as e:
        console.print(f"[red]Health check failed: {str(e)}[/red]")
        console.print("[dim]Make sure the server is running on localhost:8000[/dim]")

@main.command()
def info() -> None:
    """Show detailed information about MCPlaywright"""
    
    console.print(Panel(
        f"[bold blue]MCPlaywright v{__version__}[/bold blue]\n\n"
        "[bold]Description:[/bold]\n"
        "Advanced Python Playwright MCP server with comprehensive browser automation capabilities.\n\n"
        "[bold]Key Features:[/bold]\n"
        "• Smart video recording with auto-pause/resume\n"
        "• Advanced HTTP request monitoring and export\n" 
        "• Browser UI customization (themes, slowMo, devtools)\n"
        "• Session-based persistent browser contexts\n"
        "• Multi-browser support (Chromium, Firefox, WebKit)\n"
        "• FastMCP 2.0 integration with production features\n\n"
        "[bold]Architecture:[/bold]\n"
        "• Context management for persistent sessions\n"
        "• Artifact management with organized storage\n" 
        "• Advanced error handling and logging\n"
        "• Performance monitoring and health checks\n\n"
        "[bold]Testing:[/bold]\n"
        "• Comprehensive pytest suite with HTML reports\n"
        "• Performance benchmarking vs TypeScript version\n"
        "• Multi-browser compatibility testing\n"
        "• Container-based CI/CD testing",
        title="MCPlaywright Information",
        border_style="blue"
    ))

if __name__ == "__main__":
    # Handle async commands
    import asyncio
    import inspect
    
    # Patch click to support async commands
    def async_command(f):
        if inspect.iscoroutinefunction(f):
            def wrapper(*args, **kwargs):
                return asyncio.run(f(*args, **kwargs))
            return wrapper
        return f
    
    # Apply async wrapper to async commands
    test_playwright.callback = async_command(test_playwright.callback)
    health.callback = async_command(health.callback)
    
    main()