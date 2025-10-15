"""
Enhanced CLI with workflow integration features
Reduces context switching for scholars
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
try:
    import structlog
except ImportError:
    import logging
    structlog = logging

from .enhanced_ai_agent import EnhancedNocturnalAgent, ChatRequest
from .workflow_integration import WorkflowIntegration

logger = structlog.getLogger(__name__)

class WorkflowCLI:
    """Enhanced CLI with workflow integration"""
    
    def __init__(self):
        self.agent = None
        self.workflow = WorkflowIntegration()
        self.session_id = f"workflow_{os.getpid()}"
        
    async def initialize(self):
        """Initialize the agent and workflow"""
        self.agent = EnhancedNocturnalAgent()
        await self.agent.initialize()
        
    async def close(self):
        """Clean up resources"""
        if self.agent:
            await self.agent.close()
    
    async def search_and_save(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        """Search papers and save to library"""
        try:
            # Search for papers
            request = ChatRequest(
                question=f"Find academic papers about: {query}",
                user_id=user_id,
                conversation_id=self.session_id
            )
            
            response = await self.agent.process_request(request)
            
            # Extract papers from response
            papers = self._extract_papers_from_response(response)
            
            # Save papers to library
            saved_papers = []
            for paper in papers:
                paper_id = self.workflow.save_paper_to_library(paper, user_id)
                saved_papers.append({
                    "id": paper_id,
                    "title": paper.get("title", "Unknown Title")
                })
            
            # Save session
            session_id = self.workflow.save_session_history(
                user_id, 
                query, 
                {
                    "response": response.response,
                    "papers": papers,
                    "tools_used": response.tools_used
                }
            )
            
            return {
                "success": True,
                "papers_found": len(papers),
                "papers_saved": len(saved_papers),
                "session_id": session_id,
                "saved_papers": saved_papers
            }
            
        except Exception as e:
            logger.error("Error in search_and_save", error=str(e))
            return {"success": False, "error": str(e)}
    
    def _extract_papers_from_response(self, response) -> List[Dict[str, Any]]:
        """Extract paper data from agent response"""
        papers = []
        
        # Try to extract from execution_results
        if hasattr(response, 'execution_results') and response.execution_results:
            for result in response.execution_results.values():
                if isinstance(result, dict) and 'papers' in result:
                    papers.extend(result['papers'])
        
        # Try to extract from api_results
        if hasattr(response, 'api_results') and response.api_results:
            for result in response.api_results.values():
                if isinstance(result, dict) and 'papers' in result:
                    papers.extend(result['papers'])
        
        return papers
    
    async def export_library(self, user_id: str, format: str = "bibtex") -> str:
        """Export user's library in specified format"""
        try:
            library = self.workflow.get_user_library(user_id)
            papers = [paper_data.get('paper', {}) for paper_data in library]
            
            if format == "bibtex":
                filename = f"library_{user_id}.bib"
                file_path = self.workflow.export_to_bibtex(papers, filename)
            elif format == "markdown":
                filename = f"library_{user_id}.md"
                file_path = self.workflow.export_to_markdown(papers, filename)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return file_path
            
        except Exception as e:
            logger.error("Error exporting library", error=str(e))
            raise
    
    def search_library(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Search user's saved library"""
        return self.workflow.search_library(user_id, query)
    
    def get_library_stats(self, user_id: str) -> Dict[str, Any]:
        """Get library statistics"""
        library = self.workflow.get_user_library(user_id)
        sessions = self.workflow.get_session_history(user_id, 100)
        
        # Calculate stats
        total_papers = len(library)
        
        # Papers by year
        papers_by_year = {}
        for paper_data in library:
            paper = paper_data.get('paper', {})
            year = paper.get('year', 'Unknown')
            papers_by_year[year] = papers_by_year.get(year, 0) + 1
        
        # Most used tools
        tools_used = {}
        for session in sessions:
            for tool in session.get('tools_used', []):
                tools_used[tool] = tools_used.get(tool, 0) + 1
        
        return {
            "total_papers": total_papers,
            "total_sessions": len(sessions),
            "papers_by_year": papers_by_year,
            "most_used_tools": dict(sorted(tools_used.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    async def get_citation_suggestions(self, paper: Dict[str, Any]) -> List[str]:
        """Get citation suggestions for a paper"""
        return self.workflow.generate_citation_suggestions(paper)
    
    def get_session_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent session history"""
        return self.workflow.get_session_history(user_id, limit)
    
    async def interactive_workflow(self, user_id: str = "default"):
        """Interactive workflow mode"""
        print("🔬 Cite-Agent Workflow Mode")
        print("=" * 50)
        print("Commands:")
        print("  search <query>     - Search and save papers")
        print("  library            - Show saved papers")
        print("  export <format>    - Export library (bibtex/markdown)")
        print("  stats              - Show library statistics")
        print("  history            - Show recent searches")
        print("  suggest <title>    - Get citation suggestions")
        print("  quit               - Exit workflow mode")
        print()
        
        while True:
            try:
                command = input("workflow> ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    break
                elif command.startswith('search '):
                    query = command[7:].strip()
                    if query:
                        result = await self.search_and_save(query, user_id)
                        if result['success']:
                            print(f"✅ Found {result['papers_found']} papers, saved {result['papers_saved']}")
                        else:
                            print(f"❌ Error: {result.get('error', 'Unknown error')}")
                    else:
                        print("❌ Please provide a search query")
                
                elif command == 'library':
                    library = self.workflow.get_user_library(user_id)
                    if library:
                        print(f"📚 Library ({len(library)} papers):")
                        for i, paper_data in enumerate(library[:10], 1):
                            paper = paper_data.get('paper', {})
                            title = paper.get('title', 'Unknown Title')[:60]
                            year = paper.get('year', 'Unknown')
                            print(f"  {i}. {title}... ({year})")
                        if len(library) > 10:
                            print(f"  ... and {len(library) - 10} more")
                    else:
                        print("📚 Library is empty")
                
                elif command.startswith('export '):
                    format = command[7:].strip().lower()
                    if format in ['bibtex', 'markdown']:
                        try:
                            file_path = await self.export_library(user_id, format)
                            print(f"✅ Exported to: {file_path}")
                        except Exception as e:
                            print(f"❌ Export error: {e}")
                    else:
                        print("❌ Supported formats: bibtex, markdown")
                
                elif command == 'stats':
                    stats = self.get_library_stats(user_id)
                    print("📊 Library Statistics:")
                    print(f"  Total papers: {stats['total_papers']}")
                    print(f"  Total sessions: {stats['total_sessions']}")
                    print("  Papers by year:")
                    for year, count in sorted(stats['papers_by_year'].items()):
                        print(f"    {year}: {count}")
                    print("  Most used tools:")
                    for tool, count in stats['most_used_tools'].items():
                        print(f"    {tool}: {count}")
                
                elif command == 'history':
                    history = self.get_session_history(user_id, 5)
                    if history:
                        print("🕒 Recent Searches:")
                        for i, session in enumerate(history, 1):
                            query = session.get('query', 'Unknown')[:50]
                            timestamp = session.get('timestamp', 'Unknown')[:19]
                            papers = session.get('papers_found', 0)
                            print(f"  {i}. {query}... ({papers} papers) - {timestamp}")
                    else:
                        print("🕒 No search history")
                
                elif command.startswith('suggest '):
                    title = command[8:].strip()
                    if title:
                        # Find paper in library
                        library = self.workflow.get_user_library(user_id)
                        paper = None
                        for paper_data in library:
                            if title.lower() in paper_data.get('paper', {}).get('title', '').lower():
                                paper = paper_data.get('paper', {})
                                break
                        
                        if paper:
                            suggestions = await self.get_citation_suggestions(paper)
                            print(f"💡 Suggestions for '{paper.get('title', 'Unknown')}':")
                            for suggestion in suggestions:
                                print(f"  • {suggestion}")
                        else:
                            print(f"❌ Paper not found in library: {title}")
                    else:
                        print("❌ Please provide a paper title")
                
                else:
                    print("❌ Unknown command. Type 'quit' to exit.")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("👋 Workflow mode ended")