# src/services/research_service/conversation_manager.py

import logging
import re
import asyncio
from typing import Dict, List, Any, Optional
import json
import uuid
from datetime import datetime, timezone

from src.services.llm_service.llm_manager import LLMManager

# Configure structured logging
logger = logging.getLogger(__name__)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

class ResearchConversationManager:
    """
    Enhanced research conversation manager with comprehensive error handling, security, and observability.
    
    Features:
    - Secure conversation management and storage
    - Input validation and sanitization
    - Comprehensive error handling and retry logic
    - Structured logging and monitoring
    - Protection against injection attacks
    - Research-focused conversation handling
    """
    
    def __init__(self, llm_manager: LLMManager, redis_client):
        """
        Initialize conversation manager with enhanced security and error handling.
        
        Args:
            llm_manager: LLM manager instance
            redis_client: Redis client instance
            
        Raises:
            ValueError: If parameters are invalid
        """
        try:
            if not llm_manager:
                raise ValueError("LLM manager instance is required")
            if not redis_client:
                raise ValueError("Redis client instance is required")
            
            #logger.info("Initializing ResearchConversationManager with enhanced security")
            self.llm_manager = llm_manager
            self.redis_client = redis_client
            self.active_conversations = {}
            #logger.info("ResearchConversationManager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ResearchConversationManager: {str(e)}")
            raise
    
    def _validate_session_id(self, session_id: str) -> None:
        """
        Validate session ID for security and safety.
        
        Args:
            session_id: Session ID to validate
            
        Raises:
            ValueError: If session ID is invalid
        """
        if not isinstance(session_id, str):
            raise ValueError("Session ID must be a string")
        
        if not session_id.strip():
            raise ValueError("Session ID cannot be empty")
        
        if len(session_id) > 100:  # Reasonable limit
            raise ValueError("Session ID too long (max 100 characters)")
        
        # Check for potentially dangerous patterns
        if re.search(r'[<>"\']', session_id):
            raise ValueError("Session ID contains invalid characters")
    
    def _validate_papers(self, papers: List[Dict]) -> None:
        """
        Validate papers list for security and safety.
        
        Args:
            papers: Papers list to validate
            
        Raises:
            ValueError: If papers list is invalid
        """
        if not isinstance(papers, list):
            raise ValueError("Papers must be a list")
        
        if len(papers) > 50:  # Reasonable limit
            raise ValueError("Too many papers (max 50)")
        
        for i, paper in enumerate(papers):
            if not isinstance(paper, dict):
                raise ValueError(f"Paper at index {i} must be a dictionary")
            
            # Validate paper ID if present
            if "id" in paper:
                paper_id = str(paper["id"])
                if len(paper_id) > 100:
                    raise ValueError(f"Paper ID at index {i} too long (max 100 characters)")
    
    def _validate_message_content(self, content: str) -> None:
        """
        Validate message content for security and safety.
        
        Args:
            content: Message content to validate
            
        Raises:
            ValueError: If content is invalid
        """
        if not isinstance(content, str):
            raise ValueError("Message content must be a string")
        
        if not content.strip():
            raise ValueError("Message content cannot be empty")
        
        if len(content) > 5000:  # Reasonable limit
            raise ValueError("Message content too long (max 5000 characters)")
        
        # Check for potentially dangerous content
        dangerous_patterns = [
            r'<script.*?>.*?</script>',  # Script tags
            r'javascript:',              # JavaScript protocol
            r'data:text/html',           # Data URLs
            r'vbscript:',                # VBScript
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                raise ValueError(f"Message content contains potentially dangerous patterns: {pattern}")
    
    def _sanitize_text(self, text: str, max_length: int = 5000) -> str:
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
    
    async def create_conversation(self, 
                                 session_id: str, 
                                 papers: List[Dict], 
                                 synthesis: Dict) -> str:
        """
        Create a new conversation with enhanced error handling and security.
        
        Args:
            session_id: Research session ID
            papers: List of papers to include in conversation
            synthesis: Research synthesis data
            
        Returns:
            Conversation ID
            
        Raises:
            ValueError: If inputs are invalid
            ConnectionError: If conversation creation fails
        """
        try:
            # Input validation and sanitization
            self._validate_session_id(session_id)
            self._validate_papers(papers)
            
            if not isinstance(synthesis, dict):
                raise ValueError("Synthesis must be a dictionary")
            
            sanitized_session_id = self._sanitize_text(session_id, max_length=100)
            
            #logger.info(f"Creating conversation for session: {sanitized_session_id}")
            
            conversation_id = f"conv_{sanitized_session_id}_{str(uuid.uuid4())[:8]}"
            
            # Create a research-focused system message
            system_message = self._create_system_message(papers, synthesis)
            
            # Initialize conversation history
            conversation = {
                "id": conversation_id,
                "session_id": sanitized_session_id,
                "created_at": _utc_timestamp(),
                "updated_at": _utc_timestamp(),
                "messages": [
                    {"role": "system", "content": system_message}
                ],
                "paper_ids": [p.get("id") for p in papers if "id" in p],
                "metadata": {
                    "paper_count": len(papers),
                    "synthesis_available": bool(synthesis)
                }
            }
            
            # Store in Redis and memory with error handling
            await self._store_conversation(conversation)
            self.active_conversations[conversation_id] = conversation
            
            #logger.info(f"Successfully created conversation: {conversation_id}")
            return conversation_id
            
        except ValueError as e:
            logger.error(f"Invalid input for conversation creation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise
    
    async def add_message(self, 
                         conversation_id: str, 
                         content: str, 
                         role: str = "user") -> Dict[str, Any]:
        """
        Add a message to the conversation with enhanced error handling and security.
        
        Args:
            conversation_id: Conversation ID
            content: Message content
            role: Message role (user/assistant)
            
        Returns:
            Response with AI reply
            
        Raises:
            ValueError: If inputs are invalid
            ConnectionError: If message processing fails
        """
        try:
            # Input validation and sanitization
            if not isinstance(conversation_id, str) or not conversation_id.strip():
                raise ValueError("Conversation ID must be a non-empty string")
            
            self._validate_message_content(content)
            
            if role not in ["user", "assistant"]:
                raise ValueError("Role must be 'user' or 'assistant'")
            
            sanitized_content = self._sanitize_text(content, max_length=5000)
            
            #logger.info(f"Adding message to conversation: {conversation_id[:20]}...")
            
            # Get conversation with error handling
            conversation = await self._get_conversation(conversation_id)
            if not conversation:
                return {"error": "Conversation not found"}
            
            # Add user message
            conversation["messages"].append({
                "role": role,
                "content": sanitized_content,
                "timestamp": _utc_timestamp()
            })
            
            # Format messages for LLM
            messages = conversation["messages"]
            
            # Generate response with retry logic
            try:
                response = await self._generate_response_with_retry(messages)
                
                # Add assistant response
                conversation["messages"].append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": _utc_timestamp()
                })
                
                # Update conversation
                conversation["updated_at"] = _utc_timestamp()
                await self._store_conversation(conversation)
                
                #logger.info(f"Successfully processed message for conversation: {conversation_id[:20]}...")
                return {
                    "response": response,
                    "conversation_id": conversation_id
                }
                
            except Exception as e:
                logger.error(f"Error generating response: {str(e)}")
                return {"error": f"Failed to generate response: {str(e)}"}
            
        except ValueError as e:
            logger.error(f"Invalid input for message addition: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_response_with_retry(self, messages: List[Dict], max_retries: int = 3) -> str:
        """
        Generate response with retry logic.
        
        Args:
            messages: Conversation messages
            max_retries: Maximum retry attempts
            
        Returns:
            Generated response
            
        Raises:
            ConnectionError: If all retries fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Use LLM manager for chat completion
                response = await self.llm_manager.generate_synthesis(
                    [{"content": msg["content"]} for msg in messages if msg["role"] != "system"],
                    " ".join([msg["content"] for msg in messages if msg["role"] != "system"])
                )
                
                if isinstance(response, dict) and "summary" in response:
                    return response["summary"]
                else:
                    return str(response)
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Response generation attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Short delay between retries
        
        # All retries failed
        logger.error(f"All response generation attempts failed")
        raise ConnectionError(f"Failed to generate response after {max_retries} attempts: {str(last_error)}")
    
    async def get_conversation_history(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get full conversation history with enhanced error handling and security.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation history
            
        Raises:
            ValueError: If conversation ID is invalid
        """
        try:
            # Input validation
            if not isinstance(conversation_id, str) or not conversation_id.strip():
                raise ValueError("Conversation ID must be a non-empty string")
            
            #logger.info(f"Retrieving conversation history: {conversation_id[:20]}...")
            
            conversation = await self._get_conversation(conversation_id)
            if not conversation:
                return {"error": "Conversation not found"}
                
            # Filter out system messages for display
            user_messages = [
                msg for msg in conversation["messages"] 
                if msg["role"] != "system"
            ]
            
            # Sanitize messages for security
            sanitized_messages = []
            for msg in user_messages:
                sanitized_msg = msg.copy()
                sanitized_msg["content"] = self._sanitize_text(msg["content"], max_length=5000)
                sanitized_messages.append(sanitized_msg)
            
            result = {
                "id": conversation_id,
                "messages": sanitized_messages,
                "created_at": conversation.get("created_at"),
                "updated_at": conversation.get("updated_at"),
                "metadata": conversation.get("metadata", {})
            }
            
            #logger.info(f"Successfully retrieved conversation history: {conversation_id[:20]}...")
            return result
            
        except ValueError as e:
            logger.error(f"Invalid input for conversation history: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return {"error": str(e)}
    
    def _create_system_message(self, papers: List[Dict], synthesis: Dict) -> str:
        """
        Create a detailed system message with research context and enhanced security.
        
        Args:
            papers: List of papers
            synthesis: Research synthesis
            
        Returns:
            System message
        """
        try:
            # Extract and sanitize paper summaries
            paper_summaries = []
            for i, paper in enumerate(papers, 1):
                if not isinstance(paper, dict):
                    continue
                
                title = self._sanitize_text(paper.get("title", "Untitled"), max_length=200)
                authors = ", ".join(paper.get("authors", [])) if isinstance(paper.get("authors"), list) else ""
                
                summary = f"Paper {i}: {title}"
                if authors:
                    summary += f" by {authors}"
                
                # Add key findings
                if "main_findings" in paper:
                    findings = paper["main_findings"]
                    if isinstance(findings, list):
                        summary += "\nMain findings:\n"
                        for j, finding in enumerate(findings[:5], 1):  # Limit to 5 findings
                            sanitized_finding = self._sanitize_text(str(finding), max_length=200)
                            summary += f"  {j}. {sanitized_finding}\n"
                    else:
                        sanitized_finding = self._sanitize_text(str(findings), max_length=200)
                        summary += f"\nMain finding: {sanitized_finding}\n"
                
                # Add methodology if available
                if "methodology" in paper:
                    methodology = self._sanitize_text(str(paper['methodology']), max_length=200)
                    summary += f"\nMethodology: {methodology}\n"
                    
                paper_summaries.append(summary)
            
            # Create system message
            separator = '\n\n'
            synthesis_text = self._sanitize_text(str(synthesis.get("synthesis", "No synthesis available")), max_length=2000)
            
            system_message = f"""You are a research assistant discussing a collection of academic papers on a specific topic.

You have analyzed these papers:

{'='*40}
{separator.join(paper_summaries)}
{'='*40}

Research synthesis:
{synthesis_text}

When answering questions:
1. Reference specific papers by title when drawing from their findings
2. Acknowledge contradictions or disagreements between papers when they exist
3. Clearly state when information is not covered in the papers analyzed
4. Provide nuanced, balanced perspectives that reflect the research literature
5. Suggest additional areas to explore when the user's questions go beyond the current papers

Maintain a scholarly, informative tone while being conversational and accessible.
"""     
            return system_message
            
        except Exception as e:
            logger.error(f"Error creating system message: {str(e)}")
            return "You are a research assistant. Please ask me about the research papers."
    
    async def _store_conversation(self, conversation: Dict) -> None:
        """
        Store conversation in Redis with enhanced error handling.
        
        Args:
            conversation: Conversation data to store
        """
        conversation_id = conversation["id"]
        
        try:
            # Store as JSON string with error handling
            conversation_json = json.dumps(conversation)
            
            await self.redis_client.set(
                f"conversation:{conversation_id}",
                conversation_json,
                ex=86400  # 24 hour expiration
            )
            
            # Update active conversations
            self.active_conversations[conversation_id] = conversation
            
            logger.debug(f"Stored conversation: {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error storing conversation {conversation_id}: {str(e)}")
            raise
    
    async def _get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Get conversation from memory or Redis with enhanced error handling.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation data or None
        """
        try:
            # Check memory first
            if conversation_id in self.active_conversations:
                return self.active_conversations[conversation_id]
                
            # Try Redis
            try:
                conversation_data = await self.redis_client.get(f"conversation:{conversation_id}")
                if conversation_data:
                    conversation = json.loads(conversation_data)
                    # Cache in memory
                    self.active_conversations[conversation_id] = conversation
                    return conversation
            except Exception as e:
                logger.warning(f"Error retrieving conversation from Redis: {str(e)}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the conversation manager.
        
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
            
            # Check Redis connection
            try:
                await self.redis_client.ping()
                health_status["components"]["redis"] = {"status": "healthy"}
            except Exception as e:
                health_status["components"]["redis"] = {"status": "error", "error": str(e)}
                health_status["status"] = "degraded"
            
            # Check active conversations
            active_count = len(self.active_conversations)
            health_status["components"]["active_conversations"] = {
                "status": "healthy",
                "count": active_count
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
    
    async def cleanup(self):
        """Cleanup resources with error handling."""
        try:
            # Clear active conversations
            self.active_conversations.clear()
            #logger.info("ResearchConversationManager cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")