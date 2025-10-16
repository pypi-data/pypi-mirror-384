"""
Workflow Integration Module
Reduces context switching for scholars by providing integrated tools
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class WorkflowIntegration:
    """Handles workflow integration features to reduce context switching"""
    
    def __init__(self, data_dir: str = "~/.cite_agent"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize subdirectories
        (self.data_dir / "papers").mkdir(exist_ok=True)
        (self.data_dir / "citations").mkdir(exist_ok=True)
        (self.data_dir / "sessions").mkdir(exist_ok=True)
        
    def save_paper_to_library(self, paper: Dict[str, Any], user_id: str) -> str:
        """Save a paper to user's local library"""
        paper_id = str(uuid.uuid4())
        paper_data = {
            "id": paper_id,
            "user_id": user_id,
            "saved_at": datetime.now().isoformat(),
            "paper": paper,
            "tags": [],
            "notes": ""
        }
        
        # Save to user's paper library
        paper_file = self.data_dir / "papers" / f"{user_id}_{paper_id}.json"
        with open(paper_file, 'w') as f:
            json.dump(paper_data, f, indent=2)
            
        logger.info("Paper saved to library", paper_id=paper_id, user_id=user_id)
        return paper_id
    
    def export_to_bibtex(self, papers: List[Dict[str, Any]], filename: str = None) -> str:
        """Export papers to BibTeX format"""
        if not filename:
            filename = f"citations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bib"
            
        bibtex_file = self.data_dir / "citations" / filename
        
        bibtex_entries = []
        for paper in papers:
            entry = self._format_bibtex_entry(paper)
            bibtex_entries.append(entry)
        
        with open(bibtex_file, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(bibtex_entries))
            
        logger.info("BibTeX exported", filename=filename, count=len(papers))
        return str(bibtex_file)
    
    def _format_bibtex_entry(self, paper: Dict[str, Any]) -> str:
        """Format a paper as BibTeX entry"""
        # Extract key information
        title = paper.get('title', 'Unknown Title')
        authors = paper.get('authors', [])
        year = paper.get('year', '2024')
        venue = paper.get('venue', paper.get('journal', 'Unknown Venue'))
        doi = paper.get('doi', '')
        
        # Generate citation key
        first_author = authors[0].get('name', 'Unknown') if authors else 'Unknown'
        citation_key = f"{first_author.split()[-1].lower()}{year}"
        
        # Format authors
        author_list = " and ".join([author.get('name', 'Unknown') for author in authors])
        
        # Create BibTeX entry
        entry = f"""@article{{{citation_key},
    title = {{{title}}},
    author = {{{author_list}}},
    journal = {{{venue}}},
    year = {{{year}}}"""
        
        if doi:
            entry += f",\n    doi = {{{doi}}}"
            
        entry += "\n}"
        
        return entry
    
    def save_session_history(self, user_id: str, query: str, response: Dict[str, Any]) -> str:
        """Save query and response to session history"""
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "papers_found": len(response.get('papers', [])),
            "tools_used": response.get('tools_used', [])
        }
        
        session_file = self.data_dir / "sessions" / f"{user_id}_{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
            
        logger.info("Session saved", session_id=session_id, user_id=user_id)
        return session_id
    
    def get_user_library(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's saved paper library"""
        library = []
        papers_dir = self.data_dir / "papers"
        
        for paper_file in papers_dir.glob(f"{user_id}_*.json"):
            try:
                with open(paper_file, 'r') as f:
                    paper_data = json.load(f)
                    library.append(paper_data)
            except Exception as e:
                logger.error("Error loading paper", file=paper_file, error=str(e))
                
        # Sort by saved date
        library.sort(key=lambda x: x.get('saved_at', ''), reverse=True)
        return library
    
    def search_library(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Search user's saved paper library"""
        library = self.get_user_library(user_id)
        results = []
        
        query_lower = query.lower()
        for paper_data in library:
            paper = paper_data.get('paper', {})
            
            # Search in title, authors, abstract
            title = paper.get('title', '').lower()
            authors = ' '.join([author.get('name', '') for author in paper.get('authors', [])]).lower()
            abstract = paper.get('abstract', '').lower()
            
            if (query_lower in title or 
                query_lower in authors or 
                query_lower in abstract):
                results.append(paper_data)
                
        return results
    
    def generate_citation_suggestions(self, paper: Dict[str, Any]) -> List[str]:
        """Generate citation suggestions for a paper"""
        suggestions = []
        
        # Suggest related papers based on keywords
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        
        # Extract potential keywords
        keywords = self._extract_keywords(title + ' ' + abstract)
        
        for keyword in keywords[:5]:  # Top 5 keywords
            suggestions.append(f"Find papers related to: {keyword}")
            
        # Suggest citation format options
        suggestions.append("Format citation in APA style")
        suggestions.append("Format citation in MLA style")
        suggestions.append("Format citation in Chicago style")
        
        # Suggest verification
        if paper.get('doi'):
            suggestions.append(f"Verify DOI: {paper['doi']}")
            
        return suggestions
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract potential keywords from text"""
        # Simple keyword extraction (could be enhanced with NLP)
        words = text.lower().split()
        
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
        
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Count frequency and return top keywords
        from collections import Counter
        keyword_counts = Counter(keywords)
        return [word for word, count in keyword_counts.most_common(10)]
    
    def export_to_markdown(self, papers: List[Dict[str, Any]], filename: str = None) -> str:
        """Export papers to Markdown format for Obsidian/Notion"""
        if not filename:
            filename = f"papers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
        markdown_file = self.data_dir / "citations" / filename
        
        markdown_content = "# Research Papers\n\n"
        markdown_content += f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for i, paper in enumerate(papers, 1):
            markdown_content += f"## {i}. {paper.get('title', 'Unknown Title')}\n\n"
            
            # Authors
            authors = paper.get('authors', [])
            if authors:
                author_names = [author.get('name', 'Unknown') for author in authors]
                markdown_content += f"**Authors:** {', '.join(author_names)}\n\n"
            
            # Venue and year
            venue = paper.get('venue', paper.get('journal', 'Unknown Venue'))
            year = paper.get('year', 'Unknown Year')
            markdown_content += f"**Venue:** {venue} ({year})\n\n"
            
            # DOI
            if paper.get('doi'):
                markdown_content += f"**DOI:** {paper['doi']}\n\n"
            
            # Abstract
            if paper.get('abstract'):
                markdown_content += f"**Abstract:** {paper['abstract']}\n\n"
            
            # Citation count
            if paper.get('citation_count'):
                markdown_content += f"**Citations:** {paper['citation_count']}\n\n"
            
            markdown_content += "---\n\n"
        
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        logger.info("Markdown exported", filename=filename, count=len(papers))
        return str(markdown_file)
    
    def get_session_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's recent session history"""
        sessions = []
        sessions_dir = self.data_dir / "sessions"
        
        for session_file in sessions_dir.glob(f"{user_id}_*.json"):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    sessions.append(session_data)
            except Exception as e:
                logger.error("Error loading session", file=session_file, error=str(e))
                
        # Sort by timestamp and limit
        sessions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return sessions[:limit]
    
    def create_citation_network(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a citation network visualization data"""
        network = {
            "nodes": [],
            "edges": []
        }
        
        for paper in papers:
            # Add paper as node
            node = {
                "id": paper.get('id', str(uuid.uuid4())),
                "label": paper.get('title', 'Unknown Title'),
                "year": paper.get('year', 2024),
                "citations": paper.get('citation_count', 0),
                "venue": paper.get('venue', 'Unknown Venue')
            }
            network["nodes"].append(node)
            
            # Add edges based on citations (simplified)
            # In a real implementation, you'd analyze actual citation relationships
            
        return network