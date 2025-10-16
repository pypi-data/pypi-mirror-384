# src/services/research_service/critical_paper_detector.py

import logging
import re
import math
from typing import List, Dict, Any, Set, Optional
from collections import Counter
import networkx as nx  # type: ignore[import]
from datetime import datetime, timezone

# Configure structured logging
logger = logging.getLogger(__name__)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

class CriticalPaperDetector:
    """
    Enhanced critical paper detector with comprehensive error handling, security, and observability.
    
    Features:
    - Secure paper analysis and scoring
    - Input validation and sanitization
    - Comprehensive error handling and fallback logic
    - Structured logging and monitoring
    - Protection against injection attacks
    - Multi-factor paper importance scoring
    """
    
    def __init__(self, db_operations=None):
        """
        Initialize detector with enhanced security and error handling.
        
        Args:
            db_operations: Optional database operations instance
            
        Raises:
            ValueError: If initialization fails
        """
        try:
            #logger.info("Initializing CriticalPaperDetector with enhanced security")
            
            self.db = db_operations
            
            # Define importance indicators with enhanced coverage
            self.method_terms = {
                "novel", "methodology", "approach", "framework", "technique", 
                "algorithm", "protocol", "procedure", "process", "method",
                "implementation", "design", "architecture", "strategy",
                "paradigm", "model", "system", "mechanism", "solution"
            }
            
            self.result_terms = {
                "significant", "breakthrough", "discovery", "finding",
                "evidence", "proves", "demonstrates", "shows", "reveals",
                "establishes", "confirms", "validates", "supports", "indicates",
                "suggests", "implies", "concludes", "determines", "identifies"
            }
            
            self.contradiction_terms = {
                "contrary", "opposed", "conflict", "contradiction", "inconsistent",
                "challenge", "dispute", "unlike", "differs", "contrast",
                "disagreement", "debate", "controversy", "question", "doubt",
                "skepticism", "criticism", "limitation", "weakness", "flaw"
            }
            
            #logger.info("CriticalPaperDetector initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CriticalPaperDetector: {str(e)}")
            raise
    
    def _validate_papers(self, papers: List[Dict[str, Any]]) -> None:
        """
        Validate papers list for security and safety.
        
        Args:
            papers: Papers list to validate
            
        Raises:
            ValueError: If papers list is invalid
        """
        if not isinstance(papers, list):
            raise ValueError("Papers must be a list")
        
        if len(papers) > 1000:  # Reasonable limit
            raise ValueError("Too many papers (max 1000)")
        
        for i, paper in enumerate(papers):
            if not isinstance(paper, dict):
                raise ValueError(f"Paper at index {i} must be a dictionary")
            
            # Validate required fields
            if "id" not in paper:
                raise ValueError(f"Paper at index {i} missing required 'id' field")
            
            paper_id = str(paper["id"])
            if len(paper_id) > 100:
                raise ValueError(f"Paper ID at index {i} too long (max 100 characters)")
            
            # Check for potentially dangerous content in text fields
            text_fields = ["title", "abstract", "summary"]
            for field in text_fields:
                if field in paper and paper[field]:
                    content = str(paper[field])
                    if len(content) > 10000:  # Reasonable limit
                        raise ValueError(f"Paper {field} at index {i} too long (max 10000 characters)")
    
    def _validate_threshold(self, threshold_percentage: int) -> None:
        """
        Validate threshold percentage.
        
        Args:
            threshold_percentage: Threshold percentage to validate
            
        Raises:
            ValueError: If threshold is invalid
        """
        if not isinstance(threshold_percentage, int):
            raise ValueError("Threshold percentage must be an integer")
        
        if threshold_percentage < 1 or threshold_percentage > 50:
            raise ValueError("Threshold percentage must be between 1 and 50")
    
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
            return ""
        
        if len(text) > max_length:
            text = text[:max_length]
        
        # Basic XSS protection
        sanitized = text.replace('<', '&lt;').replace('>', '&gt;')
        
        # Remove null bytes and other control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
        
        return sanitized.strip()
    
    async def identify_critical_papers(self, papers: List[Dict[str, Any]], 
                                    threshold_percentage: int = 20) -> List[Dict[str, Any]]:
        """
        Identify critical papers with enhanced error handling and security.
        
        Args:
            papers: List of paper dictionaries with metadata
            threshold_percentage: Percentage of papers to mark as critical
            
        Returns:
            List of critical papers with scores
            
        Raises:
            ValueError: If inputs are invalid
        """
        try:
            # Input validation
            self._validate_papers(papers)
            self._validate_threshold(threshold_percentage)
            
            if not papers:
                #logger.info("No papers provided for critical analysis")
                return []
            
            #logger.info(f"Analyzing {len(papers)} papers for critical importance (threshold: {threshold_percentage}%)")
            
            # Calculate scores for all papers with error handling
            paper_scores = {}
            for i, paper in enumerate(papers):
                try:
                    score = self._calculate_paper_score(paper)
                    paper_scores[paper["id"]] = score
                except Exception as e:
                    logger.warning(f"Error calculating score for paper {i}: {str(e)}")
                    paper_scores[paper["id"]] = 0.0  # Default score
            
            # Determine threshold based on percentage
            num_critical = max(1, int(len(papers) * threshold_percentage / 100))
            
            # Get top scoring papers
            top_papers = sorted(
                [(paper_id, score) for paper_id, score in paper_scores.items()],
                key=lambda x: x[1],
                reverse=True
            )[:num_critical]
            
            # Format results with error handling
            results = []
            for paper_id, score in top_papers:
                try:
                    paper_data = next((p for p in papers if p["id"] == paper_id), None)
                    if paper_data:
                        results.append({
                            "paper_id": paper_id,
                            "title": self._sanitize_text(paper_data.get("title", "Unknown"), max_length=200),
                            "score": round(score, 2),
                            "factors": self._get_factor_breakdown(paper_data, score),
                            "analyzed_at": _utc_timestamp()
                        })
                except Exception as e:
                    logger.warning(f"Error formatting result for paper {paper_id}: {str(e)}")
                    continue
            
            #logger.info(f"Successfully identified {len(results)} critical papers")
            return results
            
        except ValueError as e:
            logger.error(f"Invalid input for critical paper identification: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error identifying critical papers: {str(e)}")
            return []
    
    def _calculate_paper_score(self, paper: Dict[str, Any]) -> float:
        """
        Calculate importance score for a paper with enhanced error handling.
        
        Args:
            paper: Paper dictionary with metadata
            
        Returns:
            Numerical score (higher = more important)
        """
        try:
            score = 0.0
            
            # Factor 1: Citation impact (if available)
            try:
                citation_score = self._calculate_citation_score(paper)
                score += citation_score * 0.25  # 25% weight
            except Exception as e:
                logger.warning(f"Error calculating citation score: {str(e)}")
                score += 0.0
            
            # Factor 2: Recency
            try:
                recency_score = self._calculate_recency_score(paper)
                score += recency_score * 0.15  # 15% weight
            except Exception as e:
                logger.warning(f"Error calculating recency score: {str(e)}")
                score += 5.0  # Default middle score
            
            # Factor 3: Title and abstract significance
            try:
                significance_score = self._calculate_significance_score(paper)
                score += significance_score * 0.20  # 20% weight
            except Exception as e:
                logger.warning(f"Error calculating significance score: {str(e)}")
                score += 0.0
            
            # Factor 4: Methodology novelty
            try:
                methodology_score = self._calculate_methodology_score(paper)
                score += methodology_score * 0.20  # 20% weight
            except Exception as e:
                logger.warning(f"Error calculating methodology score: {str(e)}")
                score += 0.0
            
            # Factor 5: Contradiction potential
            try:
                contradiction_score = self._calculate_contradiction_score(paper)
                score += contradiction_score * 0.20  # 20% weight
            except Exception as e:
                logger.warning(f"Error calculating contradiction score: {str(e)}")
                score += 0.0
            
            return max(0.0, min(10.0, score))  # Ensure score is between 0 and 10
            
        except Exception as e:
            logger.error(f"Error calculating paper score: {str(e)}")
            return 0.0
    
    def _calculate_citation_score(self, paper: Dict[str, Any]) -> float:
        """
        Calculate score based on citation count with enhanced error handling.
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Citation score
        """
        try:
            citation_count = paper.get("citation_count", 0)
            
            # Validate citation count
            if not isinstance(citation_count, (int, float)):
                return 0.0
            
            citation_count = max(0, int(citation_count))
            
            # Log-scale to prevent extremely cited papers from dominating
            if citation_count > 0:
                return min(10.0, 2.0 * math.log10(citation_count + 1))
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating citation score: {str(e)}")
            return 0.0
    
    def _calculate_recency_score(self, paper: Dict[str, Any]) -> float:
        """
        Calculate score based on paper recency with enhanced error handling.
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Recency score
        """
        try:
            year = paper.get("year")
            
            # Try to extract year from various fields
            if not year:
                # Try published_date
                if paper.get("published_date"):
                    year_match = re.search(r'20\d\d', str(paper.get("published_date", "")))
                    if year_match:
                        year = int(year_match.group(0))
                
                # Try publication_date
                if not year and paper.get("publication_date"):
                    year_match = re.search(r'20\d\d', str(paper.get("publication_date", "")))
                    if year_match:
                        year = int(year_match.group(0))
            
            if not year:
                return 5.0  # Middle score if unknown
                
            # Convert to int if it's a string
            if isinstance(year, str):
                try:
                    year = int(year)
                except ValueError:
                    return 5.0
            
            # Validate year range
            current_year = datetime.now().year
            if year < 1900 or year > current_year + 1:
                return 5.0  # Invalid year, use middle score
            
            # Scoring by recency
            years_old = current_year - year
            
            if years_old <= 1:
                return 10.0  # Very recent (0-1 years)
            elif years_old <= 3:
                return 8.0   # Recent (1-3 years)
            elif years_old <= 5:
                return 6.0   # Somewhat recent (3-5 years)
            elif years_old <= 10:
                return 4.0   # Older but still relevant (5-10 years)
            else:
                return 2.0   # Much older (>10 years)
                
        except Exception as e:
            logger.warning(f"Error calculating recency score: {str(e)}")
            return 5.0  # Default middle score
    
    def _calculate_significance_score(self, paper: Dict[str, Any]) -> float:
        """
        Calculate score based on title and abstract significance indicators with enhanced error handling.
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Significance score
        """
        try:
            title = self._sanitize_text(paper.get("title", ""), max_length=1000).lower()
            abstract = self._sanitize_text(paper.get("abstract", ""), max_length=5000).lower()
            
            combined_text = title + " " + abstract
            
            # Check for significant result terms
            result_count = sum(1 for term in self.result_terms if term in combined_text)
            
            # Score based on significance indicators
            score = min(10.0, result_count * 2.0)
            
            return score
            
        except Exception as e:
            logger.warning(f"Error calculating significance score: {str(e)}")
            return 0.0
    
    def _calculate_methodology_score(self, paper: Dict[str, Any]) -> float:
        """
        Calculate score based on methodology innovation indicators with enhanced error handling.
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Methodology score
        """
        try:
            title = self._sanitize_text(paper.get("title", ""), max_length=1000).lower()
            abstract = self._sanitize_text(paper.get("abstract", ""), max_length=5000).lower()
            
            combined_text = title + " " + abstract
            
            # Check for methodology terms
            method_count = sum(1 for term in self.method_terms if term in combined_text)
            
            # Score based on methodology indicators
            score = min(10.0, method_count * 2.0)
            
            return score
            
        except Exception as e:
            logger.warning(f"Error calculating methodology score: {str(e)}")
            return 0.0
    
    def _calculate_contradiction_score(self, paper: Dict[str, Any]) -> float:
        """
        Calculate score based on contradiction/challenge indicators with enhanced error handling.
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Contradiction score
        """
        try:
            title = self._sanitize_text(paper.get("title", ""), max_length=1000).lower()
            abstract = self._sanitize_text(paper.get("abstract", ""), max_length=5000).lower()
            
            combined_text = title + " " + abstract
            
            # Check for contradiction terms
            contradiction_count = sum(1 for term in self.contradiction_terms if term in combined_text)
            
            # Score based on contradiction indicators
            score = min(10.0, contradiction_count * 2.0)
            
            return score
            
        except Exception as e:
            logger.warning(f"Error calculating contradiction score: {str(e)}")
            return 0.0
    
    def _get_factor_breakdown(self, paper: Dict[str, Any], total_score: float) -> Dict[str, Any]:
        """
        Get detailed breakdown of scoring factors with enhanced error handling.
        
        Args:
            paper: Paper dictionary
            total_score: Total calculated score
            
        Returns:
            Factor breakdown dictionary
        """
        try:
            factors = {}
            
            # Calculate individual factor scores
            try:
                factors["citation_impact"] = round(self._calculate_citation_score(paper) * 0.25, 2)
            except Exception:
                factors["citation_impact"] = 0.0
            
            try:
                factors["recency"] = round(self._calculate_recency_score(paper) * 0.15, 2)
            except Exception:
                factors["recency"] = 0.0
            
            try:
                factors["significance"] = round(self._calculate_significance_score(paper) * 0.20, 2)
            except Exception:
                factors["significance"] = 0.0
            
            try:
                factors["methodology"] = round(self._calculate_methodology_score(paper) * 0.20, 2)
            except Exception:
                factors["methodology"] = 0.0
            
            try:
                factors["contradiction_potential"] = round(self._calculate_contradiction_score(paper) * 0.20, 2)
            except Exception:
                factors["contradiction_potential"] = 0.0
            
            # Add metadata
            factors["total_score"] = round(total_score, 2)
            factors["calculated_at"] = _utc_timestamp()
            
            return factors
            
        except Exception as e:
            logger.warning(f"Error getting factor breakdown: {str(e)}")
            return {
                "total_score": round(total_score, 2),
                "error": "Factor breakdown unavailable"
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the critical paper detector.
        
        Returns:
            Health status
        """
        try:
            health_status = {
                "status": "healthy",
                "timestamp": _utc_timestamp(),
                "components": {}
            }
            
            # Check term sets
            try:
                term_counts = {
                    "method_terms": len(self.method_terms),
                    "result_terms": len(self.result_terms),
                    "contradiction_terms": len(self.contradiction_terms)
                }
                health_status["components"]["term_sets"] = {
                    "status": "healthy",
                    "counts": term_counts
                }
            except Exception as e:
                health_status["components"]["term_sets"] = {"status": "error", "error": str(e)}
                health_status["status"] = "degraded"
            
            # Check database operations if available
            if self.db:
                try:
                    health_status["components"]["database"] = {"status": "available"}
                except Exception as e:
                    health_status["components"]["database"] = {"status": "error", "error": str(e)}
                    health_status["status"] = "degraded"
            else:
                health_status["components"]["database"] = {"status": "not_configured"}
            
            #logger.info(f"Health check completed: {health_status['status']}")
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": _utc_timestamp()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the detector.
        
        Returns:
            Statistics dictionary
        """
        try:
            stats = {
                "method_terms_count": len(self.method_terms),
                "result_terms_count": len(self.result_terms),
                "contradiction_terms_count": len(self.contradiction_terms),
                "database_configured": self.db is not None
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"error": str(e)}