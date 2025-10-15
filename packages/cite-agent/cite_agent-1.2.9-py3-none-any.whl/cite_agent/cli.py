#!/usr/bin/env python3
"""
Cite Agent CLI - Command Line Interface
Provides a terminal interface similar to cursor-agent
"""

import argparse
import asyncio
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

from .enhanced_ai_agent import EnhancedNocturnalAgent, ChatRequest
from .setup_config import NocturnalConfig, DEFAULT_QUERY_LIMIT, MANAGED_SECRETS
from .telemetry import TelemetryManager
from .updater import NocturnalUpdater
from .cli_workflow import WorkflowCLI
from .workflow import WorkflowManager, Paper, parse_paper_from_response
from .session_manager import SessionManager

class NocturnalCLI:
    """Command Line Interface for Cite Agent"""
    
    def __init__(self):
        self.agent: Optional[EnhancedNocturnalAgent] = None
        self.session_id = f"cli_{os.getpid()}"
        self.telemetry = None
        self.workflow = WorkflowManager()
        self.workflow_cli = WorkflowCLI()
        self.console = Console(theme=Theme({
            "banner": "bold magenta",
            "success": "bold green",
            "warning": "bold yellow",
            "error": "bold red",
        }))
        self._tips = [
            "Use [bold]nocturnal --setup[/] to rerun the onboarding wizard anytime.",
            "Run [bold]nocturnal tips[/] when you need a refresher on power moves.",
            "Pass a one-off question directly: [bold]nocturnal \"summarize the latest 10-Q\"[/].",
            "Enable verbose logging by exporting [bold]NOCTURNAL_DEBUG=1[/] before launching.",
            "Use [bold]/plan[/] inside the chat to nudge the agent toward structured research steps.",
            "Hit [bold]Ctrl+C[/] to stop a long-running call; the agent will clean up gracefully.",
            "Remember the sandbox: prefix shell commands with [bold]![/] to execute safe utilities only.",
            "If you see an auto-update notice, the CLI will restart itself to load the latest build.",
        ]
    
    def handle_user_friendly_session(self):
        """Handle session management with user-friendly interface"""
        session_manager = SessionManager()
        
        # Set up environment variables for backend mode
        session_manager.setup_environment_variables()
        
        # Handle session affirmation
        result = session_manager.handle_session_affirmation()
        
        if result == "error":
            self.console.print("[red]❌ Session management failed. Please try again.[/red]")
            return False
        
        return True
    
    async def initialize(self, non_interactive: bool = False):
        """Initialize the agent with automatic updates"""
        # Check for update notifications from previous runs
        self._check_update_notification()
        
        # Handle user-friendly session management (skip prompts in non-interactive mode)
        if not non_interactive:
            if not self.handle_user_friendly_session():
                return False
        
        self._show_intro_panel()

        self._enforce_latest_build()

        config = NocturnalConfig()
        had_config = config.setup_environment()
        TelemetryManager.refresh()
        self.telemetry = TelemetryManager.get()

        if not config.check_setup():
            # Check if we have env vars or session file (non-interactive mode)
            from pathlib import Path
            session_file = Path.home() / ".nocturnal_archive" / "session.json"
            has_env_creds = os.getenv("NOCTURNAL_ACCOUNT_EMAIL") and os.getenv("NOCTURNAL_ACCOUNT_PASSWORD")
            use_local_keys = os.getenv("USE_LOCAL_KEYS", "").lower() == "true"
            
            if session_file.exists() or has_env_creds or use_local_keys:
                # Skip interactive setup if session exists, env vars present, or using local keys
                if use_local_keys and not session_file.exists():
                    # Only show dev mode if explicitly in dev mode (no session)
                    self.console.print("[success]⚙️  Dev mode - using local API keys.[/success]")
                else:
                    self.console.print("[success]⚙️  Using saved credentials.[/success]")
            else:
                # Need interactive setup
                if non_interactive:
                    self.console.print("[error]❌ Not authenticated. Run 'cite-agent --setup' to configure.[/error]")
                    return False
                
                self.console.print("\n[warning]👋 Hey there, looks like this machine hasn't been set up yet.[/warning]")
                self.console.print("[banner]Let's get you signed in — this only takes a minute.[/banner]")
                try:
                    if not config.interactive_setup():
                        self.console.print("[error]❌ Setup was cancelled. Exiting without starting the agent.[/error]")
                        return False
                except (KeyboardInterrupt, EOFError):
                    self.console.print("\n[error]❌ Setup interrupted. Exiting without starting the agent.[/error]")
                    return False
            config.setup_environment()
            TelemetryManager.refresh()
            self.telemetry = TelemetryManager.get()
        elif not had_config:
            # config.setup_environment() may have populated env vars from file silently
            self.console.print("[success]⚙️  Loaded saved credentials for this device.[/success]")
        
        self.agent = EnhancedNocturnalAgent()
        success = await self.agent.initialize()
        
        if not success:
            self.console.print("[error]❌ Failed to initialize agent. Please check your configuration.[/error]")
            self.console.print("\n💡 Setup help:")
            self.console.print("   • Run `cite-agent --setup` to configure your account")
            self.console.print("   • Ensure you're logged in with valid credentials")
            self.console.print("   • Check your internet connection to the backend")
            return False
        
        # Only show panels in debug mode or interactive mode
        if not non_interactive or os.getenv("NOCTURNAL_DEBUG", "").lower() == "1":
            self._show_ready_panel()
            # Beta banner removed for production
        return True

    def _show_beta_banner(self):
        account_email = os.getenv("NOCTURNAL_ACCOUNT_EMAIL", "")
        configured_limit = DEFAULT_QUERY_LIMIT
        if configured_limit <= 0:
            limit_text = "Unlimited"
        else:
            limit_text = f"{configured_limit}"
        details = [
            f"Daily limit: [bold]{limit_text}[/] queries",
            "Telemetry streaming: [bold]enabled[/] (control plane)",
            "Auto-update: [bold]enforced[/] on launch",
            "Sandbox: safe shell commands only • SQL workflows supported",
        ]
        if account_email:
            details.insert(0, f"Signed in as: [bold]{account_email}[/]")

        panel = Panel(
            "\n".join(details),
            title="🎟️  Beta Access Active",
            border_style="magenta",
            padding=(1, 2),
            box=box.ROUNDED,
        )
        self.console.print(panel)

    def _show_intro_panel(self):
        # Only show in debug mode or interactive mode
        debug_mode = os.getenv("NOCTURNAL_DEBUG", "").lower() == "1"
        if not debug_mode:
            return
        
        message = (
            "Warming up your research cockpit…\n"
            "[dim]Loading config, telemetry, and background update checks.[/dim]"
        )
        panel = Panel(
            message,
            title="🤖  Initializing Cite Agent",
            border_style="magenta",
            padding=(1, 2),
            box=box.ROUNDED,
        )
        self.console.print(panel)

    def _show_ready_panel(self):
        panel = Panel(
            "Systems check complete.\n"
            "Type [bold]help[/] for commands or [bold]tips[/] for power moves.",
            title="✅ Cite Agent ready!",
            border_style="green",
            padding=(1, 2),
            box=box.ROUNDED,
        )
        self.console.print(panel)
    
    def _enforce_latest_build(self):
        """Ensure the CLI is running the most recent published build."""
        # Skip update check for beta - not published to PyPI yet
        # TODO: Re-enable after PyPI publication
        return

    def _restart_cli(self):
        """Re-exec the CLI using the current interpreter and arguments."""
        try:
            argv = [sys.executable, "-m", "nocturnal_archive.cli", *sys.argv[1:]]
            os.execv(sys.executable, argv)
        except Exception:
            # If restart fails just continue in the current process.
            pass
    
    def _save_update_notification(self, new_version):
        """Save update notification for next run"""
        try:
            import json
            from pathlib import Path
            
            notify_file = Path.home() / ".nocturnal_archive" / "update_notification.json"
            notify_file.parent.mkdir(exist_ok=True)
            
            with open(notify_file, 'w') as f:
                json.dump({
                    "updated_to": new_version,
                    "timestamp": time.time()
                }, f)
        except Exception:
            pass
    
    def _check_update_notification(self):
        """Check if we should show update notification"""
        try:
            import json
            import time
            from pathlib import Path
            
            notify_file = Path.home() / ".nocturnal_archive" / "update_notification.json"
            if notify_file.exists():
                with open(notify_file, 'r') as f:
                    data = json.load(f)
                
                # Show notification if update happened in last 24 hours
                if time.time() - data.get("timestamp", 0) < 86400:
                    self.console.print(f"[success]🎉 Updated to version {data['updated_to']}![/success]")
                    
                # Clean up notification
                notify_file.unlink()
                
        except Exception:
            pass
    
    async def interactive_mode(self):
        """Interactive chat mode"""
        if not await self.initialize():
            return
        
        self.console.print("\n[bold]🤖 Interactive Mode[/] — Type your questions or 'quit' to exit")
        self.console.rule(style="magenta")
        
        try:
            while True:
                try:
                    user_input = self.console.input("\n[bold cyan]👤 You[/]: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    if user_input.lower() == 'tips':
                        self.show_tips()
                        continue
                    if user_input.lower() == 'feedback':
                        self.collect_feedback()
                        continue

                    # Handle workflow commands
                    if user_input.lower() in ['show my library', 'library', 'list library']:
                        self.list_library()
                        continue
                    if user_input.lower() in ['show history', 'history']:
                        self.show_history()
                        continue
                    if user_input.lower().startswith('export bibtex'):
                        self.export_library_bibtex()
                        continue
                    if user_input.lower().startswith('export markdown'):
                        self.export_library_markdown()
                        continue

                    if not user_input:
                        continue
                except (EOFError, KeyboardInterrupt):
                    self.console.print("\n[warning]👋 Goodbye![/warning]")
                    break
                
                try:
                    from rich.spinner import Spinner
                    from rich.live import Live
                    
                    # Show loading indicator while processing
                    with Live(Spinner("dots", text="[dim]Thinking...[/dim]"), console=self.console, transient=True):
                        request = ChatRequest(
                            question=user_input,
                            user_id="cli_user",
                            conversation_id=self.session_id
                        )
                        
                        response = await self.agent.process_request(request)

                    # Print response with proper formatting
                    self.console.print("[bold violet]🤖 Agent[/]: ", end="", highlight=False)
                    self.console.print(response.response)

                    # Save to history automatically
                    self.workflow.save_query_result(
                        query=user_input,
                        response=response.response,
                        metadata={
                            "tools_used": response.tools_used,
                            "tokens_used": response.tokens_used,
                            "confidence_score": response.confidence_score
                        }
                    )

                    # Show usage stats occasionally
                    if hasattr(self.agent, 'daily_token_usage') and self.agent.daily_token_usage > 0:
                        stats = self.agent.get_usage_stats()
                        if stats['usage_percentage'] > 10:  # Show if >10% used
                            self.console.print(f"\n📊 Usage: {stats['usage_percentage']:.1f}% of daily limit")
                
                except Exception as e:
                    self.console.print(f"\n[error]❌ Error: {e}[/error]")
        
        finally:
            if self.agent:
                await self.agent.close()
    
    async def single_query(self, question: str):
        """Process a single query"""
        if not await self.initialize(non_interactive=True):
            return
        
        try:
            from rich.spinner import Spinner
            from rich.live import Live
            
            # Show clean loading indicator
            with Live(Spinner("dots", text=f"[cyan]{question}[/cyan]"), console=self.console, transient=True):
                request = ChatRequest(
                    question=question,
                    user_id="cli_user",
                    conversation_id=self.session_id
                )
                
                response = await self.agent.process_request(request)
            
            self.console.print(f"\n📝 [bold]Response[/]:\n{response.response}")
            
            # Tools used removed for cleaner output
            
            if response.tokens_used > 0:
                stats = self.agent.get_usage_stats()
                self.console.print(
                    f"\n📊 Tokens used: {response.tokens_used} "
                    f"(Daily usage: {stats['usage_percentage']:.1f}%)"
                )
        
        finally:
            if self.agent:
                await self.agent.close()
    
    def setup_wizard(self):
        """Interactive setup wizard"""
        config = NocturnalConfig()
        return config.interactive_setup()

    def show_tips(self):
        """Display a rotating set of CLI power tips"""
        sample_count = 4 if len(self._tips) >= 4 else len(self._tips)
        tips = random.sample(self._tips, sample_count)
        table = Table(show_header=False, box=box.MINIMAL_DOUBLE_HEAD, padding=(0, 1))
        for tip in tips:
            table.add_row(f"• {tip}")

        self.console.print(Panel(table, title="✨ Quick Tips", border_style="cyan", padding=(1, 2)))
        self.console.print("[dim]Run `nocturnal tips` again for a fresh batch.[/dim]")

    def collect_feedback(self) -> int:
        """Collect feedback from the user and store it locally"""
        self.console.print(
            Panel(
                "Share what's working, what feels rough, or any paper/finance workflows you wish existed.\n"
                "Press Enter on an empty line to finish.",
                title="📝 Beta Feedback",
                border_style="cyan",
                padding=(1, 2),
            )
        )

        lines = []
        while True:
            try:
                line = self.console.input("[dim]> [/]")
            except (KeyboardInterrupt, EOFError):
                self.console.print("[warning]Feedback capture cancelled.[/warning]")
                return 1

            if not line.strip():
                break
            lines.append(line)

        if not lines:
            self.console.print("[warning]No feedback captured — nothing was saved.[/warning]")
            return 1

        feedback_dir = Path.home() / ".nocturnal_archive" / "feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        feedback_path = feedback_dir / f"feedback-{timestamp}.md"

        content = "\n".join(lines)
        with open(feedback_path, "w", encoding="utf-8") as handle:
            handle.write("# Cite Agent Feedback\n")
            handle.write(f"timestamp = {timestamp}Z\n")
            handle.write("\n")
            handle.write(content)
            handle.write("\n")

        self.console.print(
            f"[success]Thanks for the intel! Saved to[/success] [bold]{feedback_path}[/bold]"
        )
        self.console.print("[dim]Attach that file when you send feedback to the team.[/dim]")
        return 0

    def list_library(self, tag: Optional[str] = None):
        """List papers in local library"""
        papers = self.workflow.list_papers(tag=tag)
        
        if not papers:
            self.console.print("[warning]No papers in library yet.[/warning]")
            self.console.print("[dim]Use --save-paper after a search to add papers.[/dim]")
            return
        
        table = Table(title=f"📚 Library ({len(papers)} papers)", box=box.ROUNDED)
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="bold")
        table.add_column("Authors", style="dim")
        table.add_column("Year", justify="right")
        table.add_column("Tags", style="yellow")
        
        for paper in papers[:20]:  # Show first 20
            authors_str = paper.authors[0] if paper.authors else "Unknown"
            if len(paper.authors) > 1:
                authors_str += " et al."
            
            tags_str = ", ".join(paper.tags) if paper.tags else ""
            
            table.add_row(
                paper.paper_id[:8],
                paper.title[:50] + "..." if len(paper.title) > 50 else paper.title,
                authors_str,
                str(paper.year),
                tags_str
            )
        
        self.console.print(table)
        
        if len(papers) > 20:
            self.console.print(f"[dim]... and {len(papers) - 20} more papers[/dim]")

    def export_library_bibtex(self):
        """Export library to BibTeX"""
        success = self.workflow.export_to_bibtex()
        if success:
            self.console.print(f"[success]✅ Exported to:[/success] [bold]{self.workflow.bibtex_file}[/bold]")
            self.console.print("[dim]Import this file into Zotero, Mendeley, or any citation manager.[/dim]")
        else:
            self.console.print("[error]❌ Failed to export BibTeX[/error]")

    def export_library_markdown(self):
        """Export library to Markdown"""
        success = self.workflow.export_to_markdown()
        if success:
            export_file = self.workflow.exports_dir / f"papers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            self.console.print(f"[success]✅ Exported to:[/success] [bold]{export_file}[/bold]")
            self.console.print("[dim]Open in Obsidian, Notion, or any markdown editor.[/dim]")
        else:
            self.console.print("[error]❌ Failed to export Markdown[/error]")

    def show_history(self, limit: int = 10):
        """Show recent query history"""
        history = self.workflow.get_history()[:limit]
        
        if not history:
            self.console.print("[warning]No query history yet.[/warning]")
            return
        
        table = Table(title=f"📜 Recent Queries", box=box.ROUNDED)
        table.add_column("Time", style="cyan")
        table.add_column("Query", style="bold")
        table.add_column("Tools", style="dim")
        
        for entry in history:
            timestamp = datetime.fromisoformat(entry['timestamp'])
            time_str = timestamp.strftime("%m/%d %H:%M")
            query_str = entry['query'][:60] + "..." if len(entry['query']) > 60 else entry['query']
            tools_str = ", ".join(entry.get('metadata', {}).get('tools_used', []))
            
            table.add_row(time_str, query_str, tools_str)
        
        self.console.print(table)

    def search_library_interactive(self, query: str):
        """Search papers in library"""
        results = self.workflow.search_library(query)
        
        if not results:
            self.console.print(f"[warning]No papers found matching '{query}'[/warning]")
            return
        
        self.console.print(f"[success]Found {len(results)} paper(s)[/success]\n")
        
        for i, paper in enumerate(results, 1):
            self.console.print(f"[bold cyan]{i}. {paper.title}[/bold cyan]")
            authors_str = ", ".join(paper.authors) if paper.authors else "Unknown"
            self.console.print(f"   Authors: {authors_str}")
            self.console.print(f"   Year: {paper.year} | ID: {paper.paper_id[:8]}")
            if paper.tags:
                self.console.print(f"   Tags: {', '.join(paper.tags)}")
            self.console.print()

    async def single_query_with_workflow(self, question: str, save_to_library: bool = False, 
                                         copy_to_clipboard: bool = False, export_format: Optional[str] = None):
        """Process a single query with workflow integration"""
        if not await self.initialize(non_interactive=True):
            return
        
        try:
            self.console.print(f"🤖 [bold]Processing[/]: {question}")
            self.console.rule(style="magenta")
            
            request = ChatRequest(
                question=question,
                user_id="cli_user",
                conversation_id=self.session_id
            )
            
            response = await self.agent.process_request(request)
            
            self.console.print(f"\n📝 [bold]Response[/]:\n{response.response}")
            
            # Tools used removed for cleaner output
            
            if response.tokens_used > 0:
                stats = self.agent.get_usage_stats()
                self.console.print(
                    f"\n📊 Tokens used: {response.tokens_used} "
                    f"(Daily usage: {stats['usage_percentage']:.1f}%)"
                )
            
            # Workflow integrations
            if copy_to_clipboard:
                if self.workflow.copy_to_clipboard(response.response):
                    self.console.print("[success]📋 Copied to clipboard[/success]")
            
            if export_format:
                if export_format == "bibtex":
                    # Try to parse paper from response
                    paper = parse_paper_from_response(response.response)
                    if paper:
                        bibtex = paper.to_bibtex()
                        self.console.print(f"\n[bold]BibTeX:[/bold]\n{bibtex}")
                        if copy_to_clipboard:
                            self.workflow.copy_to_clipboard(bibtex)
                    else:
                        self.console.print("[warning]Could not extract paper info for BibTeX[/warning]")
                
                elif export_format == "apa":
                    paper = parse_paper_from_response(response.response)
                    if paper:
                        apa = paper.to_apa_citation()
                        self.console.print(f"\n[bold]APA Citation:[/bold]\n{apa}")
                        if copy_to_clipboard:
                            self.workflow.copy_to_clipboard(apa)
            
            # Save to history
            self.workflow.save_query_result(
                query=question,
                response=response.response,
                metadata={
                    "tools_used": response.tools_used,
                    "tokens_used": response.tokens_used,
                    "confidence_score": response.confidence_score
                }
            )
            
            if save_to_library:
                paper = parse_paper_from_response(response.response)
                if paper:
                    if self.workflow.add_paper(paper):
                        self.console.print(f"[success]✅ Saved to library (ID: {paper.paper_id[:8]})[/success]")
                    else:
                        self.console.print("[error]❌ Failed to save to library[/error]")
        
        finally:
            if self.agent:
                await self.agent.close()

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Cite Agent - AI Research Assistant with real data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nocturnal                    # Interactive mode
  nocturnal "find papers on ML" # Single query
  nocturnal --setup            # Setup wizard
  nocturnal --version          # Show version
        """
    )
    
    parser.add_argument(
        'query', 
        nargs='?', 
        help='Single query to process (if not provided, starts interactive mode)'
    )
    
    parser.add_argument(
        '--setup', 
        action='store_true', 
        help='Run setup wizard for API keys'
    )
    
    parser.add_argument(
        '--version', 
        action='store_true', 
        help='Show version information'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Force interactive mode even with query'
    )
    
    parser.add_argument(
        '--update',
        action='store_true',
        help='Check for and install updates'
    )
    
    parser.add_argument(
        '--check-updates',
        action='store_true',
        help='Check for available updates'
    )
    
    # Auto-update is now enforced; no CLI flag provided to disable it.

    parser.add_argument(
        '--tips',
        action='store_true',
        help='Show quick CLI tips and exit'
    )

    parser.add_argument(
        '--feedback', 
        action='store_true', 
        help='Capture beta feedback and save it locally'
    )
    
    parser.add_argument(
        '--workflow', 
        action='store_true', 
        help='Start workflow mode for integrated research management'
    )

    parser.add_argument(
        '--import-secrets',
        metavar='PATH',
        help='Import API keys from a .env style file'
    )

    parser.add_argument(
        '--no-plaintext',
        action='store_true',
        help='Fail secret import if keyring is unavailable'
    )
    
    # Workflow integration arguments
    parser.add_argument(
        '--library',
        action='store_true',
        help='List all papers in local library'
    )
    
    parser.add_argument(
        '--export-bibtex',
        action='store_true',
        help='Export library to BibTeX format'
    )
    
    parser.add_argument(
        '--export-markdown',
        action='store_true',
        help='Export library to Markdown format'
    )
    
    parser.add_argument(
        '--history',
        action='store_true',
        help='Show recent query history'
    )
    
    parser.add_argument(
        '--search-library',
        metavar='QUERY',
        help='Search papers in local library'
    )
    
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save query results to library (use with query)'
    )
    
    parser.add_argument(
        '--copy',
        action='store_true',
        help='Copy results to clipboard (use with query)'
    )
    
    parser.add_argument(
        '--format',
        choices=['bibtex', 'apa', 'markdown'],
        help='Export format for citations (use with query)'
    )
    
    parser.add_argument(
        '--tag',
        metavar='TAG',
        help='Filter library by tag'
    )
    
    args = parser.parse_args()
    
    # Handle version
    if args.version:
        print("Cite Agent v1.2.9")
        print("AI Research Assistant with real data integration")
        return

    if args.tips or (args.query and args.query.lower() == "tips" and not args.interactive):
        cli = NocturnalCLI()
        cli.show_tips()
        return

    if args.feedback or (args.query and args.query.lower() == "feedback" and not args.interactive):
        cli = NocturnalCLI()
        exit_code = cli.collect_feedback()
        sys.exit(exit_code)
    
    # Handle workflow commands (no agent initialization needed)
    cli = NocturnalCLI()
    
    if args.library:
        cli.list_library(tag=args.tag)
        sys.exit(0)
    
    if args.export_bibtex:
        cli.export_library_bibtex()
        sys.exit(0)
    
    if args.export_markdown:
        cli.export_library_markdown()
        sys.exit(0)
    
    if args.history:
        cli.show_history(limit=20)
        sys.exit(0)
    
    if args.search_library:
        cli.search_library_interactive(args.search_library)
        sys.exit(0)
    
    # Handle secret import before setup as it can be used non-interactively
    if args.import_secrets:
        config = NocturnalConfig()
        try:
            results = config.import_from_env_file(args.import_secrets, allow_plaintext=not args.no_plaintext)
        except FileNotFoundError as exc:
            print(f"❌ {exc}")
            sys.exit(1)
        if not results:
            print("⚠️ No supported secrets found in the provided file.")
            sys.exit(1)
        overall_success = True
        for key, (status, message) in results.items():
            label = MANAGED_SECRETS.get(key, {}).get('label', key)
            icon = "✅" if status else "⚠️"
            print(f"{icon} {label}: {message}")
            if not status:
                overall_success = False
        sys.exit(0 if overall_success else 1)

    # Handle setup
    if args.setup:
        cli = NocturnalCLI()
        success = cli.setup_wizard()
        sys.exit(0 if success else 1)
    
    # Handle updates
    if args.update or args.check_updates:
        updater = NocturnalUpdater()
        if args.update:
            success = updater.update_package()
            sys.exit(0 if success else 1)
        else:
            updater.show_update_status()
            sys.exit(0)
    
    # Handle query or interactive mode
    async def run_cli():
        cli_instance = NocturnalCLI()
        
        if args.query and not args.interactive:
            # Check if workflow flags are set
            if args.save or args.copy or args.format:
                await cli_instance.single_query_with_workflow(
                    args.query,
                    save_to_library=args.save,
                    copy_to_clipboard=args.copy,
                    export_format=args.format
                )
            else:
                await cli_instance.single_query(args.query)
        else:
            await cli_instance.interactive_mode()
    
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
