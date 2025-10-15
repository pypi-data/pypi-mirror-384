#!/usr/bin/env python3
"""
User-Friendly Session Manager for Cite-Agent
Handles session detection, user choices, and authentication flow
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text

class SessionManager:
    """User-friendly session management for Cite-Agent"""
    
    def __init__(self):
        self.console = Console()
        self.session_file = Path.home() / ".nocturnal_archive" / "session.json"
        self.config_file = Path.home() / ".nocturnal_archive" / "config.env"
        self.session_data: Optional[Dict[str, Any]] = None
    
    def detect_existing_session(self) -> bool:
        """Detect if there's an existing session and load it"""
        if not self.session_file.exists():
            return False
        
        try:
            with open(self.session_file, 'r') as f:
                self.session_data = json.load(f)
                return True
        except Exception as e:
            self.console.print(f"[red]⚠️ Session file corrupted: {e}[/red]")
            return False
    
    def show_session_info(self):
        """Display existing session information in a user-friendly way"""
        if not self.session_data:
            return
        
        email = self.session_data.get('email', 'Unknown')
        user_id = self.session_data.get('user_id', 'Unknown')[:8] + "..."
        expires_at = self.session_data.get('expires_at', 'Unknown')
        daily_limit = self.session_data.get('daily_token_limit', 0)
        
        # Create a nice table
        table = Table(title="🔑 Existing Session Found", show_header=True, header_style="bold green")
        table.add_column("Property", style="cyan", width=15)
        table.add_column("Value", style="white")
        
        table.add_row("Email", email)
        table.add_row("User ID", user_id)
        table.add_row("Daily Limit", f"{daily_limit:,} queries")
        table.add_row("Expires", expires_at)
        
        self.console.print()
        self.console.print(table)
        self.console.print()
    
    def ask_session_choice(self) -> str:
        """Ask user what they want to do with the existing session"""
        self.console.print("[bold cyan]What would you like to do?[/bold cyan]")
        self.console.print()
        
        # Create a nice menu
        menu_table = Table(show_header=False, box=None, padding=(0, 1))
        menu_table.add_column("Choice", style="bold green", width=3)
        menu_table.add_column("Action", style="white", width=20)
        menu_table.add_column("Description", style="dim", width=40)
        
        menu_table.add_row("1", "Resume", "Continue with this session")
        menu_table.add_row("2", "Switch", "Login with different account")
        menu_table.add_row("3", "Logout", "Clear session and start fresh")
        menu_table.add_row("4", "Help", "Show session management help")
        
        self.console.print(menu_table)
        self.console.print()
        
        while True:
            choice = Prompt.ask(
                "Choose an option",
                choices=["1", "2", "3", "4", "resume", "switch", "logout", "help"],
                default="1"
            ).lower()
            
            if choice in ["1", "resume"]:
                return "resume"
            elif choice in ["2", "switch"]:
                return "switch"
            elif choice in ["3", "logout"]:
                return "logout"
            elif choice in ["4", "help"]:
                self.show_help()
                continue
            else:
                self.console.print("[red]Invalid choice. Please try again.[/red]")
    
    def show_help(self):
        """Show help for session management"""
        help_text = """
[bold cyan]Session Management Help[/bold cyan]

[bold green]Resume:[/bold green] Continue with your existing session
• Use your current login and settings
• No need to re-authenticate
• All your data and preferences are preserved

[bold yellow]Switch:[/bold yellow] Login with a different account
• Logout from current session
• Start fresh with new account
• Previous session data will be cleared

[bold red]Logout:[/bold red] Clear session and start fresh
• Remove all saved login information
• Start completely fresh
• You'll need to login again

[bold blue]Session Files:[/bold blue]
• Session: ~/.nocturnal_archive/session.json
• Config: ~/.nocturnal_archive/config.env

[bold blue]Manual Session Management:[/bold blue]
• To clear session manually: rm ~/.nocturnal_archive/session.json
• To clear config: rm ~/.nocturnal_archive/config.env
        """
        
        self.console.print(Panel(help_text, title="Help", border_style="blue"))
        self.console.print()
    
    def clear_session(self) -> bool:
        """Clear the existing session"""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
            if self.config_file.exists():
                self.config_file.unlink()
            self.console.print("[green]✅ Session cleared successfully[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]❌ Error clearing session: {e}[/red]")
            return False
    
    def handle_session_affirmation(self) -> str:
        """Main function to handle session affirmation with user-friendly interface"""
        # Check for existing session
        has_session = self.detect_existing_session()
        
        if not has_session:
            self.console.print("[yellow]No existing session found. Starting fresh...[/yellow]")
            return "fresh"
        
        # Show session information
        self.show_session_info()
        
        # Ask user what to do
        choice = self.ask_session_choice()
        
        if choice == "resume":
            self.console.print("[green]✅ Resuming existing session...[/green]")
            return "resume"
        elif choice == "switch":
            self.console.print("[yellow]🔄 Switching to different account...[/yellow]")
            if self.clear_session():
                return "fresh"
            else:
                return "error"
        elif choice == "logout":
            self.console.print("[red]🚪 Logging out...[/red]")
            if self.clear_session():
                return "fresh"
            else:
                return "error"
        
        return "error"
    
    def setup_environment_variables(self):
        """Set up environment variables for backend mode"""
        # PRIORITY 1: Check if user has production credentials
        # If they do, force production mode (ignore .env.local)
        from pathlib import Path
        session_file = Path.home() / ".nocturnal_archive" / "session.json"
        has_session = session_file.exists()
        has_config_creds = (
            os.getenv("NOCTURNAL_ACCOUNT_EMAIL") and 
            os.getenv("NOCTURNAL_AUTH_TOKEN")
        )
        
        if has_session or has_config_creds:
            # User is logged in → FORCE production mode
            os.environ["USE_LOCAL_KEYS"] = "false"
            if "NOCTURNAL_API_URL" not in os.environ:
                os.environ["NOCTURNAL_API_URL"] = "https://cite-agent-api-720dfadd602c.herokuapp.com/api"
            
            debug = os.getenv("NOCTURNAL_DEBUG", "").lower() == "1"
            if debug:
                print(f"🔍 Production mode: User has credentials, ignoring .env.local")
        else:
            # No production credentials → Allow dev mode from .env.local
            try:
                from dotenv import load_dotenv
                env_local = Path.home() / ".nocturnal_archive" / ".env.local"
                if env_local.exists():
                    load_dotenv(env_local)
                    debug = os.getenv("NOCTURNAL_DEBUG", "").lower() == "1"
                    if debug:
                        print(f"🔍 Loaded .env.local: USE_LOCAL_KEYS={os.getenv('USE_LOCAL_KEYS')}")
            except Exception as e:
                debug = os.getenv("NOCTURNAL_DEBUG", "").lower() == "1"
                if debug:
                    print(f"⚠️ Failed to load .env.local: {e}")
            
            # Default to production if no explicit dev mode
            if "USE_LOCAL_KEYS" not in os.environ:
                os.environ["USE_LOCAL_KEYS"] = "false"
            if "NOCTURNAL_API_URL" not in os.environ:
                os.environ["NOCTURNAL_API_URL"] = "https://cite-agent-api-720dfadd602c.herokuapp.com/api"
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status for debugging"""
        return {
            "session_file_exists": self.session_file.exists(),
            "config_file_exists": self.config_file.exists(),
            "session_data": self.session_data,
            "use_local_keys": os.environ.get("USE_LOCAL_KEYS", "not set"),
            "api_url": os.environ.get("NOCTURNAL_API_URL", "not set")
        }

def main():
    """Test the session manager"""
    sm = SessionManager()
    result = sm.handle_session_affirmation()
    print(f"Result: {result}")
    
    # Show status
    status = sm.get_session_status()
    print(f"Status: {status}")

if __name__ == "__main__":
    main()