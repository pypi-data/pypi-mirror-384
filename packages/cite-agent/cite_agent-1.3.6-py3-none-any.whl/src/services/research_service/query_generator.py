# src/services/research_service/query_generator.py

import logging
import re
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from src.services.llm_service.llm_manager import LLMManager

# Configure structured logging
logger = logging.getLogger(__name__)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

class EnhancedQueryGenerator:
    """
    Enhanced query generator with comprehensive error handling, security, and observability.
    
    Features:
    - Secure query generation and optimization
    - Input validation and sanitization
    - Comprehensive error handling and retry logic
    - Structured logging and monitoring
    - Protection against injection attacks
    - Research plan generation
    """
    
    def __init__(self, llm_manager: LLMManager):
        """
        Initialize query generator with enhanced security and error handling.
        
        Args:
            llm_manager: LLM manager instance
            
        Raises:
            ValueError: If LLM manager is invalid
        """
        try:
            if not llm_manager:
                raise ValueError("LLM manager instance is required")
            
            logger.info("Initializing EnhancedQueryGenerator with enhanced security")
            self.llm_manager = llm_manager
            logger.info("EnhancedQueryGenerator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize EnhancedQueryGenerator: {str(e)}")
            raise
    
    def _validate_topic(self, topic: str) -> None:
        """
        Validate research topic for security and safety.
        
        Args:
            topic: Research topic to validate
            
        Raises:
            ValueError: If topic is invalid
        """
        if not isinstance(topic, str):
            raise ValueError("Topic must be a string")
        
        if not topic.strip():
            raise ValueError("Topic cannot be empty")
        
        if len(topic) > 500:  # Reasonable limit
            raise ValueError("Topic too long (max 500 characters)")
        
        # Check for potentially dangerous content
        dangerous_patterns = [
            r'<script.*?>.*?</script>',  # Script tags
            r'javascript:',              # JavaScript protocol
            r'data:text/html',           # Data URLs
            r'vbscript:',                # VBScript
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, topic, re.IGNORECASE):
                raise ValueError(f"Topic contains potentially dangerous patterns: {pattern}")
    
    def _validate_research_intent(self, research_intent: str) -> None:
        """
        Validate research intent for security and safety.
        
        Args:
            research_intent: Research intent to validate
            
        Raises:
            ValueError: If research intent is invalid
        """
        if not isinstance(research_intent, str):
            raise ValueError("Research intent must be a string")
        
        if not research_intent.strip():
            raise ValueError("Research intent cannot be empty")
        
        if len(research_intent) > 2000:  # Reasonable limit
            raise ValueError("Research intent too long (max 2000 characters)")
        
        # Check for potentially dangerous content
        dangerous_patterns = [
            r'<script.*?>.*?</script>',  # Script tags
            r'javascript:',              # JavaScript protocol
            r'data:text/html',           # Data URLs
            r'vbscript:',                # VBScript
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, research_intent, re.IGNORECASE):
                raise ValueError(f"Research intent contains potentially dangerous patterns: {pattern}")
    
    def _sanitize_text(self, text: str, max_length: int = 2000) -> str:
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
    
    async def generate_research_queries(self, 
                                       topic: str, 
                                       research_intent: str,
                                       context: Optional[Dict] = None) -> List[str]:
        """
        Generate optimized search queries with enhanced error handling and security.
        
        Args:
            topic: Main research topic
            research_intent: Detailed description of research goals and focus
            context: Optional additional context (background, field, etc.)
            
        Returns:
            List of optimized search queries
            
        Raises:
            ValueError: If inputs are invalid
            ConnectionError: If query generation fails
        """
        try:
            # Input validation and sanitization
            self._validate_topic(topic)
            self._validate_research_intent(research_intent)
            
            sanitized_topic = self._sanitize_text(topic, max_length=500)
            sanitized_intent = self._sanitize_text(research_intent, max_length=2000)
            
            logger.info(f"Generating research queries for topic: {sanitized_topic[:50]}...")
            
            prompt = f"""You are an expert academic researcher helping to formulate optimal search queries.

RESEARCH TOPIC: {sanitized_topic}

RESEARCH INTENT:
{sanitized_intent}

{self._format_context(context) if context else ""}

Generate 5-7 search queries that would find the most relevant academic papers for this research. 
For each query:
1. Focus on different aspects/angles of the research topic
2. Use terminology and phrasing typically found in academic papers
3. Include relevant field-specific keywords
4. Consider both broader conceptual searches and more specific technical searches
5. Optimize for finding high-quality, relevant papers rather than general information

Format your response as a list of queries only, one per line, with no numbering or other text.
"""
            
            # Generate queries with retry logic
            queries = await self._generate_queries_with_retry(prompt, sanitized_topic)
            
            logger.info(f"Successfully generated {len(queries)} research queries")
            return queries
            
        except ValueError as e:
            logger.error(f"Invalid input for query generation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating research queries: {str(e)}")
            raise
    
    async def _generate_queries_with_retry(self, prompt: str, fallback_topic: str, max_retries: int = 3) -> List[str]:
        """
        Generate queries with retry logic.
        
        Args:
            prompt: Generation prompt
            fallback_topic: Fallback topic if generation fails
            max_retries: Maximum retry attempts
            
        Returns:
            List of generated queries
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await self.llm_manager.generate_synthesis(
                    [{"content": prompt}],
                    prompt
                )
                
                if isinstance(response, dict) and "summary" in response:
                    response_text = response["summary"]
                else:
                    response_text = str(response)
                
                # Parse queries from response
                queries = [q.strip() for q in response_text.split('\n') if q.strip()]
                
                # Validate queries
                valid_queries = []
                for query in queries:
                    if len(query) > 10 and len(query) < 200:  # Reasonable length
                        sanitized_query = self._sanitize_text(query, max_length=200)
                        valid_queries.append(sanitized_query)
                
                # Ensure we got at least one query
                if valid_queries:
                    return valid_queries[:7]  # Limit to 7 queries
                else:
                    raise ValueError("No valid queries generated")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Query generation attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Short delay between retries
        
        # All retries failed, return fallback
        logger.warning(f"All query generation attempts failed, using fallback")
        return [fallback_topic]
    
    async def generate_research_plan(self, topic: str, research_intent: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive research plan with enhanced error handling and security.
        
        Args:
            topic: Main research topic
            research_intent: Detailed description of research goals and focus
            context: Optional additional context
            
        Returns:
            Comprehensive research plan
            
        Raises:
            ValueError: If inputs are invalid
            ConnectionError: If plan generation fails
        """
        try:
            # Input validation and sanitization
            self._validate_topic(topic)
            self._validate_research_intent(research_intent)
            
            sanitized_topic = self._sanitize_text(topic, max_length=500)
            sanitized_intent = self._sanitize_text(research_intent, max_length=2000)
            
            logger.info(f"Generating research plan for topic: {sanitized_topic[:50]}...")
            
            # Create a prompt specifically focused on detailed keywords and queries
            prompt = f"""You are a research expert creating a structured research plan for "{sanitized_topic}".

RESEARCH TOPIC: {sanitized_topic}

RESEARCH INTENT:
{sanitized_intent}

{self._format_context(context) if context else ""}

I need a DETAILED research plan with particular focus on search terms and queries.

Your plan MUST include:

1. Primary Research Question: A precise, focused question that guides the investigation

2. Sub-Questions (5-7): Specific questions that break down the main research question into manageable parts
- Include technical questions about methods and implementations
- Include questions about current limitations and challenges
- Include questions about practical applications

3. Relevant Academic Disciplines: List 3-5 specific academic fields relevant to this research

4. Search Strategy:
- Keywords (10-15): Technical terms, scientific concepts, and domain-specific vocabulary 
- Search Queries (5-7): Carefully crafted search strings that would yield relevant academic papers

5. Methodological Considerations: Brief notes on research approaches

CRITICAL: For each section, particularly keywords and search queries, BE EXTREMELY SPECIFIC TO THE TOPIC.
For example, for quantum computing in drug discovery, include terms like "quantum chemistry algorithms", 
"molecular docking", "NISQ devices in pharmaceutical research", etc.

Format your response EXACTLY as a JSON object with these sections.
"""
            
            # Generate plan with retry logic
            plan = await self._generate_plan_with_retry(prompt, sanitized_topic)
            
            logger.info("Successfully generated research plan")
            return plan
            
        except ValueError as e:
            logger.error(f"Invalid input for plan generation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating research plan: {str(e)}")
            raise
    
    async def _generate_plan_with_retry(self, prompt: str, topic: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Generate research plan with retry logic.
        
        Args:
            prompt: Generation prompt
            topic: Research topic
            max_retries: Maximum retry attempts
            
        Returns:
            Generated research plan
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Generate plan
                response = await self.llm_manager.generate_synthesis(
                    [{"content": prompt}],
                    prompt
                )
                
                if isinstance(response, dict) and "summary" in response:
                    response_text = response["summary"]
                else:
                    response_text = str(response)
                
                logger.debug(f"Research plan raw response: {response_text[:100]}...")
                
                # Parse JSON response
                plan = self._parse_json_plan(response_text, topic)
                return plan
                
            except Exception as e:
                last_error = e
                logger.warning(f"Plan generation attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # Longer delay for plan generation
        
        # All retries failed, return default plan
        logger.warning(f"All plan generation attempts failed, using default plan")
        return self._generate_default_plan(topic)
    
    def _parse_json_plan(self, response_text: str, topic: str) -> Dict[str, Any]:
        """
        Parse JSON research plan with enhanced error handling.
        
        Args:
            response_text: LLM response text
            topic: Research topic
            
        Returns:
            Parsed research plan
        """
        try:
            # Find JSON in response by looking for opening/closing braces
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                # Try to fix common JSON issues before parsing
                json_str = json_str.replace('\n', ' ').replace('\\', '\\\\')
                plan = json.loads(json_str)
                
                # Ensure we have the required fields with defaults if missing
                plan = self._validate_and_fix_plan(plan, topic)
                return plan
            else:
                # Extract structured data if JSON not found
                return self._extract_structured_plan(response_text, topic)
                
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {str(e)}, extracting structured data")
            return self._extract_structured_plan(response_text, topic)
        except Exception as e:
            logger.error(f"Error parsing JSON plan: {str(e)}")
            return self._generate_default_plan(topic)
    
    def _validate_and_fix_plan(self, plan: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """
        Validate and fix research plan with defaults.
        
        Args:
            plan: Research plan to validate
            topic: Research topic
            
        Returns:
            Validated and fixed plan
        """
        try:
            if not isinstance(plan, dict):
                plan = {}
            
            # Ensure required fields with defaults
            if "primary_research_question" not in plan:
                plan["primary_research_question"] = f"How can {topic} be effectively developed and applied?"
            
            if "sub_questions" not in plan or not plan["sub_questions"]:
                plan["sub_questions"] = [
                    f"What are the current applications of {topic}?",
                    f"What are the technical challenges in implementing {topic}?",
                    f"How does {topic} compare to traditional approaches?",
                    f"What are the performance metrics for evaluating {topic}?",
                    f"What future developments are expected in {topic}?"
                ]
            
            if "disciplines" not in plan or not plan["disciplines"]:
                plan["disciplines"] = ["Computer Science", "Physics", "Chemistry", "Bioinformatics"]
            
            if "search_strategy" not in plan:
                plan["search_strategy"] = {}
            
            if "keywords" not in plan["search_strategy"] or not plan["search_strategy"]["keywords"]:
                # Generate topic-specific keywords
                words = topic.split()
                plan["search_strategy"]["keywords"] = [
                    topic,
                    f"{topic} applications",
                    f"{topic} algorithms",
                    f"{topic} implementations",
                    f"{topic} challenges",
                    " ".join(words[:1] + ["quantum"]),
                    " ".join(words[:1] + ["simulation"]),
                    " ".join(words[:1] + ["optimization"]),
                ]
            
            if "queries" not in plan["search_strategy"] or not plan["search_strategy"]["queries"]:
                # Generate topic-specific queries
                plan["search_strategy"]["queries"] = [
                    f'"{topic}" recent advances',
                    f'"{topic}" review',
                    f'"{topic}" applications',
                    f'"{topic}" implementation challenges',
                    f'"{topic}" performance comparison',
                ]
            
            if "methodological_considerations" not in plan:
                plan["methodological_considerations"] = f"Research on {topic} requires interdisciplinary approaches combining theoretical analysis and practical implementation."
            
            return plan
            
        except Exception as e:
            logger.error(f"Error validating and fixing plan: {str(e)}")
            return self._generate_default_plan(topic)
    
    def _extract_structured_plan(self, text: str, topic: str = "this topic") -> Dict[str, Any]:
        """
        Extract structured plan from text with enhanced error handling.
        
        Args:
            text: Text to extract from
            topic: Research topic
            
        Returns:
            Extracted plan
        """
        try:
            # Sanitize text
            sanitized_text = self._sanitize_text(text, max_length=5000)
            
            # Extract questions
            questions = []
            lines = sanitized_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and ('?' in line or line.startswith('Q')):
                    question = self._sanitize_text(line, max_length=300)
                    questions.append(question)
            
            # Extract keywords
            keywords = []
            for line in lines:
                line = line.strip()
                if line and len(line) < 50 and not line.startswith(('Q', 'A', '-', '*')):
                    keyword = self._sanitize_text(line, max_length=100)
                    keywords.append(keyword)
            
            return {
                "primary_research_question": f"How can {topic} be effectively developed and applied?",
                "sub_questions": questions[:7] if questions else [
                    f"What are the current applications of {topic}?",
                    f"What are the technical challenges in implementing {topic}?",
                    f"How does {topic} compare to traditional approaches?"
                ],
                "disciplines": ["Computer Science", "Physics", "Chemistry"],
                "search_strategy": {
                    "keywords": keywords[:15] if keywords else [topic, f"{topic} applications"],
                    "queries": [
                        f'"{topic}" recent advances',
                        f'"{topic}" review',
                        f'"{topic}" applications'
                    ]
                },
                "methodological_considerations": f"Research on {topic} requires systematic analysis and experimental validation."
            }
            
        except Exception as e:
            logger.error(f"Error extracting structured plan: {str(e)}")
            return self._generate_default_plan(topic)
    
    def _generate_default_plan(self, topic: str) -> Dict[str, Any]:
        """
        Generate default research plan.
        
        Args:
            topic: Research topic
            
        Returns:
            Default research plan
        """
        return {
            "primary_research_question": f"How can {topic} be effectively developed and applied?",
            "sub_questions": [
                f"What are the current applications of {topic}?",
                f"What are the technical challenges in implementing {topic}?",
                f"How does {topic} compare to traditional approaches?",
                f"What are the performance metrics for evaluating {topic}?",
                f"What future developments are expected in {topic}?"
            ],
            "disciplines": ["Computer Science", "Physics", "Chemistry", "Bioinformatics"],
            "search_strategy": {
                "keywords": [
                    topic,
                    f"{topic} algorithms",
                    f"{topic} implementations",
                    f"{topic} challenges",
                    "quantum computing",
                    "quantum chemistry",
                    "molecular simulation",
                    "quantum algorithms"
                ],
                "queries": [
                    f'"{topic}" recent advances',
                    f'"{topic}" review',
                    f'"{topic}" applications',
                    f'"{topic}" implementation challenges',
                    f'"{topic}" performance comparison'
                ]
            },
            "methodological_considerations": f"Research on {topic} requires interdisciplinary approaches combining theoretical analysis and practical implementation."
        }
    
    def _format_context(self, context: Optional[Dict]) -> str:
        """
        Format context for prompts with enhanced error handling.
        
        Args:
            context: Context dictionary
            
        Returns:
            Formatted context string
        """
        try:
            if not context:
                return ""
            
            if not isinstance(context, dict):
                logger.warning("Context is not a dictionary, ignoring")
                return ""
            
            context_parts = []
            
            if "background" in context:
                background = self._sanitize_text(str(context["background"]), max_length=500)
                context_parts.append(f"BACKGROUND: {background}")
            
            if "field" in context:
                field = self._sanitize_text(str(context["field"]), max_length=200)
                context_parts.append(f"FIELD: {field}")
            
            if "constraints" in context:
                constraints = self._sanitize_text(str(context["constraints"]), max_length=300)
                context_parts.append(f"CONSTRAINTS: {constraints}")
            
            if "goals" in context:
                goals = self._sanitize_text(str(context["goals"]), max_length=300)
                context_parts.append(f"GOALS: {goals}")
            
            return "\n\n".join(context_parts) if context_parts else ""
            
        except Exception as e:
            logger.error(f"Error formatting context: {str(e)}")
            return ""
    
    async def generate_concept_queries(self, concept: str, context: Optional[Dict] = None) -> List[str]:
        """
        Generate concept-specific queries with enhanced error handling and security.
        
        Args:
            concept: Concept to generate queries for
            context: Optional context
            
        Returns:
            List of concept queries
            
        Raises:
            ValueError: If concept is invalid
        """
        try:
            # Input validation
            self._validate_topic(concept)
            
            sanitized_concept = self._sanitize_text(concept, max_length=500)
            
            logger.info(f"Generating concept queries for: {sanitized_concept[:50]}...")
            
            prompt = f"""
            Generate 5-7 search queries specifically for the concept: "{sanitized_concept}"
            
            {self._format_context(context) if context else ""}
            
            Focus on:
            1. Core concept definition and theory
            2. Practical applications and implementations
            3. Related technologies and methods
            4. Current research and developments
            5. Challenges and limitations
            
            Return only the queries, one per line.
            """
            
            # Generate queries with retry logic
            queries = await self._generate_queries_with_retry(prompt, sanitized_concept)
            
            logger.info(f"Successfully generated {len(queries)} concept queries")
            return queries
            
        except ValueError as e:
            logger.error(f"Invalid input for concept query generation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating concept queries: {str(e)}")
            return [concept]  # Fallback
    
    async def identify_related_concepts(self, 
                                       concept: str, 
                                       web_sources: List[Dict],
                                       academic_sources: List[Dict]) -> List[str]:
        """
        Identify related concepts with enhanced error handling and security.
        
        Args:
            concept: Main concept
            web_sources: List of web sources
            academic_sources: List of academic sources
            
        Returns:
            List of related concepts
            
        Raises:
            ValueError: If concept is invalid
        """
        try:
            # Input validation
            self._validate_topic(concept)
            
            if not isinstance(web_sources, list):
                web_sources = []
            if not isinstance(academic_sources, list):
                academic_sources = []
            
            sanitized_concept = self._sanitize_text(concept, max_length=500)
            
            logger.info(f"Identifying related concepts for: {sanitized_concept[:50]}...")
            
            # Prepare source summaries
            source_texts = []
            
            for source in web_sources[:5]:  # Limit to 5 sources
                if isinstance(source, dict) and source.get('content'):
                    content = self._sanitize_text(str(source['content']), max_length=500)
                    source_texts.append(content)
            
            for source in academic_sources[:5]:  # Limit to 5 sources
                if isinstance(source, dict) and source.get('summary'):
                    summary = self._sanitize_text(str(source['summary']), max_length=500)
                    source_texts.append(summary)
            
            if not source_texts:
                logger.warning("No source content available for concept identification")
                return []
            
            prompt = f"""
            Based on the following sources, identify 5-10 concepts related to "{sanitized_concept}":
            
            Sources:
            {' '.join(source_texts)}
            
            Focus on:
            1. Directly related concepts
            2. Supporting technologies
            3. Complementary approaches
            4. Related methodologies
            5. Associated applications
            
            Return only the concept names, one per line.
            """
            
            # Generate related concepts with retry logic
            concepts = await self._generate_queries_with_retry(prompt, sanitized_concept)
            
            logger.info(f"Successfully identified {len(concepts)} related concepts")
            return concepts
            
        except ValueError as e:
            logger.error(f"Invalid input for concept identification: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error identifying related concepts: {str(e)}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the query generator.
        
        Returns:
            Health status
        """
        try:
            health_status = {
                "status": "healthy",
                "timestamp": _utc_timestamp(),
                "components": {}
            }
            
            # Check LLM manager
            try:
                llm_health = await self.llm_manager.health_check()
                health_status["components"]["llm_manager"] = llm_health
                if llm_health.get("status") != "healthy":
                    health_status["status"] = "degraded"
            except Exception as e:
                health_status["components"]["llm_manager"] = {"status": "error", "error": str(e)}
                health_status["status"] = "degraded"
            
            logger.info(f"Health check completed: {health_status['status']}")
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": _utc_timestamp()
            }