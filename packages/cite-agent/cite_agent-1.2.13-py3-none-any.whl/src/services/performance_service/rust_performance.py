"""
High-performance Rust-powered services for web scraping and text processing.
This module provides Python bindings to the Rust performance library.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

try:
    import nocturnal_performance as rust_perf  # type: ignore[import]
    RUST_AVAILABLE = True
    logger.info("Rust performance module loaded successfully")
except ImportError:
    RUST_AVAILABLE = False
    logger.warning("Rust performance module not available, falling back to Python implementations")

@dataclass
class ScrapedContent:
    """Represents scraped content from a URL."""
    url: str
    title: str
    content: str
    metadata: Dict[str, str]
    timestamp: datetime

@dataclass
class ProcessedText:
    """Represents processed text with various analyses."""
    original: str
    cleaned: str
    chunks: List[str]
    keywords: List[str]
    summary: str

class HighPerformanceService:
    """High-performance service using Rust backend when available."""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.rust_scraper = None
        
        if RUST_AVAILABLE:
            try:
                self.rust_scraper = rust_perf.HighPerformanceScraper(max_concurrent)
                logger.info("Initialized Rust performance scraper")
            except Exception as e:
                logger.error(f"Failed to initialize Rust scraper: {e}")
                self.rust_scraper = None

    async def scrape_urls(self, urls: List[str]) -> List[ScrapedContent]:
        """Scrape multiple URLs concurrently with high performance."""
        if not urls:
            return []
            
        if self.rust_scraper and RUST_AVAILABLE:
            try:
                # Use Rust implementation
                rust_results = await self.rust_scraper.scrape_urls(urls)
                
                # Convert Rust results to Python objects
                results = []
                for result in rust_results:
                    scraped = ScrapedContent(
                        url=result["url"],
                        title=result["title"],
                        content=result["content"],
                        metadata=result["metadata"],
                        timestamp=datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
                    )
                    results.append(scraped)
                
                logger.info(f"Scraped {len(results)} URLs using Rust backend")
                return results
                
            except Exception as e:
                logger.error(f"Rust scraping failed, falling back to Python: {e}")
        
        # Fallback to Python implementation
        return await self._scrape_urls_python(urls)

    async def process_text_batch(self, texts: List[str]) -> List[ProcessedText]:
        """Process multiple texts concurrently with high performance."""
        if not texts:
            return []
            
        if self.rust_scraper and RUST_AVAILABLE:
            try:
                # Use Rust implementation
                rust_results = await self.rust_scraper.process_text_batch(texts)
                
                # Convert Rust results to Python objects
                results = []
                for result in rust_results:
                    processed = ProcessedText(
                        original=result["original"],
                        cleaned=result["cleaned"],
                        chunks=result["chunks"],
                        keywords=result["keywords"],
                        summary=result["summary"]
                    )
                    results.append(processed)
                
                logger.info(f"Processed {len(results)} texts using Rust backend")
                return results
                
            except Exception as e:
                logger.error(f"Rust text processing failed, falling back to Python: {e}")
        
        # Fallback to Python implementation
        return await self._process_text_batch_python(texts)

    async def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text using high-performance algorithms."""
        if self.rust_scraper and RUST_AVAILABLE:
            try:
                return await self.rust_scraper.extract_keywords(text, max_keywords)
            except Exception as e:
                logger.error(f"Rust keyword extraction failed, falling back to Python: {e}")
        
        # Fallback to Python implementation
        return await self._extract_keywords_python(text, max_keywords)

    async def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Chunk text into smaller pieces with overlap."""
        if self.rust_scraper and RUST_AVAILABLE:
            try:
                return await self.rust_scraper.chunk_text(text, chunk_size, overlap)
            except Exception as e:
                logger.error(f"Rust text chunking failed, falling back to Python: {e}")
        
        # Fallback to Python implementation
        return await self._chunk_text_python(text, chunk_size, overlap)

    def fast_text_clean(self, text: str) -> str:
        """Fast text cleaning using Rust implementation."""
        if RUST_AVAILABLE:
            try:
                return rust_perf.fast_text_clean(text)
            except Exception as e:
                logger.error(f"Rust text cleaning failed, falling back to Python: {e}")
        
        # Fallback to Python implementation
        return self._clean_text_python(text)

    def fast_url_validation(self, url: str) -> bool:
        """Fast URL validation using Rust implementation."""
        if RUST_AVAILABLE:
            try:
                return rust_perf.fast_url_validation(url)
            except Exception as e:
                logger.error(f"Rust URL validation failed, falling back to Python: {e}")
        
        # Fallback to Python implementation
        return self._validate_url_python(url)

    def fast_text_similarity(self, text1: str, text2: str) -> float:
        """Fast text similarity calculation using Rust implementation."""
        if RUST_AVAILABLE:
            try:
                return rust_perf.fast_text_similarity(text1, text2)
            except Exception as e:
                logger.error(f"Rust text similarity failed, falling back to Python: {e}")
        
        # Fallback to Python implementation
        return self._calculate_similarity_python(text1, text2)

    # Python fallback implementations
    async def _scrape_urls_python(self, urls: List[str]) -> List[ScrapedContent]:
        """Python fallback implementation for URL scraping."""
        import aiohttp
        from bs4 import BeautifulSoup
        import re
        
        async def scrape_single_url(session: aiohttp.ClientSession, url: str) -> Optional[ScrapedContent]:
            try:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title = soup.find('title')
                    title_text = title.get_text() if title else "No title"
                    
                    # Extract content
                    content_selectors = ['article', 'main', '[role="main"]', '.content', '.main-content', 'body']
                    content = ""
                    for selector in content_selectors:
                        element = soup.select_one(selector)
                        if element:
                            content = element.get_text(separator=' ', strip=True)
                            break
                    
                    # Extract metadata
                    metadata = {}
                    for meta in soup.find_all('meta'):
                        name = meta.get('name') or meta.get('property')
                        content_attr = meta.get('content')
                        if name and content_attr:
                            metadata[name] = content_attr
                    
                    return ScrapedContent(
                        url=url,
                        title=title_text,
                        content=content,
                        metadata=metadata,
                        timestamp=_utc_now()
                    )
                    
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                return None
        
        # Scrape URLs concurrently
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [scrape_single_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out None results and exceptions
            scraped_content = []
            for result in results:
                if isinstance(result, ScrapedContent):
                    scraped_content.append(result)
            
            return scraped_content

    async def _process_text_batch_python(self, texts: List[str]) -> List[ProcessedText]:
        """Python fallback implementation for text processing."""
        tasks = [self._process_single_text_python(text) for text in texts]
        return await asyncio.gather(*tasks)

    async def _process_single_text_python(self, text: str) -> ProcessedText:
        """Process a single text using Python implementation."""
        cleaned = self._clean_text_python(text)
        chunks = await self._chunk_text_python(cleaned, 1000, 200)
        keywords = await self._extract_keywords_python(cleaned, 10)
        summary = await self._generate_summary_python(cleaned)
        
        return ProcessedText(
            original=text,
            cleaned=cleaned,
            chunks=chunks,
            keywords=keywords,
            summary=summary
        )

    def _clean_text_python(self, text: str) -> str:
        """Python implementation of text cleaning."""
        import re
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}]', '', text)
        
        # Normalize quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('–', '-').replace('—', '-')
        
        return text.strip()

    async def _chunk_text_python(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Python implementation of text chunking."""
        import re
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                if overlap > 0:
                    words = current_chunk.split()
                    overlap_words = min(overlap // 10, len(words))
                    if overlap_words > 0:
                        current_chunk = " ".join(words[-overlap_words:]) + " "
                        current_size = len(current_chunk)
                    else:
                        current_chunk = ""
                        current_size = 0
                else:
                    current_chunk = ""
                    current_size = 0
            
            current_chunk += sentence + ". "
            current_size += sentence_size + 2
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    async def _extract_keywords_python(self, text: str, max_keywords: int) -> List[str]:
        """Python implementation of keyword extraction."""
        import re
        from collections import Counter
        
        # Stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        words = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Count frequencies
        word_freq = Counter(words)
        
        # Return top keywords
        return [word for word, _ in word_freq.most_common(max_keywords)]

    async def _generate_summary_python(self, text: str) -> str:
        """Python implementation of text summarization."""
        import re
        from collections import Counter
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 3:
            return text
        
        # Calculate word frequencies
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        word_freq = Counter(words)
        
        # Score sentences
        sentence_scores = []
        for i, sentence in enumerate(sentences):
            sentence_words = re.findall(r'\b[a-zA-Z]+\b', sentence.lower())
            score = sum(word_freq.get(word, 0) for word in sentence_words)
            sentence_scores.append((i, score))
        
        # Sort by score and take top sentences
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        top_indices = sorted([i for i, _ in sentence_scores[:3]])
        
        summary = ". ".join(sentences[i] for i in top_indices)
        return summary + "."

    def _validate_url_python(self, url: str) -> bool:
        """Python implementation of URL validation."""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _calculate_similarity_python(self, text1: str, text2: str) -> float:
        """Python implementation of text similarity."""
        import re
        from collections import Counter
        
        # Extract words
        words1 = set(re.findall(r'\b[a-zA-Z]+\b', text1.lower()))
        words2 = set(re.findall(r'\b[a-zA-Z]+\b', text2.lower()))
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0

# Global instance
performance_service = HighPerformanceService()
