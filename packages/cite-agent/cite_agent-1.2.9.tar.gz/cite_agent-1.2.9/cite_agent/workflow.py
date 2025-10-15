#!/usr/bin/env python3
"""
Workflow Integration Module - Reduces context switching for scholars
Features:
- BibTeX export for citation managers
- Local paper library management
- Clipboard integration
- Markdown export for note-taking apps
- Session history and replay
"""

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class Paper:
    """Represents an academic paper"""
    title: str
    authors: List[str]
    year: int
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    venue: Optional[str] = None
    citation_count: int = 0
    paper_id: Optional[str] = None
    added_date: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.added_date is None:
            self.added_date = datetime.now().isoformat()

    def to_bibtex(self, citation_key: Optional[str] = None) -> str:
        """Convert paper to BibTeX format"""
        if not citation_key:
            # Generate citation key: FirstAuthorYearTitleWord
            first_author = self.authors[0].split()[-1] if self.authors else "Unknown"
            title_word = self.title.split()[0] if self.title else "Paper"
            citation_key = f"{first_author}{self.year}{title_word}".replace(" ", "")
        
        bibtex = f"@article{{{citation_key},\n"
        bibtex += f"  title = {{{self.title}}},\n"
        
        if self.authors:
            authors_str = " and ".join(self.authors)
            bibtex += f"  author = {{{authors_str}}},\n"
        
        bibtex += f"  year = {{{self.year}}},\n"
        
        if self.venue:
            bibtex += f"  journal = {{{self.venue}}},\n"
        
        if self.doi:
            bibtex += f"  doi = {{{self.doi}}},\n"
        
        if self.url:
            bibtex += f"  url = {{{self.url}}},\n"
        
        if self.abstract:
            # Clean abstract for BibTeX
            clean_abstract = self.abstract.replace("\n", " ").replace("{", "").replace("}", "")
            bibtex += f"  abstract = {{{clean_abstract}}},\n"
        
        bibtex += "}\n"
        return bibtex

    def to_apa_citation(self) -> str:
        """Convert paper to APA format citation"""
        authors_part = ""
        if len(self.authors) == 1:
            authors_part = self.authors[0]
        elif len(self.authors) == 2:
            authors_part = f"{self.authors[0]} & {self.authors[1]}"
        elif len(self.authors) > 2:
            authors_part = f"{self.authors[0]} et al."
        
        citation = f"{authors_part} ({self.year}). {self.title}."
        
        if self.venue:
            citation += f" {self.venue}."
        
        if self.doi:
            citation += f" https://doi.org/{self.doi}"
        elif self.url:
            citation += f" {self.url}"
        
        return citation

    def to_markdown(self) -> str:
        """Convert paper to markdown format"""
        md = f"# {self.title}\n\n"
        
        if self.authors:
            md += f"**Authors:** {', '.join(self.authors)}\n\n"
        
        md += f"**Year:** {self.year}\n\n"
        
        if self.venue:
            md += f"**Venue:** {self.venue}\n\n"
        
        if self.citation_count:
            md += f"**Citations:** {self.citation_count}\n\n"
        
        if self.doi:
            md += f"**DOI:** [{self.doi}](https://doi.org/{self.doi})\n\n"
        elif self.url:
            md += f"**URL:** {self.url}\n\n"
        
        if self.abstract:
            md += f"## Abstract\n\n{self.abstract}\n\n"
        
        if self.notes:
            md += f"## Notes\n\n{self.notes}\n\n"
        
        if self.tags:
            md += f"**Tags:** {', '.join(self.tags)}\n\n"
        
        md += f"*Added: {self.added_date}*\n"
        
        return md


