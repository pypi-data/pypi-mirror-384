#!/usr/bin/env python3
"""
Nocturnal Archive - Conversational Data Analysis Assistant
Main CLI with streaming UI, Jarvis personality, and full capabilities
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Add nocturnal_archive to path
sys.path.insert(0, str(Path(__file__).parent))

from streaming_ui import StreamingChatUI, simulate_streaming
from web_search import WebSearchIntegration
from enhanced_ai_agent import EnhancedNocturnalAgent


class NocturnalArchiveCLI:
    """
    Main CLI orchestrator bringing together:
    - Streaming chat UI (Cursor/Claude style)
    - Enhanced AI agent (with APIs)
    - Web search capability
    - Jarvis-like professional personality
    """
    
    def __init__(self):
        self.ui = None
        self.agent = None
        self.web_search = None
        self.working_dir = os.getcwd()
        self.conversation_active = True
        
    async def initialize(self):
        """Initialize all components"""
        # Initialize UI
        self.ui = StreamingChatUI(
            app_name="Nocturnal Archive",
            working_dir=self.working_dir
        )
        
        # Initialize agent
        self.agent = EnhancedNocturnalAgent()
        await self.agent.initialize()
        
        # Initialize web search
        self.web_search = WebSearchIntegration()
        
        # Update agent personality to Jarvis-like professional tone
        await self._configure_jarvis_personality()
    
    async def _configure_jarvis_personality(self):
        """Configure the agent with Jarvis-like professional personality"""
        # This will update the system prompts in the agent
        # The agent already has conversation memory, we just adjust tone
        
        jarvis_system_prompt = """You are a professional research and data analysis assistant with a refined, helpful demeanor similar to Jarvis from Iron Man.

Your communication style:
- Professional and intelligent, never casual or overly friendly
- Verbose when explaining complex topics, but always clear
- Use complete sentences and proper grammar
- Greet users formally: "Good evening" / "Good morning" (based on time)
- Ask clarifying questions when needed
- Acknowledge tasks before executing: "Understood. Let me..." or "Certainly, I'll..."
- Show intermediate progress: "I can see..." / "The data indicates..."
- Offer next steps conversationally: "Would you like me to..."

Your capabilities:
- Analyze local data files (CSV, Excel, Stata, etc.)
- Run statistical tests and data transformations
- Search academic papers (Archive API)
- Fetch financial data (FinSight API)
- Browse the web for current information
- Execute shell commands safely
- Generate visualizations

Primary role: You're a DATA ANALYSIS assistant first, research assistant second.
- When users mention data files, offer to analyze them
- Proactively suggest relevant statistical tests
- Explain results in context, not just numbers
- Synthesize information naturally, avoid bullet-point lists unless specifically listing items

