#!/usr/bin/env python3
"""
Streaming Chat UI - Cursor/Claude Style Interface
Minimal, clean, conversational interface for data analysis assistant
"""

import sys
import time
import asyncio
from typing import Optional, AsyncGenerator
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner

console = Console()


class StreamingChatUI:
    """
    Clean, minimal chat interface matching Cursor/Claude aesthetics
    - Simple header (just app name)
    - "You:" / "Agent:" conversation labels
    - Streaming character-by-character output
    - Transient action indicators
    - Markdown rendering for rich text
    """
    
    def __init__(self, app_name: str = "Nocturnal Archive", working_dir: Optional[str] = None):
        self.app_name = app_name
        self.working_dir = working_dir
        self.console = Console()
        self.typing_speed = 0.015  # ~60 chars/sec
        
    def show_header(self):
        """Display minimal header on startup"""
        self.console.print(f"\n[bold cyan]{self.app_name}[/bold cyan]")
        if self.working_dir:
            self.console.print(f"[dim]Connected to: {self.working_dir}[/dim]")
        self.console.print("─" * 70)
        self.console.print()
    
    def show_user_message(self, message: str):
        """Display user message with 'You:' prefix"""
        self.console.print(f"[bold]You:[/bold] {message}")
        self.console.print()
    
    async def stream_agent_response(
        self, 
        content_generator: AsyncGenerator[str, None],
        show_markdown: bool = True
    ):
        """
        Stream agent response character-by-character
        
        Args:
            content_generator: Async generator yielding text chunks
            show_markdown: Whether to render as markdown (default True)
        """
        # No prefix for agent - just stream naturally
        buffer = ""
        
        async for chunk in content_generator:
            buffer += chunk
            # Stream character by character for natural feel
            for char in chunk:
                self.console.print(char, end="", style="white")
                await asyncio.sleep(self.typing_speed)
        
        self.console.print()  # Newline after response
        self.console.print()  # Extra space for readability
        
        return buffer
    
    async def stream_markdown_response(self, markdown_text: str):
        """
        Stream a markdown response with proper formatting
        Used for final rendering after streaming is complete
        """
        # Render markdown with Rich
        md = Markdown(markdown_text)
        self.console.print(md)
        self.console.print()
    
    def show_action_indicator(self, action: str) -> Live:
        """
        Show a transient action indicator (e.g., [reading file...])
        Returns Live object that should be stopped when action completes
        
        Usage:
            indicator = ui.show_action_indicator("analyzing data")
            # ... do work ...
            indicator.stop()
        """
        spinner = Spinner("dots", text=f"[dim]{action}[/dim]")
        live = Live(spinner, console=self.console, transient=True)
        live.start()
        return live
    
    def show_error(self, error_message: str):
        """Display error message"""
        self.console.print(f"[red]Error:[/red] {error_message}")
        self.console.print()
    
    def show_info(self, message: str):
        """Display info message"""
        self.console.print(f"[dim]{message}[/dim]")
        self.console.print()
    
    def show_rate_limit_message(
        self, 
        limit_type: str = "Archive API",
        remaining_capabilities: Optional[list] = None
    ):
        """
        Show soft degradation message when rate limited
        
        Args:
            limit_type: What service is limited (e.g., "Archive API")
            remaining_capabilities: List of what's still available
        """
        self.console.print(
            f"\n[yellow]I've reached the daily limit for {limit_type} queries.[/yellow]\n"
        )
        
        if remaining_capabilities:
            self.console.print("[bold]However, I can still assist you with:[/bold]")
            for capability in remaining_capabilities:
                self.console.print(f"  • {capability}")
            self.console.print()
        
        self.console.print(
            "[dim]For unlimited access, consider upgrading to Pro.[/dim]\n"
        )
    
    def get_user_input(self, prompt: str = "You: ") -> str:
        """Get user input with custom prompt"""
        try:
            user_input = self.console.input(f"[bold]{prompt}[/bold]")
            self.console.print()
            return user_input.strip()
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[dim]Goodbye![/dim]")
            sys.exit(0)
    
    def clear_screen(self):
        """Clear terminal screen"""
        self.console.clear()


# Utility functions for streaming from Groq API

async def groq_stream_to_generator(stream) -> AsyncGenerator[str, None]:
    """
    Convert Groq streaming response to async generator
    
    Args:
        stream: Groq stream object from client.chat.completions.create(stream=True)
    
    Yields:
        Text chunks from the stream
    """
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def simulate_streaming(text: str, chunk_size: int = 5) -> AsyncGenerator[str, None]:
    """
    Simulate streaming for testing purposes
    
    Args:
        text: Full text to stream
        chunk_size: Characters per chunk
    
    Yields:
        Text chunks
    """
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        yield chunk
        await asyncio.sleep(0.05)  # Simulate network delay


# Example usage
async def example_usage():
    """Example of how to use the streaming UI"""
    
    ui = StreamingChatUI(
        app_name="Nocturnal Archive",
        working_dir="/home/researcher/project"
    )
    
    # Show header on startup
    ui.show_header()
    
    # Simulate conversation
    ui.show_user_message("hello")
    
    # Simulate streaming response
    response_text = (
        "Good evening. I'm ready to assist with your analysis. "
        "What would you like to work on today?"
    )
    
    async def response_generator():
        async for chunk in simulate_streaming(response_text):
            yield chunk
    
    await ui.stream_agent_response(response_generator())
    
    # Get next user input
    user_input = ui.get_user_input()
    ui.show_user_message(user_input)
    
    # Show action indicator
    indicator = ui.show_action_indicator("reading file")
    await asyncio.sleep(2)  # Simulate work
    indicator.stop()
    
    # Stream another response with markdown
    markdown_response = """
I can see you have several data files here:

• **gdp_data_2020_2024.csv** (245 KB)
• **unemployment_rates.xlsx** (89 KB)

Which dataset would you like me to analyze first?
"""
    
    async def md_generator():
        async for chunk in simulate_streaming(markdown_response):
            yield chunk
    
    await ui.stream_agent_response(md_generator())
    
    # Show rate limit message
    ui.show_rate_limit_message(
        limit_type="Archive API",
        remaining_capabilities=[
            "Local data analysis (unlimited)",
            "Web searches (unlimited)",
            "Financial data (5 queries remaining)",
            "Conversation and file reading"
        ]
    )


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