class WorkflowManager:
    """Manages scholar workflow integrations"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".cite_agent"
        self.library_dir = self.config_dir / "library"
        self.exports_dir = self.config_dir / "exports"
        self.history_dir = self.config_dir / "history"
        self.bibtex_file = self.exports_dir / "references.bib"
        
        # Create directories
        self.config_dir.mkdir(exist_ok=True)
        self.library_dir.mkdir(exist_ok=True)
        self.exports_dir.mkdir(exist_ok=True)
        self.history_dir.mkdir(exist_ok=True)
    
    def add_paper(self, paper: Paper) -> bool:
        """Add paper to local library"""
        try:
            # Generate paper ID if not provided
            if not paper.paper_id:
                paper.paper_id = self._generate_paper_id(paper)
            
            # Save paper as JSON
            paper_file = self.library_dir / f"{paper.paper_id}.json"
            with open(paper_file, 'w') as f:
                json.dump(asdict(paper), f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error adding paper: {e}")
            return False
    
    def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Retrieve paper from library"""
        try:
            paper_file = self.library_dir / f"{paper_id}.json"
            if not paper_file.exists():
                return None
            
            with open(paper_file, 'r') as f:
                data = json.load(f)
                return Paper(**data)
        except Exception as e:
            print(f"Error retrieving paper: {e}")
            return None
    
    def list_papers(self, tag: Optional[str] = None) -> List[Paper]:
        """List all papers in library, optionally filtered by tag"""
        papers = []
        for paper_file in self.library_dir.glob("*.json"):
            try:
                with open(paper_file, 'r') as f:
                    data = json.load(f)
                    paper = Paper(**data)
                    
                    if tag is None or tag in paper.tags:
                        papers.append(paper)
            except Exception as e:
                print(f"Error reading {paper_file}: {e}")
        
        # Sort by added date (newest first)
        papers.sort(key=lambda p: p.added_date or "", reverse=True)
        return papers
    
    def export_to_bibtex(self, papers: Optional[List[Paper]] = None, append: bool = True) -> bool:
        """Export papers to BibTeX file"""
        try:
            if papers is None:
                # Export all papers from library
                papers = self.list_papers()
            
            mode = 'a' if append else 'w'
            with open(self.bibtex_file, mode) as f:
                if not append:
                    f.write("% Generated by Cite-Agent\n")
                    f.write(f"% Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for paper in papers:
                    f.write(paper.to_bibtex())
                    f.write("\n")
            
            return True
        except Exception as e:
            print(f"Error exporting to BibTeX: {e}")
            return False
    
    def export_to_markdown(self, papers: Optional[List[Paper]] = None, output_file: Optional[Path] = None) -> bool:
        """Export papers to markdown file"""
        try:
            if papers is None:
                papers = self.list_papers()
            
            if output_file is None:
                output_file = self.exports_dir / f"papers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            with open(output_file, 'w') as f:
                f.write(f"# Research Library Export\n\n")
                f.write(f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                f.write(f"Total papers: {len(papers)}\n\n")
                f.write("---\n\n")
                
                for i, paper in enumerate(papers, 1):
                    f.write(f"## {i}. {paper.title}\n\n")
                    f.write(paper.to_markdown())
                    f.write("\n---\n\n")
            
            return True
        except Exception as e:
            print(f"Error exporting to markdown: {e}")
            return False
    
    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to system clipboard"""
        try:
            # Try multiple clipboard commands based on platform
            commands = [
                ['xclip', '-selection', 'clipboard'],  # Linux X11
                ['xsel', '--clipboard', '--input'],     # Linux alternative
                ['wl-copy'],                             # Linux Wayland
                ['pbcopy'],                              # macOS
                ['clip'],                                # Windows
            ]
            
            for cmd in commands:
                try:
                    subprocess.run(
                        cmd,
                        input=text.encode('utf-8'),
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return True
                except (FileNotFoundError, subprocess.CalledProcessError):
                    continue
            
            # If all commands fail, save to temp file as fallback
            temp_file = self.config_dir / "clipboard.txt"
            with open(temp_file, 'w') as f:
                f.write(text)
            print(f"⚠️  Clipboard unavailable. Saved to: {temp_file}")
            return False
            
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            return False
    
    def save_query_result(self, query: str, response: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Save query and response to history"""
        try:
            timestamp = datetime.now()
            history_file = self.history_dir / f"{timestamp.strftime('%Y%m%d')}.jsonl"
            
            entry = {
                "timestamp": timestamp.isoformat(),
                "query": query,
                "response": response,
                "metadata": metadata or {}
            }
            
            with open(history_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
            
            return True
        except Exception as e:
            print(f"Error saving query result: {e}")
            return False
    
    def get_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Retrieve query history from last N days"""
        history = []
        cutoff = datetime.now()
        
        for history_file in sorted(self.history_dir.glob("*.jsonl"), reverse=True):
            try:
                with open(history_file, 'r') as f:
                    for line in f:
                        entry = json.loads(line)
                        history.append(entry)
            except Exception as e:
                print(f"Error reading history: {e}")
        
        return history[:100]  # Limit to last 100 queries
    
    def search_library(self, query: str) -> List[Paper]:
        """Search papers in library by title, author, or abstract"""
        query_lower = query.lower()
        results = []
        
        for paper in self.list_papers():
            # Search in title
            if query_lower in paper.title.lower():
                results.append(paper)
                continue
            
            # Search in authors
            if any(query_lower in author.lower() for author in paper.authors):
                results.append(paper)
                continue
            
            # Search in abstract
            if paper.abstract and query_lower in paper.abstract.lower():
                results.append(paper)
                continue
        
        return results
    
    def add_note_to_paper(self, paper_id: str, note: str) -> bool:
        """Add note to a paper in the library"""
        paper = self.get_paper(paper_id)
        if not paper:
            return False
        
        if paper.notes:
            paper.notes += f"\n\n{note}"
        else:
            paper.notes = note
        
        return self.add_paper(paper)
    
    def tag_paper(self, paper_id: str, tags: List[str]) -> bool:
        """Add tags to a paper"""
        paper = self.get_paper(paper_id)
        if not paper:
            return False
        
        paper.tags = list(set(paper.tags + tags))
        return self.add_paper(paper)
    
    def _generate_paper_id(self, paper: Paper) -> str:
        """Generate unique paper ID"""
        # Use DOI if available
        if paper.doi:
            return paper.doi.replace('/', '_').replace('.', '_')
        
        # Otherwise use hash of title + first author + year
        content = f"{paper.title}{paper.authors[0] if paper.authors else ''}{paper.year}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]


def parse_paper_from_response(response_text: str) -> Optional[Paper]:
    """
    Extract paper information from agent response text
    This is a helper to convert agent responses into Paper objects
    """
    # This is a simple parser - could be enhanced with more sophisticated NLP
    try:
        # Try to extract common patterns
        title_match = re.search(r'(?:title|Title):\s*["\']?([^"\'\n]+)["\']?', response_text)
        authors_match = re.search(r'(?:author|Author)s?:\s*(.+?)(?:\n|Year)', response_text, re.IGNORECASE)
        year_match = re.search(r'(?:year|Year):\s*(\d{4})', response_text)
        doi_match = re.search(r'(?:doi|DOI):\s*(10\.\d+/[^\s\n]+)', response_text)
        
        if not title_match:
            return None
        
        title = title_match.group(1).strip()
        
        authors = []
        if authors_match:
            author_text = authors_match.group(1)
            # Split by common delimiters
            authors = [a.strip() for a in re.split(r'[,&]|\sand\s', author_text)]
        
        year = int(year_match.group(1)) if year_match else datetime.now().year
        doi = doi_match.group(1) if doi_match else None
        
        return Paper(
            title=title,
            authors=authors,
            year=year,
            doi=doi
        )
    except Exception as e:
        print(f"Error parsing paper: {e}")
        return None


# Convenience function for quick exports
def quick_export_bibtex(paper_data: Dict[str, Any]) -> str:
    """Quick convert dict to BibTeX format"""
    paper = Paper(
        title=paper_data.get('title', ''),
        authors=paper_data.get('authors', []),
        year=paper_data.get('year', datetime.now().year),
        doi=paper_data.get('doi'),
        url=paper_data.get('url'),
        venue=paper_data.get('venue'),
        abstract=paper_data.get('abstract')
    )
    return paper.to_bibtex()

