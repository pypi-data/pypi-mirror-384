"""
Polished Terminal UI - Inspired by Cursor/Claude
Clean, professional, with subtle visual hierarchy
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich import box
from contextlib import contextmanager
import time

console = Console()

class NocturnalUI:
    """Polished terminal UI - clean with subtle hierarchy"""
    
    # Color palette (subtle, professional)
    ACCENT = "cyan"
    DIM = "dim"
    SUCCESS = "green"
    ERROR = "red"
    
    @staticmethod
    def show_welcome():
        """Welcome screen - quick and polished"""
        console.clear()
        
        # Quick loading with style
        with Progress(
            SpinnerColumn(spinner_name="dots", style="cyan"),
            TextColumn("[cyan]Initializing Nocturnal Archive...[/cyan]"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task("", total=None)
            time.sleep(1.0)
        
        # Clean header with subtle styling
        console.print()
        console.print("┌" + "─" * 58 + "┐", style="dim")
        console.print("│  [bold cyan]Nocturnal Archive[/bold cyan]" + " " * 35 + "│", style="dim")
        console.print("│  [dim]Research & Finance Intelligence Terminal[/dim]" + " " * 10 + "│", style="dim")
        console.print("└" + "─" * 58 + "┘", style="dim")
        console.print()
    
    @staticmethod
    def prompt_login() -> tuple[str, str]:
        """Login prompt with subtle panel"""
        console.print()
        console.print("[dim]─── Authentication ───[/dim]")
        console.print()
        
        email = Prompt.ask("[cyan]Email[/cyan]", console=console)
        password = Prompt.ask("[cyan]Password[/cyan]", password=True, console=console)
        
        return email, password
    
    @staticmethod
    def prompt_register() -> tuple[str, str, str]:
        """Registration prompt with subtle panel"""
        console.print()
        console.print("[dim]─── Create Account ───[/dim]")
        console.print()
        
        email = Prompt.ask("[cyan]Email[/cyan]", console=console)
        password = Prompt.ask("[cyan]Password[/cyan]", password=True, console=console)
        license_key = Prompt.ask("[cyan]License Key[/cyan]", console=console)
        
        return email, password, license_key
    
    @staticmethod
    def show_status(email: str, queries_today: int, daily_limit: int):
        """Status bar - subtle and informative"""
        remaining = daily_limit - queries_today
        status_color = "green" if remaining > 10 else "yellow" if remaining > 5 else "red"
        
        console.print()
        console.print(
            f"[dim]{email}[/dim]  │  [{status_color}]{queries_today}/{daily_limit}[/{status_color}] [dim]queries today[/dim]"
        )
        console.print("[dim]" + "─" * 60 + "[/dim]")
        console.print()
    
    @staticmethod
    def prompt_query() -> str:
        """Get user query with styled prompt"""
        return Prompt.ask("[bold cyan]❯[/bold cyan]", console=console)
    
    @staticmethod
    @contextmanager
    def show_thinking():
        """Thinking spinner - polished"""
        with Progress(
            SpinnerColumn(spinner_name="dots", style="cyan"),
            TextColumn("[dim]Processing your query...[/dim]"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task("", total=None)
            yield
    
    @staticmethod
    def show_response(response: str, metadata: dict = None):
        """Show agent response with subtle styling"""
        console.print()
        
        # Response content
        console.print(response)
        
        # Optional metadata footer (minimal)
        if metadata:
            console.print()
            meta_parts = []
            if metadata.get("tools_used"):
                meta_parts.append(f"[dim]Tools: {', '.join(metadata['tools_used'])}[/dim]")
            if metadata.get("sources"):
                meta_parts.append(f"[dim]Sources: {metadata['sources']}[/dim]")
            if meta_parts:
                console.print(" • ".join(meta_parts))
        
        console.print()
    
    @staticmethod
    def show_error(message: str):
        """Error message - clear but not aggressive"""
        console.print()
        console.print(f"[red]✗[/red] {message}")
        console.print()
    
    @staticmethod
    def show_success(message: str):
        """Success message - subtle confirmation"""
        console.print()
        console.print(f"[green]✓[/green] {message}")
        console.print()
    
    @staticmethod
    def show_info(message: str):
        """Info message"""
        console.print()
        console.print(f"[dim]ℹ[/dim] {message}")
        console.print()
    
    @staticmethod
    def show_help():
        """Show help message - clean list"""
        console.print()
        console.print("[bold cyan]Commands[/bold cyan]")
        console.print("[dim]─────────[/dim]")
        console.print("  [cyan]help[/cyan]    Show this help message")
        console.print("  [cyan]clear[/cyan]   Clear the screen")
        console.print("  [cyan]logout[/cyan]  Log out of your account")
        console.print("  [cyan]exit[/cyan]    Exit the application")
        console.print()
    
    @staticmethod
    def show_tips(tips: list = None):
        """Show helpful tips - clean list"""
        if tips is None:
            tips = [
                "Try: 'Find papers about transformers'",
                "Ask: 'What's Apple's latest revenue?'",
                "Query: 'Analyze sentiment in tech stocks'",
                "Search: 'Compare Google vs Microsoft earnings'",
            ]
        
        console.print()
        console.print("[bold cyan]Tips[/bold cyan]")
        console.print("[dim]────[/dim]")
        for tip in tips:
            console.print(f"  [dim]•[/dim] {tip}")
        console.print()