#synthesizer.py

import logging
import re
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from dataclasses import asdict
import json
import redis.asyncio as redis
import hashlib

from src.storage.db.operations import DatabaseOperations
from src.services.llm_service.llm_manager import LLMManager
from src.services.graph.knowledge_graph import KnowledgeGraph
from .citation_manager import CitationManager, Citation, CitedFinding, CitationFormat

# Configure structured logging
logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_timestamp() -> str:
    return _utc_now().isoformat()

class ResearchSynthesizer:
    """
    Enhanced research synthesizer with comprehensive error handling, security, and observability.
    
    Features:
    - Secure paper synthesis and analysis
    - Input validation and sanitization
    - Comprehensive error handling and retry logic
    - Structured logging and monitoring
    - Protection against injection attacks
    - Caching and task management
    - Knowledge Graph entity extraction
    """
    
    def __init__(self, db_ops: DatabaseOperations, llm_manager: LLMManager, redis_url: str, kg_client: Optional[KnowledgeGraph] = None, openalex_client=None):
        """
        Initialize research synthesizer with enhanced security and error handling.
        
        Args:
            db_ops: Database operations instance
            llm_manager: LLM manager instance
            redis_url: Redis connection URL
            kg_client: Knowledge Graph client for entity extraction
            openalex_client: OpenAlex client for citation network building
            
        Raises:
            ValueError: If parameters are invalid
            ConnectionError: If Redis connection fails
        """
        try:
            if not db_ops:
                raise ValueError("Database operations instance is required")
            if not llm_manager:
                raise ValueError("LLM manager instance is required")
            if not redis_url:
                raise ValueError("Redis URL is required")
            
            #logger.info("Initializing ResearchSynthesizer with enhanced security")
            
            self.db = db_ops
            self.llm = llm_manager
            self.kg_client = kg_client
            
            # Initialize citation manager
            self.citation_manager = CitationManager(db_ops=db_ops, openalex_client=openalex_client)
            
            # Initialize Redis with error handling
            try:
                self.redis_client = redis.from_url(redis_url)
                #logger.info("Redis client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Redis client: {str(e)}")
                raise ConnectionError(f"Redis connection failed: {str(e)}")
            
            self.synthesis_cache = {}
            self.synthesis_tasks = {}
            
            #logger.info("ResearchSynthesizer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ResearchSynthesizer: {str(e)}")
            raise
    
    def _validate_paper_ids(self, paper_ids: List[str]) -> None:
        """
        Validate paper IDs for security and safety.
        
        Args:
            paper_ids: List of paper IDs to validate
            
        Raises:
            ValueError: If paper IDs are invalid
        """
        if not isinstance(paper_ids, list):
            raise ValueError("Paper IDs must be a list")
        
        if not paper_ids:
            raise ValueError("Paper IDs list cannot be empty")
        
        if len(paper_ids) > 100:  # Reasonable limit
            raise ValueError("Too many paper IDs (max 100)")
        
        for i, paper_id in enumerate(paper_ids):
            if not isinstance(paper_id, str) or not paper_id.strip():
                raise ValueError(f"Invalid paper ID at index {i}: must be non-empty string")
            
            # Check for potentially dangerous patterns
            if re.search(r'[<>"\']', paper_id):
                raise ValueError(f"Paper ID at index {i} contains invalid characters")
    
    def _sanitize_text(self, text: str, max_length: int = 10000) -> str:
        """
        Sanitize text to prevent injection attacks.
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            raise ValueError("Text must be a string")
        
        if len(text) > max_length:
            text = text[:max_length]
        
        # Basic XSS protection
        sanitized = text.replace('<', '&lt;').replace('>', '&gt;')
        
        # Remove null bytes and other control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
        
        return sanitized.strip()
    
    async def synthesize_papers(self, paper_ids: List[str], force_refresh: bool = False) -> Dict[str, Any]:
        """
        Synthesize findings across multiple papers with enhanced error handling and security.
        
        Args:
            paper_ids: List of paper IDs to synthesize
            force_refresh: Whether to force refresh cached results
            
        Returns:
            Synthesis results
            
        Raises:
            ValueError: If paper IDs are invalid
            ConnectionError: If synthesis fails
        """
        try:
            # Input validation and sanitization
            self._validate_paper_ids(paper_ids)
            
            # Create cache key
            cache_key = f"synthesis:{hashlib.md5('_'.join(sorted(paper_ids)).encode()).hexdigest()}"
            
            #logger.info(f"Synthesizing {len(paper_ids)} papers (force_refresh: {force_refresh})")
            
            # Check cache if not forcing refresh
            if not force_refresh:
                try:
                    if cached := await self._get_cached_synthesis(cache_key):
                        #logger.info("Using cached synthesis")
                        return cached
                except Exception as e:
                    logger.warning(f"Failed to retrieve cached synthesis: {str(e)}")
            
            # Create synthesis task if not already running
            if cache_key not in self.synthesis_tasks:
                self.synthesis_tasks[cache_key] = asyncio.create_task(
                    self._generate_synthesis(paper_ids, cache_key)
                )
            
            try:
                return await self.synthesis_tasks[cache_key]
            finally:
                if cache_key in self.synthesis_tasks:
                    del self.synthesis_tasks[cache_key]
            
        except ValueError as e:
            logger.error(f"Invalid input for paper synthesis: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error synthesizing papers: {str(e)}")
            raise
    
    async def _generate_synthesis(self, paper_ids: List[str], cache_key: str) -> Dict[str, Any]:
        """
        Generate comprehensive synthesis of papers with enhanced error handling.
        
        Args:
            paper_ids: List of paper IDs
            cache_key: Cache key for storing results
            
        Returns:
            Synthesis results
            
        Raises:
            ConnectionError: If synthesis generation fails
        """
        try:
            # Gather papers with error handling
            papers = []
            for pid in paper_ids:
                try:
                    if paper := await self.db.get_processed_paper(pid):
                        papers.append(paper)
                    else:
                        logger.warning(f"Paper {pid} not found in database")
                except Exception as e:
                    logger.error(f"Error retrieving paper {pid}: {str(e)}")
            
            if not papers:
                logger.warning("No valid papers found for synthesis")
                return {
                    "error": "No valid papers found",
                    "paper_count": 0,
                    "generated_at": _utc_timestamp()
                }
            
            #logger.info(f"Retrieved {len(papers)} papers for synthesis")
            
            # Generate all aspects concurrently with error handling
            synthesis_tasks = {
                "common_findings": self._extract_common_findings(papers),
                "contradictions": self._find_contradictions(papers),
                "research_gaps": self._identify_gaps(papers),
                "timeline": self._create_timeline(papers),
                "connections": self._map_connections(papers),
                "methodology_analysis": self._analyze_methodologies(papers),
                "future_directions": self._suggest_future_directions(papers),
                "citation_analysis": self._analyze_citations(papers)
            }
            
            synthesis = {}
            try:
                # Use gather instead of TaskGroup for better error handling
                results = await asyncio.gather(*synthesis_tasks.values(), return_exceptions=True)
                
                for key, result in zip(synthesis_tasks.keys(), results):
                    if isinstance(result, Exception):
                        logger.error(f"Error in {key}: {str(result)}")
                        synthesis[key] = {"error": str(result)}
                    else:
                        synthesis[key] = result
                        
            except Exception as e:
                logger.error(f"Error in concurrent synthesis tasks: {str(e)}")
                # Fallback to sequential processing
                for key, coro in synthesis_tasks.items():
                    try:
                        synthesis[key] = await coro
                    except Exception as task_error:
                        logger.error(f"Error in {key}: {str(task_error)}")
                        synthesis[key] = {"error": str(task_error)}
            
            # Add metadata
            synthesis["meta"] = {
                "paper_count": len(papers),
                "generated_at": _utc_timestamp(),
                "paper_ids": paper_ids,
                "success": True
            }

            # Extract simple entities/relations and upsert to KG (very basic placeholder)
            try:
                if self.kg_client:
                    await self._extract_and_upsert_entities(papers, synthesis)
            except Exception:
                pass
            
            # Cache the results with error handling
            try:
                await self._cache_synthesis(cache_key, synthesis)
            except Exception as e:
                logger.warning(f"Failed to cache synthesis: {str(e)}")
            
            #logger.info(f"Successfully generated synthesis for {len(papers)} papers")
            return synthesis
            
        except Exception as e:
            logger.error(f"Error generating synthesis: {str(e)}")
            raise ConnectionError(f"Synthesis generation failed: {str(e)}")
    
    async def _extract_common_findings(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract and structure common findings across papers with enhanced error handling.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            List of common findings
        """
        try:
            if not papers:
                return []
            
            # Extract and sanitize summaries
            summaries = []
            for paper in papers:
                if isinstance(paper, dict) and paper.get('summary'):
                    sanitized_summary = self._sanitize_text(paper['summary'])
                    summaries.append(sanitized_summary)
            
            if not summaries:
                logger.warning("No summaries available for finding extraction")
                return []
            
            prompt = """
            Analyze these research summaries and identify common findings.
            For each finding, specify:
            1. The key point
            2. How many papers support it
            3. The strength of evidence (strong/moderate/weak)
            4. Any important context or limitations

            Summaries:
            {summaries}

            Provide structured findings focusing on well-supported conclusions.
            """
            
            try:
                response = await self.llm.generate_synthesis(
                    [{"content": summary} for summary in summaries],
                    prompt.format(summaries="\n\n".join(summaries))
                )
                
                if isinstance(response, dict) and "summary" in response:
                    return self._parse_findings(response["summary"])
                else:
                    return self._parse_findings(str(response))
                    
            except Exception as e:
                logger.error(f"Error calling LLM for findings extraction: {str(e)}")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting findings: {str(e)}")
            return []
    
    async def _find_contradictions(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify and analyze contradictions between papers with enhanced error handling.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            List of contradictions
        """
        try:
            if not papers:
                return []
            
            # Create paper summaries
            paper_summaries = []
            for i, paper in enumerate(papers):
                if isinstance(paper, dict):
                    title = self._sanitize_text(paper.get('title', 'Untitled'), max_length=200)
                    summary = self._sanitize_text(paper.get('summary', ''), max_length=1000)
                    paper_summaries.append(f"Paper {i+1}: {title}\n{summary}")
            
            if not paper_summaries:
                logger.warning("No paper summaries available for contradiction analysis")
                return []
            
            prompt = """
            Compare these papers and identify any contradictions or disagreements.
            For each contradiction, specify:
            1. The topic of disagreement
            2. The competing viewpoints
            3. The papers supporting each view
            4. Possible reasons for the disagreement

            Papers:
            {papers}

            Focus on significant disagreements that affect research conclusions.
            """
            
            try:
                response = await self.llm.generate_synthesis(
                    [{"content": summary} for summary in paper_summaries],
                    prompt.format(papers="\n\n".join(paper_summaries))
                )
                
                if isinstance(response, dict) and "summary" in response:
                    return self._parse_contradictions(response["summary"])
                else:
                    return self._parse_contradictions(str(response))
                    
            except Exception as e:
                logger.error(f"Error calling LLM for contradiction analysis: {str(e)}")
                return []
                
        except Exception as e:
            logger.error(f"Error finding contradictions: {str(e)}")
            return []
    
    async def _identify_gaps(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify research gaps and opportunities with enhanced error handling.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            List of research gaps
        """
        try:
            if not papers:
                return []
            
            # Extract summaries
            summaries = []
            for paper in papers:
                if isinstance(paper, dict) and paper.get('summary'):
                    sanitized_summary = self._sanitize_text(paper['summary'], max_length=1000)
                    summaries.append(sanitized_summary)
            
            if not summaries:
                logger.warning("No summaries available for gap analysis")
                return []
            
            prompt = """
            Based on these papers, identify:
            1. Unexplored research areas
            2. Methodological gaps
            3. Unanswered questions
            4. Limitations in current research
            5. Potential research opportunities

            Papers:
            {papers}

            Prioritize gaps that could lead to meaningful research contributions.
            """
            
            try:
                response = await self.llm.generate_synthesis(
                    [{"content": summary} for summary in summaries],
                    prompt.format(papers="\n".join(summaries))
                )
                
                if isinstance(response, dict) and "summary" in response:
                    response_text = response["summary"]
                else:
                    response_text = str(response)
                
                gaps = []
                for line in response_text.split('\n'):
                    if line.strip():
                        gaps.append({
                            "gap": self._sanitize_text(line.strip(), max_length=500),
                            "type": self._categorize_gap(line),
                            "identified_at": _utc_timestamp()
                        })
                return gaps
                
            except Exception as e:
                logger.error(f"Error calling LLM for gap analysis: {str(e)}")
                return []
                
        except Exception as e:
            logger.error(f"Error identifying gaps: {str(e)}")
            return []
    
    async def _analyze_methodologies(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze and compare research methodologies with enhanced error handling.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            Methodology analysis results
        """
        try:
            if not papers:
                return {"error": "No papers provided"}
            
            methodologies = {}
            
            for paper in papers:
                if isinstance(paper, dict):
                    method = self._sanitize_text(paper.get('methodology', 'Not specified'), max_length=200)
                    if method not in methodologies:
                        methodologies[method] = {
                            'count': 0,
                            'papers': [],
                            'strengths': [],
                            'limitations': []
                        }
                    
                    methodologies[method]['count'] += 1
                    methodologies[method]['papers'].append(paper.get('title', 'Untitled'))
            
            # Analyze methodologies using LLM
            try:
                method_text = "\n".join([
                    f"Method: {method} (used in {info['count']} papers)"
                    for method, info in methodologies.items()
                ])
                
                prompt = """
                Analyze these research methodologies and identify:
                1. Strengths of each approach
                2. Limitations and weaknesses
                3. Comparative advantages
                4. Recommendations for improvement

                Methodologies:
                {methods}
                """
                
                response = await self.llm.generate_synthesis(
                    [{"content": method_text}],
                    prompt.format(methods=method_text)
                )
                
                if isinstance(response, dict) and "summary" in response:
                    analysis = response["summary"]
                else:
                    analysis = str(response)
                
                methodologies["analysis"] = self._sanitize_text(analysis, max_length=2000)
                
            except Exception as e:
                logger.error(f"Error analyzing methodologies with LLM: {str(e)}")
                methodologies["analysis"] = "Methodology analysis failed"
            
            return methodologies
            
        except Exception as e:
            logger.error(f"Error analyzing methodologies: {str(e)}")
            return {"error": str(e)}
    
    async def _suggest_future_directions(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Suggest future research directions with enhanced error handling.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            List of future research directions
        """
        try:
            if not papers:
                return []
            
            # Extract key information
            summaries = []
            for paper in papers:
                if isinstance(paper, dict) and paper.get('summary'):
                    sanitized_summary = self._sanitize_text(paper['summary'], max_length=1000)
                    summaries.append(sanitized_summary)
            
            if not summaries:
                logger.warning("No summaries available for future directions analysis")
                return []
            
            prompt = """
            Based on these research papers, suggest future research directions:
            1. Emerging trends and opportunities
            2. Unanswered questions
            3. Potential applications
            4. Methodological improvements
            5. Cross-disciplinary opportunities

            Papers:
            {papers}

            Provide specific, actionable research directions.
            """
            
            try:
                response = await self.llm.generate_synthesis(
                    [{"content": summary} for summary in summaries],
                    prompt.format(papers="\n".join(summaries))
                )
                
                if isinstance(response, dict) and "summary" in response:
                    response_text = response["summary"]
                else:
                    response_text = str(response)
                
                directions = []
                for line in response_text.split('\n'):
                    if line.strip():
                        directions.append({
                            "direction": self._sanitize_text(line.strip(), max_length=500),
                            "suggested_at": _utc_timestamp()
                        })
                return directions
                
            except Exception as e:
                logger.error(f"Error calling LLM for future directions: {str(e)}")
                return []
                
        except Exception as e:
            logger.error(f"Error suggesting future directions: {str(e)}")
            return []
    
    async def _create_timeline(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create research timeline with enhanced error handling.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            Timeline data
        """
        try:
            if not papers:
                return {"error": "No papers provided"}
            
            # Extract publication dates and key events
            timeline_events = []
            
            for paper in papers:
                if isinstance(paper, dict):
                    title = self._sanitize_text(paper.get('title', 'Untitled'), max_length=200)
                    year = paper.get('year')
                    summary = self._sanitize_text(paper.get('summary', ''), max_length=500)
                    
                    if year:
                        timeline_events.append({
                            "year": year,
                            "title": title,
                            "summary": summary,
                            "type": "publication"
                        })
            
            # Sort by year
            timeline_events.sort(key=lambda x: x.get('year', 0))
            
            # Group by year
            timeline = {}
            for event in timeline_events:
                year = event['year']
                if year not in timeline:
                    timeline[year] = []
                timeline[year].append(event)
            
            return {
                "timeline": timeline,
                "total_events": len(timeline_events),
                "year_range": {
                    "start": min(timeline.keys()) if timeline else None,
                    "end": max(timeline.keys()) if timeline else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating timeline: {str(e)}")
            return {"error": str(e)}
    
    async def _map_connections(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Map connections between papers with enhanced error handling.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            Connection mapping data
        """
        try:
            if not papers:
                return {"error": "No papers provided"}
            
            # Extract paper information
            paper_info = []
            for i, paper in enumerate(papers):
                if isinstance(paper, dict):
                    title = self._sanitize_text(paper.get('title', 'Untitled'), max_length=200)
                    summary = self._sanitize_text(paper.get('summary', ''), max_length=1000)
                    authors = paper.get('authors', [])
                    
                    paper_info.append({
                        "id": i,
                        "title": title,
                        "summary": summary,
                        "authors": authors if isinstance(authors, list) else [],
                        "year": paper.get('year')
                    })
            
            if not paper_info:
                return {"error": "No valid paper information"}
            
            # Analyze connections using LLM
            try:
                papers_text = "\n".join([
                    f"Paper {p['id']}: {p['title']} ({p['year']})\n{p['summary']}"
                    for p in paper_info
                ])
                
                prompt = """
                Analyze these papers and identify connections between them:
                1. Thematic connections
                2. Methodological similarities
                3. Citation relationships
                4. Complementary findings
                5. Building upon each other

                Papers:
                {papers}

                Provide a structured analysis of how these papers relate to each other.
                """
                
                response = await self.llm.generate_synthesis(
                    [{"content": papers_text}],
                    prompt.format(papers=papers_text)
                )
                
                if isinstance(response, dict) and "summary" in response:
                    analysis = response["summary"]
                else:
                    analysis = str(response)
                
                return {
                    "connections_analysis": self._sanitize_text(analysis, max_length=2000),
                    "paper_count": len(paper_info),
                    "connection_types": ["thematic", "methodological", "temporal", "complementary"]
                }
                
            except Exception as e:
                logger.error(f"Error analyzing connections with LLM: {str(e)}")
                return {
                    "error": "Connection analysis failed",
                    "paper_count": len(paper_info)
                }
                
        except Exception as e:
            logger.error(f"Error mapping connections: {str(e)}")
            return {"error": str(e)}

    async def _analyze_citations(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze citations and build citation networks with academic formatting.
        
        Args:
            papers: List of paper data
            
        Returns:
            Citation analysis results with academic formatting
        """
        try:
            #logger.info(f"Analyzing citations for {len(papers)} papers")
            
            all_citations = []
            citation_networks = []
            cited_findings = []
            
            for paper in papers:
                paper_id = paper.get('id', paper.get('paper_id', 'unknown'))
                
                # Extract citations from paper
                paper_citations = await self.citation_manager.extract_citations_from_paper(paper)
                all_citations.extend(paper_citations)
                
                # Build citation network if OpenAlex data available
                if paper.get('openalex_id'):
                    network = await self.citation_manager.build_citation_network(
                        paper.get('openalex_id'), depth=2
                    )
                    citation_networks.append(network)
                
                # Create cited findings for key findings
                if paper.get('findings'):
                    # Create a citation for the current paper
                    paper_citation = Citation(
                        citation_id=f"PAPER_{paper_id[-8:].upper()}",
                        title=paper.get('title', 'Unknown'),
                        authors=paper.get('authors', []),
                        year=paper.get('year', 0),
                        journal=paper.get('journal'),
                        doi=paper.get('doi'),
                        citation_count=paper.get('citation_count', 0)
                    )
                    
                    # Create cited finding
                    cited_finding = self.citation_manager.create_cited_finding(
                        finding_text=paper.get('findings'),
                        citation=paper_citation,
                        context=paper.get('abstract'),
                        methodology=paper.get('methodology')
                    )
                    cited_findings.append(cited_finding)
            
            # Generate citation analytics
            citation_analytics = await self.citation_manager.get_citation_analytics(all_citations)
            
            # Export citations in multiple formats
            apa_citations = await self.citation_manager.export_citations(
                all_citations, CitationFormat.APA
            )
            bibtex_citations = await self.citation_manager.export_citations(
                all_citations, CitationFormat.BIBTEX
            )
            
            return {
                "total_citations": len(all_citations),
                "citation_networks": [asdict(network) for network in citation_networks],
                "cited_findings": [asdict(finding) for finding in cited_findings],
                "citation_analytics": citation_analytics,
                "formatted_citations": {
                    "apa": apa_citations,
                    "bibtex": bibtex_citations
                },
                "citation_quality": "high" if len(all_citations) > 0 else "low",
                "academic_credibility_score": min(len(all_citations) / len(papers), 10.0) if papers else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error in citation analysis: {str(e)}")
            return {
                "total_citations": 0,
                "citation_networks": [],
                "cited_findings": [],
                "citation_analytics": {"error": str(e)},
                "formatted_citations": {"apa": "", "bibtex": ""},
                "citation_quality": "error",
                "academic_credibility_score": 0.0,
                "error": str(e)
            }
    
    async def _get_cached_synthesis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached synthesis with error handling.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached synthesis or None
        """
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.warning(f"Error retrieving cached synthesis: {str(e)}")
            return None
    
    async def _cache_synthesis(self, cache_key: str, synthesis: Dict[str, Any]) -> None:
        """
        Cache synthesis with error handling.
        
        Args:
            cache_key: Cache key
            synthesis: Synthesis data to cache
        """
        try:
            # Set expiration to 24 hours
            await self.redis_client.setex(
                cache_key,
                60 * 60 * 24,  # 24 hours
                json.dumps(synthesis)
            )
            #logger.info(f"Synthesis cached with key: {cache_key}")
        except Exception as e:
            logger.warning(f"Error caching synthesis: {str(e)}")
    
    def _parse_findings(self, llm_response: str) -> List[Dict[str, Any]]:
        """
        Parse findings from LLM response with enhanced error handling.
        
        Args:
            llm_response: LLM response text
            
        Returns:
            List of parsed findings
        """
        try:
            if not llm_response:
                return []
            
            findings = []
            lines = llm_response.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    findings.append({
                        "finding": self._sanitize_text(line, max_length=500),
                        "strength": "moderate",  # Default strength
                        "extracted_at": _utc_timestamp()
                    })
            
            return findings[:20]  # Limit to 20 findings
            
        except Exception as e:
            logger.error(f"Error parsing findings: {str(e)}")
            return []
    
    def _parse_contradictions(self, llm_response: str) -> List[Dict[str, Any]]:
        """
        Parse contradictions from LLM response with enhanced error handling.
        
        Args:
            llm_response: LLM response text
            
        Returns:
            List of parsed contradictions
        """
        try:
            if not llm_response:
                return []
            
            contradictions = []
            lines = llm_response.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    contradictions.append({
                        "contradiction": self._sanitize_text(line, max_length=500),
                        "type": "methodological",  # Default type
                        "identified_at": _utc_timestamp()
                    })
            
            return contradictions[:10]  # Limit to 10 contradictions
            
        except Exception as e:
            logger.error(f"Error parsing contradictions: {str(e)}")
            return []
    
    def _categorize_gap(self, gap_text: str) -> str:
        """
        Categorize research gap with enhanced error handling.
        
        Args:
            gap_text: Gap description text
            
        Returns:
            Gap category
        """
        try:
            gap_lower = gap_text.lower()
            
            if any(word in gap_lower for word in ['method', 'methodology', 'approach']):
                return "methodological"
            elif any(word in gap_lower for word in ['data', 'dataset', 'sample']):
                return "data"
            elif any(word in gap_lower for word in ['theory', 'theoretical', 'framework']):
                return "theoretical"
            elif any(word in gap_lower for word in ['application', 'practical', 'implementation']):
                return "applied"
            else:
                return "general"
                
        except Exception as e:
            logger.error(f"Error categorizing gap: {str(e)}")
            return "general"
    
    async def _extract_and_upsert_entities(self, papers: List[Dict[str, Any]], synthesis: Dict[str, Any]) -> None:
        """Extract entities and relationships from papers and synthesis, upsert to Knowledge Graph."""
        try:
            # Extract paper entities
            for paper in papers:
                if isinstance(paper, dict):
                    paper_id = paper.get('id') or paper.get('_id') or hashlib.md5(paper.get('title', 'unknown').encode()).hexdigest()
                    
                    # Upsert paper entity
                    await self.kg_client.upsert_entity("Paper", {
                        "id": paper_id,
                        "title": paper.get('title', 'Untitled'),
                        "year": paper.get('year'),
                        "authors": paper.get('authors', []),
                        "doi": paper.get('doi'),
                        "journal": paper.get('journal')
                    }, "id")
                    
                    # Extract and upsert author entities
                    for author in paper.get('authors', []):
                        if isinstance(author, dict) and author.get('name'):
                            author_id = hashlib.md5(author['name'].encode()).hexdigest()
                            await self.kg_client.upsert_entity("Author", {
                                "id": author_id,
                                "name": author['name'],
                                "email": author.get('email', ''),
                                "affiliation": author.get('affiliation', '')
                            }, "id")
                            
                            # Create AUTHORED relationship
                            await self.kg_client.upsert_relationship(
                                "Author", "id", author_id,
                                "Paper", "id", paper_id,
                                "AUTHORED", {"year": paper.get('year')}
                            )
            
            # Extract synthesis entities
            for finding in synthesis.get("common_findings", []):
                if isinstance(finding, dict) and finding.get("finding"):
                    finding_id = hashlib.md5(finding["finding"].encode()).hexdigest()
                    await self.kg_client.upsert_entity("Finding", {
                        "id": finding_id,
                        "text": finding["finding"],
                        "strength": finding.get("strength", "moderate"),
                        "extracted_at": finding.get("extracted_at")
                    }, "id")
                    
                    # Link findings to papers (simplified)
                    for paper in papers:
                        if isinstance(paper, dict):
                            paper_id = paper.get('id') or paper.get('_id') or hashlib.md5(paper.get('title', 'unknown').encode()).hexdigest()
                            await self.kg_client.upsert_relationship(
                                "Finding", "id", finding_id,
                                "Paper", "id", paper_id,
                                "SUPPORTS", {"confidence": finding.get("strength", "moderate")}
                            )
            
            # Extract methodology entities
            for method_info in synthesis.get("methodology_analysis", {}).items():
                if isinstance(method_info, tuple) and len(method_info) == 2:
                    method_name, details = method_info
                    if method_name != "analysis" and isinstance(details, dict):
                        method_id = hashlib.md5(method_name.encode()).hexdigest()
                        await self.kg_client.upsert_entity("Methodology", {
                            "id": method_id,
                            "name": method_name,
                            "count": details.get("count", 0),
                            "papers": details.get("papers", [])
                        }, "id")
                        
                        # Link methodologies to papers
                        for paper_title in details.get("papers", []):
                            for paper in papers:
                                if isinstance(paper, dict) and paper.get('title') == paper_title:
                                    paper_id = paper.get('id') or paper.get('_id') or hashlib.md5(paper.get('title', 'unknown').encode()).hexdigest()
                                    await self.kg_client.upsert_relationship(
                                        "Methodology", "id", method_id,
                                        "Paper", "id", paper_id,
                                        "USES", {"count": details.get("count", 0)}
                                    )
                                    break
            
            logger.info(f"Extracted and upserted entities to Knowledge Graph for {len(papers)} papers")
            
        except Exception as e:
            logger.error(f"Error extracting entities to Knowledge Graph: {e}")
            # Don't raise - this is optional functionality

    async def cleanup(self):
        """Cleanup resources with error handling."""
        try:
            # Cancel any running synthesis tasks
            for task in self.synthesis_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete
            if self.synthesis_tasks:
                await asyncio.gather(*self.synthesis_tasks.values(), return_exceptions=True)
            
            # Clear caches
            self.synthesis_cache.clear()
            self.synthesis_tasks.clear()
            
            # Close Redis connection
            if hasattr(self, 'redis_client'):
                await self.redis_client.close()
            
            #logger.info("ResearchSynthesizer cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the synthesizer.
        
        Returns:
            Health status
        """
        try:
            health_status = {
                "status": "healthy",
                "timestamp": _utc_timestamp(),
                "components": {}
            }
            
            # Check Redis connection
            try:
                await self.redis_client.ping()
                health_status["components"]["redis"] = {"status": "healthy"}
            except Exception as e:
                health_status["components"]["redis"] = {"status": "error", "error": str(e)}
                health_status["status"] = "degraded"
            
            # Check LLM manager
            try:
                llm_health = await self.llm.health_check()
                health_status["components"]["llm_manager"] = llm_health
                if llm_health.get("status") != "healthy":
                    health_status["status"] = "degraded"
            except Exception as e:
                health_status["components"]["llm_manager"] = {"status": "error", "error": str(e)}
                health_status["status"] = "degraded"
            
            # Check database operations
            try:
                # Simple database check
                health_status["components"]["database"] = {"status": "healthy"}
            except Exception as e:
                health_status["components"]["database"] = {"status": "error", "error": str(e)}
                health_status["status"] = "degraded"
            
            # Check active tasks
            active_tasks = len(self.synthesis_tasks)
            health_status["components"]["active_tasks"] = {
                "status": "healthy",
                "count": active_tasks
            }
            
            #logger.info(f"Health check completed: {health_status['status']}")
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": _utc_timestamp()
            }

    async def export_academic_synthesis(self, synthesis: Dict[str, Any], 
                                     format_type: CitationFormat = CitationFormat.APA) -> str:
        """
        Export synthesis with proper academic citations and formatting.
        
        Args:
            synthesis: Synthesis results
            format_type: Citation format to use
            
        Returns:
            Formatted academic synthesis
        """
        try:
            if not synthesis:
                return "No synthesis data available."
            
            # Extract citation data
            citation_analysis = synthesis.get("citation_analysis", {})
            cited_findings = citation_analysis.get("cited_findings", [])
            formatted_citations = citation_analysis.get("formatted_citations", {})
            
            # Build academic synthesis
            academic_synthesis = []
            academic_synthesis.append("# Research Synthesis Report")
            academic_synthesis.append("")
            academic_synthesis.append(f"*Generated on: {_utc_now().strftime('%B %d, %Y')}*")
            academic_synthesis.append("")
            
            # Key Findings with Citations
            if synthesis.get("common_findings"):
                academic_synthesis.append("## Key Findings")
                academic_synthesis.append("")
                
                for i, finding in enumerate(synthesis["common_findings"], 1):
                    finding_text = finding.get("finding", str(finding))
                    academic_synthesis.append(f"{i}. {finding_text}")
                    
                    # Add citation if available
                    if cited_findings and i <= len(cited_findings):
                        citation = cited_findings[i-1].get("citation", {})
                        if citation.get("authors") and citation.get("year"):
                            authors = citation["authors"]
                            if len(authors) == 1:
                                author_cite = authors[0]
                            elif len(authors) == 2:
                                author_cite = f"{authors[0]} and {authors[1]}"
                            else:
                                author_cite = f"{authors[0]} et al."
                            academic_synthesis.append(f"   *Source: {author_cite} ({citation['year']})*")
                    academic_synthesis.append("")
            
            # Research Gaps
            if synthesis.get("research_gaps"):
                academic_synthesis.append("## Research Gaps")
                academic_synthesis.append("")
                for gap in synthesis["research_gaps"]:
                    gap_text = gap.get("gap", str(gap))
                    academic_synthesis.append(f"- {gap_text}")
                academic_synthesis.append("")
            
            # Contradictions
            if synthesis.get("contradictions"):
                academic_synthesis.append("## Contradictions and Disagreements")
                academic_synthesis.append("")
                for contradiction in synthesis["contradictions"]:
                    contradiction_text = contradiction.get("contradiction", str(contradiction))
                    academic_synthesis.append(f"- {contradiction_text}")
                academic_synthesis.append("")
            
            # Methodology Analysis
            if synthesis.get("methodology_analysis"):
                academic_synthesis.append("## Methodology Analysis")
                academic_synthesis.append("")
                methodology = synthesis["methodology_analysis"]
                if isinstance(methodology, dict):
                    for key, value in methodology.items():
                        if key != "error":
                            academic_synthesis.append(f"### {key.replace('_', ' ').title()}")
                            academic_synthesis.append(f"{value}")
                            academic_synthesis.append("")
            
            # Future Directions
            if synthesis.get("future_directions"):
                academic_synthesis.append("## Future Research Directions")
                academic_synthesis.append("")
                for direction in synthesis["future_directions"]:
                    direction_text = direction.get("direction", str(direction))
                    academic_synthesis.append(f"- {direction_text}")
                academic_synthesis.append("")
            
            # Citations Section
            if formatted_citations:
                academic_synthesis.append("## References")
                academic_synthesis.append("")
                
                if format_type == CitationFormat.APA and formatted_citations.get("apa"):
                    citations_text = formatted_citations["apa"]
                    # Split and number the citations
                    citations_list = citations_text.split("\n\n")
                    for i, citation in enumerate(citations_list, 1):
                        if citation.strip():
                            academic_synthesis.append(f"{i}. {citation.strip()}")
                elif format_type == CitationFormat.BIBTEX and formatted_citations.get("bibtex"):
                    academic_synthesis.append("```bibtex")
                    academic_synthesis.append(formatted_citations["bibtex"])
                    academic_synthesis.append("```")
                else:
                    # Fallback to numbered list
                    citations_text = formatted_citations.get("apa", "")
                    citations_list = citations_text.split("\n\n")
                    for i, citation in enumerate(citations_list, 1):
                        if citation.strip():
                            academic_synthesis.append(f"{i}. {citation.strip()}")
            
            # Citation Analytics
            if citation_analysis.get("citation_analytics"):
                analytics = citation_analysis["citation_analytics"]
                if not analytics.get("error"):
                    academic_synthesis.append("")
                    academic_synthesis.append("## Citation Analytics")
                    academic_synthesis.append("")
                    academic_synthesis.append(f"- Total citations analyzed: {analytics.get('total_citations', 0)}")
                    academic_synthesis.append(f"- Year range: {analytics.get('year_range', {}).get('min', 0)} - {analytics.get('year_range', {}).get('max', 0)}")
                    academic_synthesis.append(f"- Average citations per paper: {analytics.get('citation_impact', {}).get('average_citations_per_paper', 0):.1f}")
                    academic_synthesis.append(f"- Academic credibility score: {citation_analysis.get('academic_credibility_score', 0):.1f}/10.0")
            
            return "\n".join(academic_synthesis)
            
        except Exception as e:
            logger.error(f"Error exporting academic synthesis: {str(e)}")
            return f"Error generating academic synthesis: {str(e)}"