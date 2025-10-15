#!/usr/bin/env python3
"""
Web Search Integration for Enhanced AI Agent
Simple wrapper around existing SearchEngine for web browsing capability
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class WebSearchIntegration:
    """
    Lightweight web search integration using DuckDuckGo
    Formats results conversationally for the agent
    """
    
    def __init__(self):
        """Initialize web search - lazy load SearchEngine to avoid import issues"""
        self.search_engine = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Lazy initialization with duckduckgo-search"""
        if not self._initialized:
            try:
                # Use ddgs (duckduckgo search)
                from ddgs import DDGS
                self.search_engine = DDGS()
                self._initialized = True
                logger.info("Web search engine initialized (DuckDuckGo)")
            except Exception as e:
                logger.error(f"Failed to initialize web search: {e}")
                self.search_engine = None
                self._initialized = False
    
    async def search_web(
        self, 
        query: str, 
        num_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search the web using DuckDuckGo
        
        Args:
            query: Search query
            num_results: Number of results to return (1-10)
        
        Returns:
            Dict with 'success', 'results', 'formatted_response'
        """
        await self._ensure_initialized()
        
        if not self.search_engine:
            return {
                "success": False,
                "error": "Web search unavailable",
                "formatted_response": (
                    "I apologize, but web search is temporarily unavailable. "
                    "I can still help with local data analysis, file operations, "
                    "and answering questions based on my knowledge."
                )
            }
        
        try:
            # Use DDGS.text() for web search
            results_list = []
            for result in self.search_engine.text(query, max_results=num_results):
                results_list.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", ""),
                    "source": "DuckDuckGo"
                })
            
            if not results_list:
                return {
                    "success": True,
                    "results": [],
                    "formatted_response": (
                        f"I searched for '{query}' but didn't find relevant results. "
                        "Could you rephrase or provide more specific terms?"
                    )
                }
            
            # Format results conversationally
            formatted = self._format_conversational_results(query, results_list)
            
            return {
                "success": True,
                "results": results_list,
                "formatted_response": formatted,
                "count": len(results_list)
            }
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "formatted_response": (
                    "I encountered an issue while searching the web. "
                    "Let me try to help using other available resources."
                )
            }
    
    def _format_conversational_results(
        self, 
        query: str, 
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Format web search results in a natural, conversational way
        Not as bullet-point list, but as synthesized information
        
        Args:
            query: Original search query
            results: List of search results
        
        Returns:
            Formatted string for natural conversation
        """
        if not results:
            return f"I couldn't find any results for '{query}'."
        
        # Build conversational response
        response_parts = []
        
        # Opening
        response_parts.append(
            f"I found {len(results)} relevant results for '{query}':"
        )
        response_parts.append("")
        
        # Format each result
        for i, result in enumerate(results, 1):
            title = result.get("title", "Untitled")
            url = result.get("url", "")
            snippet = result.get("snippet", "")
            
            # Format naturally
            response_parts.append(f"**{i}. {title}**")
            if snippet:
                response_parts.append(f"   {snippet}")
            if url:
                response_parts.append(f"   Source: {url}")
            response_parts.append("")
        
        return "\n".join(response_parts)
    
    async def close(self):
        """Clean up resources"""
        if self.search_engine:
            try:
                await self.search_engine.close()
            except Exception as e:
                logger.error(f"Error closing search engine: {e}")


# Convenience function for direct usage
async def search_web_simple(query: str, num_results: int = 5) -> str:
    """
    Simple web search that returns formatted string
    
    Args:
        query: Search query
        num_results: Number of results (1-10)
    
    Returns:
        Formatted search results as string
    """
    integration = WebSearchIntegration()
    try:
        result = await integration.search_web(query, num_results)
        return result.get("formatted_response", "No results found.")
    finally:
        await integration.close()


# Example usage
async def example_usage():
    """Example of how to use web search integration"""
    
    integration = WebSearchIntegration()
    
    # Search for something
    result = await integration.search_web("Federal Reserve interest rates 2024", num_results=5)
    
    if result["success"]:
        print("✅ Search successful!")
        print(f"\nFormatted response:\n{result['formatted_response']}")
        print(f"\nRaw results: {len(result.get('results', []))} items")
    else:
        print(f"❌ Search failed: {result.get('error')}")
    
    await integration.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