Remember:
- Never invent data or citations
- Be honest about limitations
- Offer alternatives when rate-limited
- Maintain conversation flow naturally
"""
        
        # Store this for when we make requests
        self.jarvis_prompt = jarvis_system_prompt
    
    async def run(self):
        """Main conversation loop"""
        try:
            # Show welcome
            self.ui.show_header()
            
            # Jarvis-style greeting based on time of day
            from datetime import datetime
            hour = datetime.now().hour
            if hour < 12:
                greeting = "Good morning."
            elif hour < 18:
                greeting = "Good afternoon."
            else:
                greeting = "Good evening."
            
            welcome_message = (
                f"{greeting} I'm ready to assist with your analysis. "
                "What would you like to work on today?"
            )
            
            # Stream the welcome message
            async def welcome_gen():
                async for chunk in simulate_streaming(welcome_message, chunk_size=3):
                    yield chunk
            
            await self.ui.stream_agent_response(welcome_gen())
            
            # Main conversation loop
            while self.conversation_active:
                try:
                    # Get user input
                    user_input = self.ui.get_user_input()
                    
                    if not user_input:
                        continue
                    
                    # Check for exit commands
                    if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                        farewell = "Goodbye. Feel free to return whenever you need assistance."
                        async def farewell_gen():
                            async for chunk in simulate_streaming(farewell, chunk_size=3):
                                yield chunk
                        await self.ui.stream_agent_response(farewell_gen())
                        break
                    
                    # Process the request
                    await self._process_user_request(user_input)
                    
                except KeyboardInterrupt:
                    self.ui.show_info("\nInterrupted. Goodbye.")
                    break
                except Exception as e:
                    self.ui.show_error(f"An error occurred: {str(e)}")
                    continue
        
        finally:
            await self.cleanup()
    
    async def _process_user_request(self, user_input: str):
        """
        Process user request with full capabilities:
        - Detect intent (data analysis, web search, research, etc.)
        - Use appropriate tools
        - Stream response naturally
        """
        
        # Determine if this is a web search request
        is_web_search = any(keyword in user_input.lower() for keyword in [
            'google', 'search for', 'browse', 'look up', 'find on the web',
            'what does', 'who is', 'recent news'
        ])
        
        # Determine if this is a data analysis request
        is_data_analysis = any(keyword in user_input.lower() for keyword in [
            'analyze', 'data', 'csv', 'plot', 'graph', 'test', 'regression',
            'correlation', 'statistics', 'mean', 'median', 'distribution'
        ])
        
        # For now, let's handle web search directly as an example
        if is_web_search and 'google' in user_input.lower():
            # Extract search query
            query = user_input.lower().replace('google', '').replace('search for', '').strip()
            
            # Show indicator
            indicator = self.ui.show_action_indicator(f"browsing web for '{query}'")
            
            try:
                # Perform web search
                result = await self.web_search.search_web(query, num_results=5)
                indicator.stop()
                
                # Stream the response
                response_text = result.get('formatted_response', 'No results found.')
                async def response_gen():
                    async for chunk in simulate_streaming(response_text, chunk_size=4):
                        yield chunk
                
                await self.ui.stream_agent_response(response_gen())
                
            except Exception as e:
                indicator.stop()
                self.ui.show_error(f"Web search failed: {str(e)}")
        
        else:
            # For other requests, use the enhanced agent
            indicator = self.ui.show_action_indicator("processing your request")
            
            try:
                # Call the agent with REAL Groq streaming
                from enhanced_ai_agent import ChatRequest
                from streaming_ui import groq_stream_to_generator
                
                request = ChatRequest(
                    question=user_input,
                    user_id="cli_user",
                    conversation_id="main_session"
                )
                
                # Get streaming response from agent
                try:
                    # Check if agent has streaming support
                    if hasattr(self.agent, 'process_request_streaming'):
                        # Use real streaming
                        stream = await self.agent.process_request_streaming(request)
                        indicator.stop()
                        await self.ui.stream_agent_response(groq_stream_to_generator(stream))
                    else:
                        # Fallback to non-streaming
                        response = await self.agent.process_request(request)
                        indicator.stop()
                        
                        # Check for rate limiting
                        if response.error_message and 'limit' in response.error_message.lower():
                            self.ui.show_rate_limit_message(
                                limit_type="API queries",
                                remaining_capabilities=[
                                    "Local data analysis (unlimited)",
                                    "Web searches (unlimited)",
                                    "General conversation",
                                    "File operations"
                                ]
                            )
                        
                        # Stream the response (simulated for now)
                        response_text = response.response
                        async def response_gen():
                            for char in response_text:
                                yield char
                        
                        await self.ui.stream_agent_response(response_gen())
                        
                except Exception as e:
                    indicator.stop()
                    self.ui.show_error(f"Error: {str(e)}")
                
            except Exception as e:
                indicator.stop()
                self.ui.show_error(f"Request processing failed: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.agent:
            await self.agent.close()
        if self.web_search:
            await self.web_search.close()


async def main():
    """Main entry point"""
    cli = NocturnalArchiveCLI()
    
    try:
        await cli.initialize()
        await cli.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await cli.cleanup()


if __name__ == "__main__":
    # Check dependencies
    try:
        import rich
        import groq
        import aiohttp
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install requirements: pip install -r requirements.txt")
        sys.exit(1)
    
    # Run the CLI
    asyncio.run(main())
