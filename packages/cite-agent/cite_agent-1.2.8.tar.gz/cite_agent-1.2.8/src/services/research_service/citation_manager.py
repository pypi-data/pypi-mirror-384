"""
Citation management system for tracking sources and generating proper citations.
Supports multiple citation formats and automatic reference management.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from urllib.parse import urlparse
import json
from enum import Enum

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

class CitationFormat(Enum):
    """Supported citation formats."""
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    IEEE = "ieee"

@dataclass
class CitedFinding:
    """Represents a finding with its associated citations."""
    finding_id: str
    content: str
    citations: List[str]  # List of citation IDs
    relevance_score: float
    category: str
    timestamp: datetime

@dataclass
class Citation:
    """Represents a citation with metadata."""
    id: str
    url: str
    title: str
    authors: List[str]
    publication_date: Optional[str]
    access_date: str
    source_type: str  # 'web', 'journal', 'book', 'conference'
    doi: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    publisher: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = None
    citation_count: Optional[int] = None
    relevance_score: float = 0.0

@dataclass
class CachedItem:
    """Represents a cached item with expiration."""
    data: Any
    created_at: datetime
    expires_at: Optional[datetime]

class CitationManager:
    """Manages citations and generates proper reference formats."""
    
    def __init__(self, db_ops=None, openalex_client=None):
        self.citations: Dict[str, Citation] = {}
        self.citation_counter = 0
        self.db_ops = db_ops
        self.openalex_client = openalex_client
        
    def add_citation(self, url: str, title: str, content: str, metadata: Dict[str, Any]) -> str:
        """Add a new citation and return its ID."""
        citation_id = f"ref_{self.citation_counter + 1:03d}"
        self.citation_counter += 1
        
        # Extract authors from metadata or content
        authors = self._extract_authors(metadata, content)
        
        # Determine source type
        source_type = self._determine_source_type(url, metadata)
        
        # Extract publication date
        pub_date = self._extract_publication_date(metadata, content)
        
        # Calculate relevance score
        relevance_score = self._calculate_relevance_score(content, metadata)
        
        citation = Citation(
            id=citation_id,
            url=url,
            title=title,
            authors=authors,
            publication_date=pub_date,
            access_date=_utc_now().strftime("%Y-%m-%d"),
            source_type=source_type,
            doi=metadata.get('doi'),
            journal=metadata.get('journal'),
            volume=metadata.get('volume'),
            issue=metadata.get('issue'),
            pages=metadata.get('pages'),
            publisher=metadata.get('publisher'),
            abstract=metadata.get('abstract'),
            keywords=metadata.get('keywords', []),
            citation_count=metadata.get('citation_count'),
            relevance_score=relevance_score
        )
        
        self.citations[citation_id] = citation
        logger.info(f"Added citation {citation_id}: {title}")
        
        return citation_id
    
    def get_citation(self, citation_id: str) -> Optional[Citation]:
        """Get a citation by ID."""
        return self.citations.get(citation_id)
    
    def get_all_citations(self) -> List[Citation]:
        """Get all citations sorted by relevance."""
        return sorted(self.citations.values(), key=lambda x: x.relevance_score, reverse=True)
    
    def generate_citation_text(self, citation_id: str, format: str = "apa") -> str:
        """Generate citation text in specified format."""
        citation = self.get_citation(citation_id)
        if not citation:
            return f"[Citation {citation_id} not found]"
        
        if format.lower() == "apa":
            return self._generate_apa_citation(citation)
        elif format.lower() == "mla":
            return self._generate_mla_citation(citation)
        elif format.lower() == "chicago":
            return self._generate_chicago_citation(citation)
        elif format.lower() == "ieee":
            return self._generate_ieee_citation(citation)
        else:
            return self._generate_apa_citation(citation)
    
    def generate_reference_list(self, format: str = "apa") -> str:
        """Generate a complete reference list."""
        citations = self.get_all_citations()
        
        if format.lower() == "apa":
            return self._generate_apa_reference_list(citations)
        elif format.lower() == "mla":
            return self._generate_mla_reference_list(citations)
        elif format.lower() == "chicago":
            return self._generate_chicago_reference_list(citations)
        elif format.lower() == "ieee":
            return self._generate_ieee_reference_list(citations)
        else:
            return self._generate_apa_reference_list(citations)
    
    def generate_inline_citations(self, text: str, format: str = "apa") -> str:
        """Add inline citations to text."""
        # Find citation markers like [ref_001] and replace with proper citations
        pattern = r'\[(ref_\d+)\]'
        
        def replace_citation(match):
            citation_id = match.group(1)
            citation = self.get_citation(citation_id)
            if citation:
                if format.lower() == "apa":
                    return f"({citation.authors[0] if citation.authors else 'Unknown'}, {citation.publication_date or 'n.d.'})"
                elif format.lower() == "mla":
                    return f"({citation.authors[0] if citation.authors else 'Unknown'} {citation.publication_date or 'n.d.'})"
                else:
                    return f"[{citation_id}]"
            return match.group(0)
        
        return re.sub(pattern, replace_citation, text)
    
    def export_citations(self, format: str = "json") -> str:
        """Export citations in various formats."""
        if format.lower() == "json":
            return json.dumps([self._citation_to_dict(c) for c in self.citations.values()], indent=2)
        elif format.lower() == "bibtex":
            return self._generate_bibtex_export()
        elif format.lower() == "ris":
            return self._generate_ris_export()
        else:
            return json.dumps([self._citation_to_dict(c) for c in self.citations.values()], indent=2)
    
    def _extract_authors(self, metadata: Dict[str, Any], content: str) -> List[str]:
        """Extract authors from metadata or content."""
        authors = []
        
        # Try metadata first
        if 'author' in metadata:
            if isinstance(metadata['author'], list):
                authors = metadata['author']
            else:
                authors = [metadata['author']]
        
        # Try Open Graph authors
        if 'og:author' in metadata:
            authors.append(metadata['og:author'])
        
        # Try to extract from content if no authors found
        if not authors:
            # Look for common author patterns
            author_patterns = [
                r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'Author[s]?:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'Written by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            ]
            
            for pattern in author_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    authors.extend(matches[:3])  # Limit to 3 authors
                    break
        
        return authors[:5]  # Limit to 5 authors
    
    def _determine_source_type(self, url: str, metadata: Dict[str, Any]) -> str:
        """Determine the type of source."""
        domain = urlparse(url).netloc.lower()
        
        # Academic domains
        academic_domains = ['arxiv.org', 'scholar.google.com', 'researchgate.net', 'academia.edu', 
                           'jstor.org', 'sciencedirect.com', 'ieee.org', 'acm.org']
        
        if any(domain in url for domain in academic_domains):
            return 'journal'
        
        # Conference domains
        conference_domains = ['conference', 'proceedings', 'workshop']
        if any(term in url for term in conference_domains):
            return 'conference'
        
        # Book domains
        book_domains = ['amazon.com', 'goodreads.com', 'books.google.com']
        if any(domain in url for domain in book_domains):
            return 'book'
        
        return 'web'
    
    def _extract_publication_date(self, metadata: Dict[str, Any], content: str) -> Optional[str]:
        """Extract publication date from metadata or content."""
        # Try metadata first
        date_fields = ['date', 'pubdate', 'publication_date', 'published', 'og:published_time']
        for field in date_fields:
            if field in metadata:
                return metadata[field]
        
        # Try to extract from content
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\w+\s+\d{1,2},?\s+\d{4})',
            r'(\d{4})'  # Just year
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            if matches:
                return matches[0]
        
        return None
    
    def _calculate_relevance_score(self, content: str, metadata: Dict[str, Any]) -> float:
        """Calculate relevance score based on content quality and metadata."""
        score = 0.0
        
        # Content length (longer content is generally better)
        score += min(len(content) / 1000, 2.0)
        
        # Has authors
        if metadata.get('author'):
            score += 1.0
        
        # Has publication date
        if metadata.get('date') or metadata.get('publication_date'):
            score += 1.0
        
        # Has DOI (academic indicator)
        if metadata.get('doi'):
            score += 2.0
        
        # Has abstract
        if metadata.get('abstract'):
            score += 1.0
        
        # Source type bonus
        source_type = self._determine_source_type(metadata.get('url', ''), metadata)
        if source_type == 'journal':
            score += 2.0
        elif source_type == 'conference':
            score += 1.5
        elif source_type == 'book':
            score += 1.0
        
        return score
    
    def _generate_apa_citation(self, citation: Citation) -> str:
        """Generate APA format citation."""
        if citation.authors:
            authors = ', '.join(citation.authors)
        else:
            authors = 'Unknown'
        
        year = citation.publication_date[:4] if citation.publication_date else 'n.d.'
        
        if citation.source_type == 'journal':
            return f"{authors} ({year}). {citation.title}. {citation.journal or 'Journal'}, {citation.volume or ''}{f'({citation.issue})' if citation.issue else ''}{f', {citation.pages}' if citation.pages else ''}."
        else:
            return f"{authors} ({year}). {citation.title}. Retrieved {citation.access_date} from {citation.url}"
    
    def _generate_mla_citation(self, citation: Citation) -> str:
        """Generate MLA format citation."""
        if citation.authors:
            authors = ', '.join(citation.authors)
        else:
            authors = 'Unknown'
        
        year = citation.publication_date[:4] if citation.publication_date else 'n.d.'
        
        return f'"{citation.title}." {citation.publisher or "Web"}, {year}, {citation.url}. Accessed {citation.access_date}.'
    
    def _generate_chicago_citation(self, citation: Citation) -> str:
        """Generate Chicago format citation."""
        if citation.authors:
            authors = ', '.join(citation.authors)
        else:
            authors = 'Unknown'
        
        year = citation.publication_date[:4] if citation.publication_date else 'n.d.'
        
        return f"{authors}. \"{citation.title}.\" {citation.publisher or 'Web'}, {year}. {citation.url}."
    
    def _generate_ieee_citation(self, citation: Citation) -> str:
        """Generate IEEE format citation."""
        if citation.authors:
            authors = ', '.join(citation.authors)
        else:
            authors = 'Unknown'
        
        year = citation.publication_date[:4] if citation.publication_date else 'n.d.'
        
        return f"{authors}, \"{citation.title},\" {citation.publisher or 'Web'}, {year}. [Online]. Available: {citation.url}"
    
    def _generate_apa_reference_list(self, citations: List[Citation]) -> str:
        """Generate APA format reference list."""
        references = []
        for citation in citations:
            references.append(self._generate_apa_citation(citation))
        
        return "\n\n".join(references)
    
    def _generate_mla_reference_list(self, citations: List[Citation]) -> str:
        """Generate MLA format reference list."""
        references = []
        for citation in citations:
            references.append(self._generate_mla_citation(citation))
        
        return "\n\n".join(references)
    
    def _generate_chicago_reference_list(self, citations: List[Citation]) -> str:
        """Generate Chicago format reference list."""
        references = []
        for citation in citations:
            references.append(self._generate_chicago_citation(citation))
        
        return "\n\n".join(references)
    
    def _generate_ieee_reference_list(self, citations: List[Citation]) -> str:
        """Generate IEEE format reference list."""
        references = []
        for citation in citations:
            references.append(self._generate_ieee_citation(citation))
        
        return "\n\n".join(references)
    
    def _generate_bibtex_export(self) -> str:
        """Generate BibTeX export."""
        bibtex_entries = []
        for citation in self.citations.values():
            entry = f"@misc{{{citation.id},\n"
            entry += f"  title = {{{citation.title}}},\n"
            if citation.authors:
                entry += f"  author = {{{' and '.join(citation.authors)}}},\n"
            if citation.publication_date:
                entry += f"  year = {{{citation.publication_date[:4]}}},\n"
            entry += f"  url = {{{citation.url}}},\n"
            entry += f"  urldate = {{{citation.access_date}}}\n"
            entry += "}"
            bibtex_entries.append(entry)
        
        return "\n\n".join(bibtex_entries)
    
    def _generate_ris_export(self) -> str:
        """Generate RIS export."""
        ris_entries = []
        for citation in self.citations.values():
            entry = []
            entry.append("TY  - GEN")
            entry.append(f"TI  - {citation.title}")
            if citation.authors:
                for author in citation.authors:
                    entry.append(f"AU  - {author}")
            if citation.publication_date:
                entry.append(f"PY  - {citation.publication_date[:4]}")
            entry.append(f"UR  - {citation.url}")
            entry.append(f"ER  -")
            ris_entries.append("\n".join(entry))
        
        return "\n\n".join(ris_entries)
    
    def _citation_to_dict(self, citation: Citation) -> Dict[str, Any]:
        """Convert citation to dictionary for JSON export."""
        return {
            'id': citation.id,
            'url': citation.url,
            'title': citation.title,
            'authors': citation.authors,
            'publication_date': citation.publication_date,
            'access_date': citation.access_date,
            'source_type': citation.source_type,
            'doi': citation.doi,
            'journal': citation.journal,
            'volume': citation.volume,
            'issue': citation.issue,
            'pages': citation.pages,
            'publisher': citation.publisher,
            'abstract': citation.abstract,
            'keywords': citation.keywords,
            'citation_count': citation.citation_count,
            'relevance_score': citation.relevance_score
        }

# Global instance
citation_manager = CitationManager()
