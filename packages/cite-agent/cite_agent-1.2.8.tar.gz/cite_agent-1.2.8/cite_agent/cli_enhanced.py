#!/usr/bin/env python3
"""
Nocturnal Archive CLI - Simple, Clean, Functional
Like Cursor/Claude - no clutter
"""

import argparse
import asyncio
import sys
from typing import Optional

from .enhanced_ai_agent import EnhancedNocturnalAgent, ChatRequest
from .ui import NocturnalUI, console
from .auth import AuthManager
from .setup_config import NocturnalConfig
from .telemetry import TelemetryManager

class NocturnalCLI:
    """Simple CLI - no bloat"""
    
    def __init__(self):
        self.agent: Optional[EnhancedNocturnalAgent] = None
        self.auth = AuthManager()
        self.session = None
        self.telemetry = None
        self.queries_today = 0
        self.daily_limit = 25
        
    async def run(self):
        """Main entry point"""
        try:
            # Quick welcome
            NocturnalUI.show_welcome()
            
            # Check auth
            self.session = self.auth.get_session()
            
            if not self.session:
                # Login or register
                if not await self._handle_auth():
                    return
            
            # Initialize agent
            if not await self._init_agent():
                return
            
            # Show status
            email = self.session.get("email", "user")
            NocturnalUI.show_status(email, self.queries_today, self.daily_limit)
            
            # Start chat loop
            await self._chat_loop()
            
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!")
        except Exception as e:
            NocturnalUI.show_error(f"Something went wrong: {e}")
    
    async def _handle_auth(self) -> bool:
        """Handle login or registration"""
        choice = console.input("[1] Login  [2] Register  [3] Exit\n> ").strip()
        
        if choice == "1":
            email, password = NocturnalUI.prompt_login()
            try:
                with NocturnalUI.show_thinking():
                    self.session = self.auth.login(email, password)
                NocturnalUI.show_success("Logged in!")
                return True
            except Exception as e:
                NocturnalUI.show_error(f"Login failed: {e}")
                return False
        
        elif choice == "2":
            email, password, license_key = NocturnalUI.prompt_register()
            try:
                with NocturnalUI.show_thinking():
                    self.session = self.auth.register(email, password, license_key)
                NocturnalUI.show_success("Account created!")
                return True
            except Exception as e:
                NocturnalUI.show_error(f"Registration failed: {e}")
                return False
        
        return False
    
    async def _init_agent(self) -> bool:
        """Initialize the AI agent"""
        try:
            config = NocturnalConfig()
            self.telemetry = TelemetryManager(config)
            self.agent = EnhancedNocturnalAgent(config, self.telemetry)
            return True
        except Exception as e:
            NocturnalUI.show_error(f"Failed to initialize: {e}")
            return False
    
    async def _chat_loop(self):
        """Main chat loop - polished and responsive"""
        while True:
            try:
                # Get query
                query = NocturnalUI.prompt_query()
                
                if not query.strip():
                    continue
                
                # Handle special commands
                if query.lower() in ['exit', 'quit', 'q']:
                    console.print("\n[dim]Thanks for using Nocturnal Archive![/dim]\n")
                    break
                elif query.lower() == 'clear':
                    console.clear()
                    email = self.session.get("email", "user")
                    NocturnalUI.show_status(email, self.queries_today, self.daily_limit)
                    continue
                elif query.lower() == 'logout':
                    self.auth.logout()
                    NocturnalUI.show_success("Logged out successfully")
                    break
                elif query.lower() in ['help', '?']:
                    NocturnalUI.show_help()
                    continue
                
                # Check daily limit
                if self.queries_today >= self.daily_limit:
                    NocturnalUI.show_error(
                        f"You've reached your daily limit of {self.daily_limit} queries.\n"
                        "Your limit resets tomorrow. Thanks for using Nocturnal Archive!"
                    )
                    continue
                
                # Process query
                with NocturnalUI.show_thinking():
                    request = ChatRequest(
                        question=query,
                        user_id=self.session.get("user_id", "unknown")
                    )
                    response = await self.agent.process_request(request)
                
                # Show response with metadata
                metadata = {
                    "tools_used": response.tools_used if response.tools_used else None,
                    "sources": f"{len(response.tools_used)} sources" if response.tools_used else None
                }
                NocturnalUI.show_response(response.response, metadata)
                
                self.queries_today += 1
                
                # Update status in session
                email = self.session.get("email", "user")
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                # Graceful error handling
                NocturnalUI.show_error(
                    f"Something went wrong: {str(e)}\n"
                    "The error has been logged. Please try rephrasing your question."
                )
                
                # Log for developer
                self._log_error(query if 'query' in locals() else "unknown", str(e))
    
    def _log_error(self, query: str, error: str):
        """Simple error logging - just append to file for dev to check"""
        import datetime
        from pathlib import Path
        
        log_dir = Path.home() / ".nocturnal_archive"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / "errors.log"
        
        timestamp = datetime.datetime.now().isoformat()
        email = self.session.get("email", "unknown")
        
        with open(log_file, "a") as f:
            f.write(f"\n--- {timestamp} ---\n")
            f.write(f"User: {email}\n")
            f.write(f"Query: {query}\n")
            f.write(f"Error: {error}\n")

def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description="Nocturnal Archive - Research & Finance Intelligence")
    parser.add_argument("query", nargs="*", help="Single query to run")
    parser.add_argument("--logout", action="store_true", help="Log out")
    parser.add_argument("--version", action="store_true", help="Show version")
    
    args = parser.parse_args()
    
    if args.logout:
        AuthManager().logout()
        print("Logged out")
        return
    
    if args.version:
        print("Nocturnal Archive v1.0.0-beta")
        return
    
    # Run CLI
    cli = NocturnalCLI()
    asyncio.run(cli.run())

if __name__ == "__main__":
    main()
