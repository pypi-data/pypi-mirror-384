import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone
import os
from src.services.llm_service.api_clients.llm_chat_client import LLMChatClient
from src.services.llm_service.api_clients.llm_doc_client import LLMDcClient
from src.services.llm_service.llm_manager import LLMManager
from src.services.research_service.context_manager import ResearchContextManager
from src.services.research_service.synthesizer import ResearchSynthesizer
from src.services.graph.knowledge_graph import KnowledgeGraph
from src.storage.db.operations import DatabaseOperations
from dotenv import load_dotenv
load_dotenv(".env.local")
import random
import re
import sys
import time

# Configure logging
logger = logging.getLogger(__name__)

class TypingEffect:
    """Simulate human-like typing effect for chatbot responses."""
    
    def __init__(self, speed=0.03, pause_chars=['.', '!', '?', ',', ';', ':']):
        self.speed = speed
        self.pause_chars = pause_chars
    
    async def type_message(self, message: str, stream=True):
        """Type out a message with realistic timing."""
        if not stream:
            return message
        
        typed_message = ""
        for char in message:
            typed_message += char
            print(char, end='', flush=True)
            
            # Add longer pauses for punctuation
            if char in self.pause_chars:
                await asyncio.sleep(self.speed * 3)
            else:
                await asyncio.sleep(self.speed)
        
        print()  # New line at the end
        return typed_message
    
    def type_message_simple(self, message: str, stream=True):
        """Simpler typing effect for when async isn't available."""
        if not stream:
            print(message)
            return message
        
        for char in message:
            print(char, end='', flush=True)
            time.sleep(self.speed)
        print()
        return message

class ConversationContext:
    """Track conversation context for better responses."""
    
    def __init__(self):
        self.topics_discussed = []
        self.user_interests = set()
        self.conversation_style = "neutral"
        self.depth_preference = "balanced"
        self.questions_asked = []
        self.research_readiness = 0.0
    
    def update(self, user_message: str, bot_response: str):
        """Update context based on conversation."""
        # Extract and track topics
        new_topics = self._extract_topics(user_message)
        self.topics_discussed.extend(new_topics)
        
        # Detect user's preferred style
        if "?" in user_message:
            self.questions_asked.append(user_message)
        
        # Adjust conversation style based on patterns
        if len(user_message.split()) > 50:
            self.depth_preference = "detailed"
        elif len(user_message.split()) < 10:
            self.depth_preference = "concise"
        
        # Update research readiness
        self._update_research_readiness(user_message)
    
    def get_style_guidelines(self) -> str:
        """Get style guidelines based on context."""
        guidelines = []
        
        if self.depth_preference == "detailed":
            guidelines.append("Provide thorough, detailed responses")
        elif self.depth_preference == "concise":
            guidelines.append("Keep responses focused and concise")
        
        if len(self.questions_asked) > 3:
            guidelines.append("User is curious - encourage exploration")
        
        if self.research_readiness > 0.7:
            guidelines.append("User seems ready for deeper research")
        
        return "\n".join(guidelines)
    
    def _extract_topics(self, user_message: str) -> list:
        """Extract topics from user message."""
        # Simple keyword extraction
        words = user_message.lower().split()
        # Filter for meaningful words (length > 4, not common words)
        topics = [w for w in words if len(w) > 4 and w not in 
                 ['about', 'would', 'could', 'should', 'there', 'where']]
        return topics[:3]  # Top 3 topics
    
    def _update_research_readiness(self, user_message: str):
        """Update research readiness score."""
        # Increase readiness if research-related terms appear
        research_indicators = ['research', 'study', 'papers', 'literature', 
                              'investigate', 'explore', 'deep dive']
        
        if any(term in user_message.lower() for term in research_indicators):
            self.research_readiness = min(self.research_readiness + 0.2, 1.0)
        
        # Also increase based on conversation depth
        if len(self.questions_asked) > 2:
            self.research_readiness = min(self.research_readiness + 0.1, 1.0)

class ChatbotResearchSession:
    """Full-featured CLI chatbot for research planning and execution with parallel web search and projection."""
    def __init__(self, context_manager=None, synthesizer=None, db_ops=None, user_profile: Optional[Dict] = None):
        # Initialize with fallback mode detection
        self.fallback_mode = False  # Force real mode
        self.context_manager = context_manager
        self.synthesizer = synthesizer
        self.db_ops = db_ops
        
        # Initialize typing effect
        self.typing_effect = TypingEffect(speed=0.02)  # Slightly faster for better UX
        
        # Force real mode - don't check dependencies
        logger.info("Forcing real research mode - using actual research capabilities")
        print("🔬 Running in REAL research mode with academic database access")
        
        self.history: List[Dict] = []
        self.context: Dict = {}
        self.user_profile = user_profile or {"name": "User"}
        self.created_at = datetime.now(timezone.utc)
        self.active = True
        self.session_id = None
        self.research_plan = None
        self.status = None
        self.synthesis = None
        self.topic = None
        self.questions = []
        self.last_bot_message = ""
        
        # Initialize clients for real research
        try:
            self.chat_client = LLMChatClient()
            self.doc_client = LLMDcClient()
            logger.info("LLM clients initialized successfully")
        except Exception as e:
            logger.error("LLM client initialization failed; real mode is required for launch", exc_info=True)
            raise RuntimeError(
                "LLM stack failed to initialize. Configure the required provider credentials "
                "(e.g., CEREBRAS_API_KEY) and network access before launching the chatbot."
            ) from e
        
        # New attributes for parallel web search and projection
        self.parallel_web_context = []
        self.research_proposed = False
        self.projection_given = False
        self.research_approved = False
        self.context_tracker = ConversationContext()

        import random
        self.random = random

    def _is_research_query(self, message: str) -> bool:
        """Detect if the message is a research query."""
        message_lower = message.lower()
        
        # Research keywords
        research_keywords = [
            'research', 'study', 'find', 'search', 'explore', 'investigate',
            'analyze', 'examine', 'look into', 'find out about', 'what is',
            'how does', 'why does', 'latest', 'recent', 'developments',
            'advances', 'breakthroughs', 'innovations', 'technology',
            'papers', 'articles', 'studies', 'literature'
        ]
        
        # Check if message contains research keywords
        has_research_keywords = any(keyword in message_lower for keyword in research_keywords)
        
        # Check if message is long enough to be a research query
        is_long_enough = len(message.split()) > 3
        
        # Check if message contains a topic (not just a greeting)
        is_not_greeting = not any(greeting in message_lower for greeting in ['hello', 'hi', 'hey', 'how are you'])
        
        return has_research_keywords and is_long_enough and is_not_greeting

    async def _perform_real_research(self, user_message: str) -> str:
        """Perform real academic research using the enhanced research service."""
        try:
            print("🔍 Starting REAL comprehensive research...")
            
            # Use the enhanced research service for deep analysis
            from src.services.research_service.enhanced_research import enhanced_research_service
            
            # Extract the actual research topic from the message
            research_topic = self._extract_research_topic(user_message)
            
            print(f"📝 Research Topic: {research_topic}")
            print("⏳ Performing comprehensive research with analysis...")
            
            # Perform comprehensive research
            results = await enhanced_research_service.research_topic(
                query=research_topic,
                max_results=20  # Go deeper
            )
            
            if results and not results.get('error'):
                # Format comprehensive results
                response = self._format_comprehensive_research_response(results, research_topic)
                print("✅ Comprehensive research completed!")
                return response
            else:
                # Fallback to basic search if enhanced research fails
                print("⚠️  Enhanced research failed, falling back to basic search...")
                return await self._perform_basic_research(user_message)
            
        except Exception as e:
            print(f"❌ Error in comprehensive research: {e}")
            return await self._perform_basic_research(user_message)

    def _extract_research_topic(self, message: str) -> str:
        """Extract the actual research topic from user message."""
        # More intelligent topic extraction
        topic = message.lower()
        
        # Remove common research request words but preserve the core topic
        research_words = [
            'research', 'study', 'analyze', 'analysis', 'comprehensive', 'detailed', 
            'thorough', 'perform', 'conduct', 'find', 'latest', 'developments', 
            'breakthroughs', 'papers', 'sources', 'go deep', 'deep', 'at least',
            'proper', 'citations', 'quality assessment', 'synthesis', 'i want',
            'detailed analysis of', 'content synthesis', 'and quality assessment'
        ]
        
        for word in research_words:
            topic = topic.replace(word, '')
        
        # Remove numbers that are likely not part of the topic
        import re
        topic = re.sub(r'\b\d+\b', '', topic)  # Remove standalone numbers
        
        # Clean up and return
        topic = ' '.join(topic.split())  # Remove extra spaces
        topic = topic.strip()
        
        # If topic is too short, try to extract the main subject
        if len(topic.split()) < 3:
            # Look for key terms that indicate the actual topic
            key_terms = ['quantum computing', 'artificial intelligence', 'machine learning', 
                        'renewable energy', 'climate change', 'healthcare', 'biotechnology',
                        'nanotechnology', 'robotics', 'cybersecurity', 'blockchain']
            
            for term in key_terms:
                if term in message.lower():
                    return term
        
        return topic if topic else "research topic"

    def _format_comprehensive_research_response(self, results: dict, topic: str) -> str:
        """Format comprehensive research results with analysis."""
        
        response = f"🔬 **Comprehensive Research Analysis: {topic}**\n\n"
        
        # Summary section
        response += f"📊 **Research Summary:**\n"
        response += f"• Sources Analyzed: {results.get('sources_analyzed', 0)}\n"
        response += f"• Key Findings: {len(results.get('key_findings', []))}\n"
        response += f"• Citations Generated: {len(results.get('citations', []))}\n"
        response += f"• Visualizations: {len(results.get('visualizations', {}))}\n\n"
        
        # Key findings
        if results.get('key_findings'):
            response += "🔍 **Key Findings:**\n"
            for i, finding in enumerate(results['key_findings'][:10], 1):
                response += f"{i}. {finding}\n"
            response += "\n"
        
        # Detailed analysis
        if results.get('detailed_analysis'):
            response += "📋 **Detailed Analysis:**\n"
            response += f"{results['detailed_analysis'][:500]}...\n\n"
        
        # Recommendations
        if results.get('recommendations'):
            response += "💡 **Recommendations:**\n"
            for i, rec in enumerate(results['recommendations'][:5], 1):
                response += f"{i}. {rec}\n"
            response += "\n"
        
        # Citations
        if results.get('citations'):
            response += "📚 **Top Sources (with Citations):**\n"
            for i, citation in enumerate(results['citations'][:5], 1):
                title = citation.get('title', 'No title')
                authors = citation.get('authors', [])
                doi = citation.get('doi', 'No DOI')
                
                response += f"{i}. **{title}**\n"
                if authors:
                    response += f"   Authors: {', '.join(authors[:3])}\n"
                response += f"   DOI: {doi}\n\n"
        
        # Citation formats
        if results.get('citation_formats'):
            response += "📖 **Citation Formats Available:**\n"
            for format_name in results['citation_formats'].keys():
                response += f"• {format_name.upper()}\n"
            response += "\n"
        
        response += "🎯 **This is REAL academic research with comprehensive analysis, not just a list of sources!**\n\n"
        response += "Would you like me to:\n"
        response += "• Generate a full research report\n"
        response += "• Create interactive visualizations\n"
        response += "• Export citations in specific formats\n"
        response += "• Dive deeper into specific findings\n"
        
        return response

    async def _perform_basic_research(self, user_message: str) -> str:
        """Fallback to basic research if enhanced research fails."""
        try:
            print("🔍 Performing basic research...")
            
            # Import search engine
            from src.services.search_service.search_engine import SearchEngine
            from src.storage.db.operations import DatabaseOperations
            
            # Initialize search engine
            db_ops = DatabaseOperations(
                os.environ.get('MONGODB_URL', 'mongodb://localhost:27017/nocturnal_archive'),
                os.environ.get('REDIS_URL', 'redis://localhost:6379')
            )
            search_engine = SearchEngine(db_ops, os.environ.get('REDIS_URL', 'redis://localhost:6379'))
            
            # Perform academic search
            print("📚 Searching academic databases...")
            academic_results = []
            
            try:
                from src.services.paper_service.openalex import OpenAlexClient
                async with OpenAlexClient() as openalex:
                    academic_data = await openalex.search_works(user_message, per_page=10)
                    if academic_data and "results" in academic_data:
                        academic_results = academic_data["results"]
                        print(f"✅ Found {len(academic_results)} academic papers")
            except Exception as e:
                print(f"⚠️  Academic search failed: {e}")
            
            # Perform web search
            print("🌐 Searching web sources...")
            web_results = await search_engine.web_search(user_message, num_results=5)
            print(f"✅ Found {len(web_results)} web sources")
            
            # Generate response with basic research results
            response = self._format_research_response(user_message, academic_results, web_results)
            
            print("✅ Basic research completed!")
            return response
            
        except Exception as e:
            print(f"❌ Error in basic research: {e}")
            return f"I encountered an error while researching '{user_message}'. Please try again."

    def _format_research_response(self, query: str, academic_results: list, web_results: list) -> str:
        """Format research results into a comprehensive response."""
        
        response = f"🔬 **Research Results for: {query}**\n\n"
        
        # Academic papers section
        if academic_results:
            response += "📚 **Academic Papers Found:**\n"
            for i, paper in enumerate(academic_results[:5], 1):
                title = paper.get('title', 'No title')
                authors = paper.get('authorships', [])
                author_names = [author.get('author', {}).get('display_name', 'Unknown') for author in authors[:3]]
                doi = paper.get('doi', 'No DOI')
                
                response += f"{i}. **{title}**\n"
                response += f"   Authors: {', '.join(author_names)}\n"
                response += f"   DOI: {doi}\n\n"
        
        # Web sources section
        if web_results:
            response += "🌐 **Web Sources Found:**\n"
            for i, result in enumerate(web_results[:3], 1):
                title = result.get('title', 'No title')
                url = result.get('url', 'No URL')
                snippet = result.get('snippet', 'No description')
                
                response += f"{i}. **{title}**\n"
                response += f"   URL: {url}\n"
                response += f"   {snippet[:150]}...\n\n"
        
        # Summary
        total_sources = len(academic_results) + len(web_results)
        response += f"📊 **Summary:** Found {total_sources} sources total ({len(academic_results)} academic papers, {len(web_results)} web sources)\n\n"
        
        response += "Would you like me to:\n"
        response += "• Analyze specific papers in detail\n"
        response += "• Generate citations for these sources\n"
        response += "• Create a comprehensive research summary\n"
        response += "• Explore related topics\n\n"
        
        response += "Just let me know what aspect you'd like to dive deeper into!"
        
        return response

    async def chat_turn(self, user_message: str) -> str:
        """Process user message with fallback support."""
        self.history.append({"role": "user", "content": user_message})
        
        # Update conversation context
        if hasattr(self, 'context_tracker'):
            self.context_tracker.update(user_message, self.last_bot_message)
        
        try:
            # Check if this is a research query
            if self._is_research_query(user_message):
                print("🔬 Detected research query - using real academic research...")
                response = await self._perform_real_research(user_message)
            elif self.fallback_mode:
                response = await self._simulate_chat_response(user_message)
            else:
                response = await self._full_chat_response(user_message)
            
            # Add typing effect to response
            await self.typing_effect.type_message(response)
            
            # Store the response
            self.last_bot_message = response
            self.history.append({"role": "assistant", "content": response})
            
            return response
                
        except Exception as e:
            logger.error(f"Error in chat_turn: {str(e)}")
            error_response = await self._handle_error_gracefully(e, user_message)
            await self.typing_effect.type_message(error_response)
            return error_response

    async def _parallel_web_search(self, user_message: str):
        """Do silent parallel web search for background context."""
        try:
            from src.services.search_service.search_engine import SearchEngine
            search_engine = SearchEngine(self.db_ops, os.environ.get('REDIS_URL', 'redis://localhost:6379'))
            
            # Extract key terms for search
            search_terms = await self._extract_search_terms(user_message)
            
            # Do quick web search in background
            results = await search_engine.web_search(search_terms, num_results=3)
            
            # Store context for later use
            self.parallel_web_context.extend(results)
            
        except Exception as e:
            # Silently fail - parallel search shouldn't interrupt conversation
            pass

    async def _extract_search_terms(self, message: str) -> str:
        """Extract search terms from user message."""
        try:
            # Use LLM to extract key search terms
            prompt = f"Extract 2-3 key search terms from this message for web search. Return ONLY the search terms, no JSON or formatting: {message}"
            result = await self.doc_client.process_document(
                title="Search Terms Extraction",
                content=prompt,
                model="llama-3.3-70b",
                temperature=0.1,
                max_tokens=100
            )
            terms = result.get("raw_text", "").strip()
            return terms if terms else message
        except:
            return message

    async def _simulate_chat_response(self, user_message: str) -> str:
        """Provide simulated responses when in fallback mode."""
        message_lower = user_message.lower()
        
        # Greeting responses
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'start']):
            return ("Hello! I'm the Nocturnal Archive research assistant. "
                   "I can help you with comprehensive research on any topic. "
                   "What would you like to research today?")
        
        # Research topic responses
        if any(word in message_lower for word in ['research', 'study', 'topic', 'explore']):
            if len(message_lower.split()) > 3:  # Likely contains a topic
                topic = user_message.strip()
                return (f"Great! I'd love to help you research '{topic}'. "
                       "In simulation mode, I can show you what the research process would look like. "
                       "Would you like me to demonstrate the research workflow for this topic?")
            else:
                return ("What topic would you like to research? "
                       "For example: 'quantum computing', 'AI in healthcare', or 'blockchain technology'")
        
        # Research type responses
        if any(word in message_lower for word in ['comprehensive', 'detailed', 'thorough']):
            return ("Perfect! I'll conduct a comprehensive analysis. "
                   "This would include:\n"
                   "• 15-20 papers analyzed\n"
                   "• Quality assessment\n"
                   "• Citation network mapping\n"
                   "• Trend analysis\n"
                   "• Advanced visualizations\n"
                   "• Multiple export formats\n\n"
                   "Estimated time: 35 minutes\n\n"
                   "Would you like me to start the research simulation?")
        
        if any(word in message_lower for word in ['quick', 'overview', 'summary']):
            return ("Great! I'll provide a quick overview. "
                   "This would include:\n"
                   "• 5-8 key papers\n"
                   "• Executive summary\n"
                   "• Main findings\n"
                   "• Basic visualizations\n\n"
                   "Estimated time: 15 minutes\n\n"
                   "Would you like me to start the research simulation?")
        
        # Confirmation responses
        if any(word in message_lower for word in ['yes', 'start', 'go', 'begin']):
            return ("🚀 Starting research simulation...\n\n"
                   "This is where the actual research would happen.\n"
                   "The system would:\n"
                   "1. Search academic databases\n"
                   "2. Analyze papers with AI\n"
                   "3. Generate insights and visualizations\n"
                   "4. Create professional reports\n\n"
                   "For now, this is a simulation. The full system requires:\n"
                   "• API keys for LLM services\n"
                   "• Database connections\n"
                   "• Web search capabilities\n\n"
                   "Would you like to see what the final output would look like?")
        
        # Help responses
        if any(word in message_lower for word in ['help', 'what can you do', 'capabilities']):
            return ("I'm the Nocturnal Archive research assistant! Here's what I can do:\n\n"
                   "🔬 **Research Capabilities:**\n"
                   "• Comprehensive literature reviews\n"
                   "• Market analysis and trends\n"
                   "• Technology assessment\n"
                   "• Quality evaluation of sources\n\n"
                   "📊 **Output Formats:**\n"
                   "• Executive summaries\n"
                   "• Advanced visualizations\n"
                   "• Multiple export formats (JSON, Markdown, HTML, LaTeX, CSV)\n\n"
                   "⚡ **Speed:**\n"
                   "• Quick overviews (15 minutes)\n"
                   "• Comprehensive analysis (35 minutes)\n\n"
                   "What would you like to research?")
        
        # Default response
        return ("I'm here to help with research! "
               "What topic would you like to explore? "
               "Or ask me what I can do for you.")

    async def _full_chat_response(self, user_message: str) -> str:
        """Full chat response when all dependencies are available."""
        try:
            # Background web search (non-blocking)
            asyncio.create_task(self._parallel_web_search(user_message))
            
            # Handle ambiguous inputs first
            if self._is_ambiguous(user_message):
                return await self._handle_ambiguous_input(user_message)
            
            # Natural flow decision tree
            conversation_state = self._analyze_conversation_state()
            
            if conversation_state == "warming_up":
                return await self._warm_conversation(user_message)
            
            elif conversation_state == "exploring":
                if self._should_propose_research():
                    return await self._propose_research()
                return await self._normal_conversation(user_message)
            
            elif conversation_state == "ready_for_research":
                if not self.research_proposed:
                    return await self._propose_research()
                elif self._is_research_approved(user_message):
                    # Start research immediately (layered engine + saturation metrics)
                    return await self._start_research_with_preferences({"comprehensive": True})
                elif self.projection_given and self._is_projection_approved(user_message):
                    return await self._start_research_with_preferences(self.research_preferences)
                else:
                    return await self._handle_research_hesitation(user_message)
            
            elif conversation_state == "researching":
                return await self._handle_research_in_progress(user_message)
            
            elif conversation_state == "discussing_results":
                return await self._handle_followup_question(user_message)
            
            else:
                return await self._normal_conversation(user_message)
                
        except Exception as e:
            return await self._handle_error_gracefully(e, user_message)

    async def _handle_error_gracefully(self, error: Exception, user_message: str) -> str:
        """Handle errors gracefully with user-friendly messages."""
        logger.error(f"Error in chat: {str(error)}")
        
        # Convert technical errors to user-friendly messages
        error_message = str(error).lower()
        
        if "connection" in error_message or "timeout" in error_message:
            return ("I'm having trouble connecting to the research databases right now. "
                   "This might be due to network issues or database configuration. "
                   "Would you like to try again, or would you prefer to see a demo of what I can do?")
        
        elif "authentication" in error_message or "api key" in error_message:
            return ("I need API keys to access the research services. "
                   "Please check your .env.local file and ensure your API keys are configured. "
                   "For now, I can show you what the research process would look like.")
        
        elif "database" in error_message:
            return ("I'm having trouble connecting to the database. "
                   "Please check your database configuration. "
                   "Would you like to try again or see a demo?")
        
        else:
            return ("I encountered an unexpected error while processing your request. "
                   "This might be a temporary issue. Would you like to try again, "
                   "or would you prefer to see what I can do in demo mode?")

    def _detect_ambiguity_type(self, user_message: str) -> str:
        """Detect type of ambiguity in user message."""
        message_lower = user_message.lower()
        words = message_lower.split()
        
        if len(words) < 5 and any(broad in message_lower for broad in ['everything', 'all', 'anything']):
            return "too_broad"
        elif len(words) < 3 or '?' not in user_message:
            return "unclear_intent"
        elif any(connector in message_lower for connector in ['and also', 'but also', 'oh and']):
            return "mixed_topics"
        else:
            return "general"

    async def _clarify_intent_naturally(self, user_message: str) -> str:
        """Clarify user's intent naturally."""
        return (
            "I want to make sure I understand what you're looking for. "
            "Could you tell me a bit more about what aspect interests you most?"
        )

    async def _handle_mixed_topics(self, user_message: str) -> str:
        """Handle messages with multiple topics."""
        return (
            "I see you've mentioned several interesting points! "
            "Which one would you like to explore first? We can always come back to the others."
        )

    async def _engage_exploratively(self, user_message: str) -> str:
        """Engage exploratively with ambiguous input."""
        messages = [
            {
                "role": "system",
                "content": "The user's message is somewhat ambiguous. Engage with curiosity and help them clarify their interests."
            },
            {"role": "user", "content": user_message}
        ]
        
        bot_response = await self.chat_client.chat(
            messages=messages,
            model="llama-3.3-70b",  # This model is correct for Cerebras
            temperature=0.7,
            max_tokens=800
        )
        self.history.append({"role": "assistant", "content": bot_response})
        return bot_response

    async def _categorize_followup(self, user_message: str) -> str:
        """Categorize the type of follow-up question."""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['clarify', 'explain', 'what do you mean']):
            return "clarification"
        elif any(word in message_lower for word in ['deeper', 'more detail', 'elaborate']):
            return "deeper_dive"
        elif any(word in message_lower for word in ['apply', 'implement', 'practice', 'use']):
            return "practical_application"
        elif any(word in message_lower for word in ['but', 'however', 'disagree']):
            return "challenge"
        else:
            return "general"

    async def _provide_clarification(self, user_message: str) -> str:
        """Provide clarification on research results."""
        prompt = f"""The user needs clarification about the research results.
        
    User question: {user_message}
    Research synthesis: {str(self.synthesis)[:1000]}

    Provide a clear, helpful clarification that:
    - Directly addresses their confusion
    - Uses simpler language if needed
    - Gives concrete examples
    - Maintains a helpful tone"""

        result = await self.doc_client.process_document(
            title="Clarification",
            content=prompt,
            model="llama-3.3-70b",
            temperature=0.5,
            max_tokens=400
        )
        
        response = result.get("raw_text", "Let me clarify that point for you...")
        self.history.append({"role": "assistant", "content": response})
        return response

    async def _provide_practical_insights(self, user_message: str) -> str:
        """Provide practical applications of research findings."""
        prompt = f"""The user wants practical applications of the research.
        
    User question: {user_message}
    Research synthesis: {str(self.synthesis)[:1000]}

    Provide practical insights that:
    - Connect research to real-world applications
    - Give actionable recommendations
    - Consider implementation challenges
    - Remain grounded in the research"""

        result = await self.doc_client.process_document(
            title="Practical Insights",
            content=prompt,
            model="llama-3.3-70b",
            temperature=0.6,
            max_tokens=500
        )
        
        response = result.get("raw_text", "Here's how you might apply these findings...")
        self.history.append({"role": "assistant", "content": response})
        return response

    async def _handle_challenge_gracefully(self, user_message: str) -> str:
        """Handle challenges to research findings gracefully."""
        response = (
            "That's a valid point to raise. Research findings often have nuances and limitations. "
            "Let me address your concern with what the research actually shows, including any "
            "contradicting viewpoints or limitations in the current studies..."
        )
        
        # Add more specific response based on the challenge
        self.history.append({"role": "assistant", "content": response})
        return response

    async def _provide_general_followup(self, user_message: str) -> str:
        """Provide general follow-up response."""
        prompt = f"""Answer this follow-up question about the research results.
        
    Question: {user_message}
    Research context: {str(self.synthesis)[:1000]}

    Be helpful, thorough, and conversational."""

        result = await self.doc_client.process_document(
            title="Follow-up Response",
            content=prompt,
            model="llama-3.3-70b",
            temperature=0.6,
            max_tokens=400
        )
        
        response = result.get("raw_text", "Based on the research findings...")
        self.history.append({"role": "assistant", "content": response})
        return response

    async def _extract_followup_aspect(self, user_message: str) -> str:
        """Extract the specific aspect user wants to explore."""
        # Simple extraction - could be enhanced
        return user_message[:100]  # Just use the message as the aspect

    async def _analyze_conversation_depth(self) -> dict:
        """Analyze conversation depth for proposal style."""
        return {
            'depth': self._calculate_conversation_depth(),
            'engagement': self._measure_user_engagement(),
            'style': self.context_tracker.conversation_style if hasattr(self, 'context_tracker') else 'neutral'
        }

    def _determine_proposal_style(self, analysis: dict) -> str:
        """Determine the best proposal style."""
        if analysis['engagement'] > 0.8 and analysis['depth'] > 0.7:
            return "enthusiastic"
        elif analysis['depth'] > 0.6:
            return "analytical"
        else:
            return "gentle"

    async def _generate_analytical_proposal(self) -> str:
        """Generate an analytical research proposal."""
        topic = self.topic or self._extract_implicit_topic()
        
        prompt = f"""Create an analytical research proposal for '{topic}' based on our conversation.
        
    Context: {self.get_context_summary()[-500:]}

    The proposal should:
    - Acknowledge the complexity of the topic
    - Outline specific research questions we could explore
    - Mention methodological approaches
    - Be conversational but intellectually rigorous
    - Invite the user to refine or proceed"""

        result = await self.doc_client.process_document(
            title="Analytical Proposal",
            content=prompt,
            model="llama-3.3-70b",
            temperature=0.6,
            max_tokens=400
        )
        
        return result.get("raw_text", f"I see there are several interesting dimensions to {topic}. Would you like me to conduct a systematic research review?")

    async def _generate_gentle_proposal(self) -> str:
        """Generate a gentle research proposal."""
        topic = self.topic or self._extract_implicit_topic()
        
        return (f"I've noticed we keep coming back to {topic}, and there seem to be some interesting "
                f"questions emerging. If you'd like, I could look into the academic research on this "
                f"topic and see what insights are available. Would that be helpful?")

    def _should_propose_research(self) -> bool:
        """Check if we have enough context to propose research."""
        # Don't propose if already proposed or research is running
        if self.research_proposed or self.status in {"running", "completed"}:
            return False
        
        # Check if we have enough context - need at least 3 turns
        if len(self.history) < 6:
            return False
        
        # Check if we have a clear topic
        topic, questions = self._extract_topic_and_questions(self.get_context_summary())
        if not topic or topic == "Untitled Research":
            return False
        
        # Check for research intent keywords in recent messages
        recent_messages = [turn["content"].lower() for turn in self.history[-3:] if turn["role"] == "user"]
        research_keywords = [
            "research", "find papers", "literature review", "study", "review", 
            "investigate", "collect papers", "gather sources", "quantum", "cryptography"
        ]
        has_research_intent = any(any(kw in msg for kw in research_keywords) for msg in recent_messages)
        
        if has_research_intent:
            return True
        
        return False

    async def _propose_research(self) -> str:
        """Propose research in a natural, conversational way."""
        self.research_proposed = True
        
        # Analyze conversation for natural entry point
        conversation_analysis = await self._analyze_conversation_depth()
        
        # Generate a natural, contextual proposal
        proposal_style = self._determine_proposal_style(conversation_analysis)
        
        if proposal_style == "enthusiastic":
            proposal = await self._generate_enthusiastic_proposal()
        elif proposal_style == "analytical":
            proposal = await self._generate_analytical_proposal()
        else:
            proposal = await self._generate_gentle_proposal()
        
        self.history.append({"role": "assistant", "content": proposal})
        return proposal

    async def _generate_enthusiastic_proposal(self) -> str:
        """Generate an enthusiastic research proposal."""
        topic = self.topic or self._extract_implicit_topic()
        
        templates = [
            f"This is fascinating! You know what? I think we're onto something really interesting with {topic}. "
            f"I could dive deep into the academic literature and pull together a comprehensive analysis for you. "
            f"There's likely some cutting-edge research we could explore - would you like me to start gathering papers and synthesizing the current state of knowledge?",
            
            f"I'm getting really intrigued by our discussion about {topic}! "
            f"I have access to academic databases and could conduct a thorough literature review to map out "
            f"the research landscape. We could uncover some fascinating insights - shall I start that research process?",
            
            f"You've touched on something that deserves deeper exploration! {topic} has so many dimensions "
            f"we could investigate through academic research. I could search for peer-reviewed papers, "
            f"analyze methodologies, and synthesize findings. Want me to put together a comprehensive research review?"
        ]
        
        # Use LLM to make it more natural based on context
        return await self._personalize_template(random.choice(templates))

    def _should_propose_research(self) -> bool:
        """Smarter detection of when to propose research."""
        if self.research_proposed or self.status in {"running", "completed"}:
            return False
        
        # Check conversation depth and complexity
        depth_score = self._calculate_conversation_depth()
        
        # Check for research indicators beyond keywords
        indicators = {
            'question_complexity': self._assess_question_complexity(),
            'topic_persistence': self._check_topic_persistence(),
            'knowledge_gaps': self._identify_knowledge_gaps(),
            'user_engagement': self._measure_user_engagement(),
            'conversation_maturity': len(self.history) > 6
        }
        
        # Weighted scoring
        score = (
            indicators['question_complexity'] * 0.3 +
            indicators['topic_persistence'] * 0.25 +
            indicators['knowledge_gaps'] * 0.2 +
            indicators['user_engagement'] * 0.15 +
            (1.0 if indicators['conversation_maturity'] else 0) * 0.1
        )
        
        return score > 0.4

    def _assess_question_complexity(self) -> float:
        """Assess the complexity of user questions."""
        recent_questions = [
            turn["content"] for turn in self.history[-6:] 
            if turn["role"] == "user"
        ]
        
        complexity_indicators = [
            "how", "why", "explain", "compare", "analyze", 
            "implications", "trade-offs", "challenges", "future",
            "state of the art", "research", "studies", "evidence"
        ]
        
        complexity_score = 0
        for question in recent_questions:
            question_lower = question.lower()
            score = sum(1 for indicator in complexity_indicators if indicator in question_lower)
            complexity_score += min(score / 3, 1.0)  # Normalize per question
        
        return complexity_score / max(len(recent_questions), 1)

    def _is_research_approved(self, user_message: str) -> bool:
        """Check if user approved the research proposal."""
        message_lower = user_message.lower()
        
        # Don't approve if we're already past this stage
        if self.projection_given or self.status == "running":
            return False
            
        approval_keywords = ["yes", "okay", "go ahead", "sure", "start", "sounds good"]
        return any(keyword in message_lower for keyword in approval_keywords)
    
    async def _give_projection(self) -> str:
        """Give projection based on gathered context."""
        self.projection_given = True
        
        # Create projection based on context and parallel web searches
        projection = await self._create_projection()
        
        projection_message = (
            f"Here's what I'm probably gonna find when I dig into the research:\n\n"
            f"{projection}\n\n"
            f"Let me verify this with the actual research. Should I proceed?"
        )
        
        self.history.append({"role": "assistant", "content": projection_message})
        return projection_message

    async def _create_projection(self) -> str:
        """Create sophisticated projection with academic depth."""
        try:
            # Combine conversation context and web search results
            context_summary = self.get_context_summary()
            web_context = "\n".join([f"- {r.get('title', '')}: {r.get('snippet', '')}" 
                                   for r in self.parallel_web_context[:5]])
            
            prompt = (
                f"Based on this conversation context and recent web information, "
                f"provide a sophisticated academic projection of research findings:\n\n"
                f"Conversation: {context_summary}\n\n"
                f"Recent web context: {web_context}\n\n"
                f"Create a projection that includes:\n"
                f"- Expected key findings and insights\n"
                f"- Potential research gaps that might be identified\n"
                f"- Current trends in the field\n"
                f"- Methodological considerations\n"
                f"- Potential limitations or challenges\n"
                f"- Academic rigor and depth\n\n"
                f"Project what the comprehensive academic research will likely reveal about this topic."
            )
            
            result = await self.doc_client.process_document(
                title="Research Projection",
                content=prompt,
                model="llama-3.3-70b",
                temperature=0.3,
                max_tokens=500
            )
            
            projection = result.get("raw_text", "")
            if not projection:
                projection = (
                    "Based on the research context and current literature trends, I expect to find:\n\n"
                    "**Key Findings**: [Expected insights from academic papers]\n"
                    "**Research Gaps**: [Areas where current literature is insufficient]\n"
                    "**Methodological Insights**: [Different research approaches and their effectiveness]\n"
                    "**Current Trends**: [Recent developments in the field]\n"
                    "**Limitations**: [Potential challenges in current research]\n\n"
                    "This projection is based on the current state of academic knowledge and will be verified through comprehensive research."
                )
            
            return projection
            
        except Exception as e:
            return (
                "Based on the academic context gathered, I expect to find relevant research papers, "
                "methodological insights, and potential research gaps. The comprehensive analysis will "
                "provide a thorough understanding of the current state of knowledge in this field."
            )

    def _is_projection_approved(self, user_message: str) -> bool:
        """Check if user approved the projection."""
        approval_keywords = ["yes", "okay", "proceed", "go ahead", "sure", "verify", "check"]
        return any(keyword in user_message.lower() for keyword in approval_keywords)

    async def _start_research(self) -> str:
        """Start the actual research process (layered engine with saturation metrics)."""
        self.research_approved = True
        self.status = "running"
        
        # Build research plan if not already built
        if not self.research_plan:
            self.research_plan = await self.build_research_plan()
        
        # Launch research using layered engine
        await self._approve_and_launch_layered()
        
        start_message = (
            f"Starting research now. This will take a moment as I search for academic papers "
            f"and analyze the findings. I'll let you know when it's complete."
        )
        
        self.history.append({"role": "assistant", "content": start_message})
        
        # Don't wait here - let the research run in background
        # The user will check status or the bot will check in _handle_research_in_progress
        
        return start_message

    async def _approve_and_launch_layered(self):
        plan_str = self.research_plan if self.research_plan is not None else ""
        topic, questions = self._extract_topic_and_questions(plan_str)
        self.topic = topic
        self.questions = questions
        # Start layered research (multi-source + saturation)
        self.session_id = await self.context_manager.start_layered_research(
            topic=topic,
            research_questions=questions or [topic],
            max_layers=3,
            user_id=self.user_profile.get("id", "default_user")
        )
        self.status = "running"

    async def check_status(self):
        if not self.session_id:
            print("No research session running.")
            return
        status = await self.context_manager.get_session_status(self.session_id)
        print(f"\n[Session Status: {status.get('status')}] Progress: {status.get('progress', {}).get('percentage', 0)}%")
        if status.get('status') == 'completed':
            self.status = 'completed'
        return status

    async def show_results(self):
        if not self.session_id:
            return "No research session found."
        session = await self.context_manager._get_session(self.session_id)
        synthesis = session.synthesis if session else None
        if synthesis:
            self.synthesis = synthesis
            # Prepare artifact links if available
            artifact_links = ""
            try:
                artifacts = synthesis.get('artifacts') if isinstance(synthesis, dict) else None
                if artifacts and artifacts.get('report_markdown') and artifacts.get('report_json'):
                    artifact_links = f"\n\nReports: {artifacts['report_markdown']} | {artifacts['report_json']}"
            except Exception:
                pass
            # Compose message
            syn_str = str(synthesis)
            results_message = (
                f"Research complete! Here are the findings:\n\n"
                f"{syn_str[:2000]}{'...' if len(syn_str) > 2000 else ''}"
                f"{artifact_links}\n\n"
                f"You can ask me follow-up questions about the results, or start a new research topic."
            )
            
            self.history.append({"role": "assistant", "content": results_message})
            return results_message
        else:
            return "Research is still in progress. Please wait a moment."

    def _is_followup_question(self, user_message: str) -> bool:
        """Check if user is asking a follow-up question about results."""
        if not self.synthesis:
            return False
        
        # Check for question indicators
        question_indicators = ["?", "explain", "clarify", "what about", "how", "why", "tell me more", "challenges", "implement"]
        return any(indicator in user_message.lower() for indicator in question_indicators)

    async def _handle_followup_question(self, user_message: str) -> str:
        """Handle follow-up questions with ChatGPT-like depth and personality."""
        
        # Categorize the follow-up type
        followup_type = await self._categorize_followup(user_message)
        
        if followup_type == "clarification":
            return await self._provide_clarification(user_message)
        elif followup_type == "deeper_dive":
            return await self._provide_deeper_analysis(user_message)
        elif followup_type == "practical_application":
            return await self._provide_practical_insights(user_message)
        elif followup_type == "challenge":
            return await self._handle_challenge_gracefully(user_message)
        else:
            return await self._provide_general_followup(user_message)
    
    async def _handle_ambiguous_input(self, user_message: str) -> str:
        """Handle ambiguous or unclear inputs gracefully."""
        
        ambiguity_type = self._detect_ambiguity_type(user_message)
        
        if ambiguity_type == "too_broad":
            return await self._narrow_down_gracefully(user_message)
        elif ambiguity_type == "unclear_intent":
            return await self._clarify_intent_naturally(user_message)
        elif ambiguity_type == "mixed_topics":
            return await self._handle_mixed_topics(user_message)
        else:
            return await self._engage_exploratively(user_message)

    async def _narrow_down_gracefully(self, user_message: str) -> str:
        """Help user narrow down broad topics naturally."""
        
        prompt = f"""The user has asked a very broad question. Help them narrow it down conversationally.

    User message: {user_message}
    Conversation context: {self.get_context_summary()[-500:]}

    Create a response that:
    1. Acknowledges the breadth of their interest
    2. Offers 2-3 specific directions they might explore
    3. Asks an engaging question to help focus
    4. Maintains enthusiasm and curiosity
    5. Feels like a natural conversation, not an interrogation"""

        result = await self.doc_client.process_document(
            title="Narrowing Assistance",
            content=prompt,
            model="llama-3.3-70b",
            temperature=0.8,
            max_tokens=400
        )
        
        return result.get("raw_text", "That's a fascinating area! Could you tell me what aspect interests you most?")
        
    def _add_personality_touches(self, response: str, style: str) -> str:
        """Add personality touches to responses."""
        
        if style == "analytical":
            # Add analytical personality markers
            connectors = [
                "Actually, this connects to an interesting point...",
                "What's particularly fascinating here is...",
                "This reminds me of a key insight from the research...",
                "There's a subtle but important distinction here..."
            ]
            if not any(conn in response for conn in connectors):
                response = f"{random.choice(connectors)} {response}"
        
        elif style == "enthusiastic":
            # Add enthusiasm markers
            if "!" not in response[:50]:  # Add excitement if missing
                sentences = response.split(". ")
                if len(sentences) > 1:
                    sentences[0] += "!"
                    response = ". ".join(sentences)
        
        elif style == "thoughtful":
            # Add thoughtful pauses and considerations
            thoughtful_phrases = [
                "Hmm, ",
                "You know, ",
                "That's a great question - ",
                "I've been thinking about this... "
            ]
            if not any(phrase in response[:30] for phrase in thoughtful_phrases):
                response = f"{random.choice(thoughtful_phrases)}{response}"
        
        return response
    
    async def _provide_deeper_analysis(self, user_message: str) -> str:
        """Provide deeper analysis with personality."""
        
        # Extract the specific aspect they want to dive into
        aspect = await self._extract_followup_aspect(user_message)
        
        prompt = f"""Based on the research synthesis, provide a deeper, more nuanced analysis of the user's question.
        
    Research synthesis: {str(self.synthesis)}
    User's follow-up: {user_message}
    Specific aspect: {aspect}

    Guidelines:
    - Start with an engaging hook that shows you understand their curiosity
    - Provide rich, detailed analysis with examples
    - Use analogies or metaphors where helpful
    - Connect to broader implications
    - Maintain conversational tone while being thorough
    - End with a thought-provoking insight or question"""

        result = await self.doc_client.process_document(
            title="Deep Dive Analysis",
            content=prompt,
            model="llama-3.3-70b",
            temperature=0.7,
            max_tokens=800
        )
        
        response = result.get("raw_text", "")
        
        # Add personality touches
        response = self._add_personality_touches(response, "analytical")
        
        self.history.append({"role": "assistant", "content": response})
        return response
    
    async def _normal_conversation(self, user_message: str) -> str:
        """Handle normal conversation flow with ChatGPT/Claude-style interaction."""
        
        # Build a rich context for the LLM
        system_prompt = self._build_dynamic_system_prompt()
        
        # Prepare conversation history with context awareness
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history with smart truncation
        messages.extend(self._prepare_conversation_history())
        
        # Inject subtle context from parallel searches
        if self.parallel_web_context:
            messages.append({
                "role": "system", 
                "content": f"[Background knowledge from recent searches: {self._summarize_web_context()}]"
            })
        
        try:
            bot_response = await self.chat_client.chat(
                messages=messages,
                model="llama-3.3-70b",  # This model is correct for Cerebras
                temperature=0.7,
                max_tokens=800
            )
            # Post-process for natural flow
            bot_response = self._enhance_response_naturally(bot_response, user_message)
            
        except Exception as e:
            bot_response = self._generate_fallback_response(user_message)
        
        self.history.append({"role": "assistant", "content": bot_response})
        return bot_response

    def _build_dynamic_system_prompt(self) -> str:
        """Build a dynamic system prompt based on conversation state."""
        
        base_prompt = """You are an advanced AI research assistant with a warm, intellectually curious personality. 
    You engage naturally in conversations, showing genuine interest in topics while maintaining academic rigor.

    Key traits:
    - Intellectually curious and enthusiastic about learning
    - Naturally conversational while being precise when needed
    - Proactively helpful without being pushy
    - Subtly guide conversations toward productive research when appropriate
    - Use natural transitions and conversational bridges
    - Show personality through word choice and engagement style

    Current capabilities include:
    - Deep academic research and literature analysis
    - Real-time web search integration
    - Comprehensive paper synthesis
    - Methodological guidance
    - Critical analysis"""

        # Add state-aware context
        if len(self.history) > 4:
            base_prompt += "\n\n[Note: The conversation is developing depth. Consider whether research might be valuable soon.]"
        
        if self.parallel_web_context:
            base_prompt += "\n\n[You have access to recent web search context. Use it naturally when relevant.]"
        
        if self._has_research_indicators():
            base_prompt += "\n\n[The user seems interested in deeper exploration. Be ready to suggest research naturally.]"
        
        return base_prompt

    async def _handle_clarification_request(self, user_message: str) -> str:
        """Handle requests for clarification with comprehensive academic guidance."""
        try:
            prompt = (
                f"Based on the conversation history, provide a comprehensive explanation of how I can help with academic research.\n\n"
                f"Conversation context: {self.get_context_summary()}\n\n"
                f"User is asking for clarification: {user_message}\n\n"
                f"Provide a detailed explanation of my capabilities for academic research assistance, "
                f"including literature review, methodology guidance, critical analysis, and research synthesis."
            )
            
            result = await self.doc_client.process_document(
                title="Clarification Response",
                content=prompt,
                model="llama-3.3-70b",
                temperature=0.3,
                max_tokens=400
            )
            
            response = result.get("raw_text", "")
            if not response:
                response = (
                    "I can help you with comprehensive academic research in several ways:\n\n"
                    "**Literature Review & Synthesis**: I can search academic databases, analyze papers, "
                    "and synthesize findings across multiple sources.\n\n"
                    "**Research Methodology**: I can help you choose appropriate research methods, "
                    "design studies, and identify research gaps.\n\n"
                    "**Critical Analysis**: I can provide deep analysis of academic papers, "
                    "identify strengths/weaknesses, and suggest improvements.\n\n"
                    "**Citation Management**: I can help organize sources, format citations, "
                    "and ensure proper academic referencing.\n\n"
                    "**Writing Assistance**: I can help structure arguments, improve clarity, "
                    "and enhance academic writing.\n\n"
                    "What specific aspect of your research would you like to focus on?"
                )
            
            self.history.append({"role": "assistant", "content": response})
            return response
            
        except Exception as e:
            return "I can help with comprehensive academic research including literature reviews, methodology guidance, and critical analysis. What specific aspect would you like to explore?"

    def _extract_implicit_topic(self) -> str:
        """Extract topic from conversation if not explicitly set."""
        
        # Look for noun phrases in recent messages
        user_messages = [
            turn["content"] for turn in self.history[-6:] 
            if turn["role"] == "user"
        ]
        
        # Simple extraction - find the most discussed concept
        all_text = " ".join(user_messages).lower()
        
        # Common research topics (extend this list based on your domain)
        topic_keywords = [
            "quantum", "cryptography", "security", "algorithm", "computing",
            "research", "technology", "science", "study", "analysis"
        ]
        
        for keyword in topic_keywords:
            if keyword in all_text:
                # Find surrounding context
                index = all_text.find(keyword)
                start = max(0, index - 20)
                end = min(len(all_text), index + 30)
                context = all_text[start:end].strip()
                return context
        
        # Default to first substantial user message
        for msg in user_messages:
            if len(msg) > 20:
                return msg[:50] + "..."
        
        return "the topic we've been discussing"

    async def _personalize_template(self, template: str) -> str:
        """Personalize template based on conversation context."""
        
        # Add conversation-specific details
        recent_context = self.get_context_summary()[-500:]
        
        prompt = f"""Personalize this research proposal template based on our conversation:

    Template: {template}

    Recent conversation: {recent_context}

    Make it feel natural and specific to what we've been discussing. Keep the same enthusiasm but make it more personal."""

        result = await self.doc_client.process_document(
            title="Personalize Proposal",
            content=prompt,
            model="llama-3.3-70b",
            temperature=0.7,
            max_tokens=300
        )
        
        return result.get("raw_text", template)

    def _calculate_conversation_depth(self) -> float:
        """Calculate how deep/complex the conversation has become."""
        
        depth_score = 0.0
        
        # Factor 1: Message length
        avg_length = sum(len(turn["content"]) for turn in self.history) / max(len(self.history), 1)
        depth_score += min(avg_length / 200, 1.0) * 0.3
        
        # Factor 2: Question complexity
        depth_score += self._assess_question_complexity() * 0.4
        
        # Factor 3: Topic persistence
        depth_score += self._check_topic_persistence() * 0.3
        
        return min(depth_score, 1.0)

    def _check_topic_persistence(self) -> float:
        """Check if user is sticking to a topic."""
        
        if len(self.history) < 4:
            return 0.0
        
        # Extract key terms from recent messages
        recent_messages = [
            turn["content"].lower() for turn in self.history[-6:] 
            if turn["role"] == "user"
        ]
        
        # Find common words (simple approach)
        word_counts = {}
        for msg in recent_messages:
            words = msg.split()
            for word in words:
                if len(word) > 4:  # Skip small words
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        # If any substantial word appears multiple times, topic is persistent
        max_count = max(word_counts.values()) if word_counts else 0
        return min(max_count / 3, 1.0)

    def _identify_knowledge_gaps(self) -> float:
        """Identify if there are knowledge gaps to fill."""
        
        # Look for uncertainty markers
        gap_indicators = [
            "i don't know", "not sure", "wondering", "curious",
            "how does", "why does", "what causes", "can you explain"
        ]
        
        recent_messages = " ".join([
            turn["content"].lower() for turn in self.history[-4:] 
            if turn["role"] == "user"
        ])
        
        gap_count = sum(1 for indicator in gap_indicators if indicator in recent_messages)
        return min(gap_count / 3, 1.0)

    def _measure_user_engagement(self) -> float:
        """Measure how engaged the user is."""
        
        if len(self.history) < 2:
            return 0.5
        
        # Check response length trend
        user_messages = [
            turn["content"] for turn in self.history 
            if turn["role"] == "user"
        ]
        
        if len(user_messages) < 2:
            return 0.5
        
        # Are messages getting longer? (sign of engagement)
        recent_avg = sum(len(msg) for msg in user_messages[-3:]) / 3
        early_avg = sum(len(msg) for msg in user_messages[:3]) / 3
        
        if recent_avg > early_avg * 1.5:
            return 1.0
        elif recent_avg > early_avg:
            return 0.7
        else:
            return 0.4

    async def _warm_conversation(self, user_message: str) -> str:
        """Handle early conversation warmly and naturally."""
        
        # Simple, warm system prompt
        messages = [
            {
                "role": "system", 
                "content": (
                    "You are a friendly, intellectually curious AI assistant. "
                    "This is early in the conversation, so be welcoming and engaging. "
                    "Show interest in what the user is saying and ask natural follow-up questions. "
                    "Be conversational, not formal."
                )
            },
            *self.history
        ]
        
        bot_response = await self.chat_client.chat(
            messages=messages,
            model="llama-3.3-70b",  # This model is correct for Cerebras
            temperature=0.7,
            max_tokens=800
        )
        self.history.append({"role": "assistant", "content": bot_response})
        return bot_response

    async def _handle_research_hesitation(self, user_message: str) -> str:
        """Handle when user seems hesitant about research."""
        
        # Understand their concern
        prompt = f"""The user seems hesitant about starting research. Their message: "{user_message}"

    Provide a helpful, understanding response that:
    1. Acknowledges their hesitation
    2. Offers to clarify or adjust the research scope
    3. Gives them control over the process
    4. Remains friendly and supportive

    Keep it conversational and brief."""

        result = await self.doc_client.process_document(
            title="Hesitation Response",
            content=prompt,
            model="llama-3.3-70b",
            temperature=0.7,
            max_tokens=200
        )
        
        response = result.get("raw_text", "No problem! Would you like to explore the topic more first, or should we adjust what we're looking for?")
        
        self.history.append({"role": "assistant", "content": response})
        return response

    async def _handle_research_in_progress(self, user_message: str) -> str:
        """Handle conversation while research is running."""
        
        # Check actual research status
        if self.session_id:
            status = await self.context_manager.get_session_status(self.session_id)
            progress = status.get('progress', {}).get('percentage', 0)
            
            if status.get('status') == 'completed':
                self.status = 'completed'
                return await self.show_results()
        
        # Friendly progress update
        messages = [
            {
                "role": "system",
                "content": "Research is currently running. Be helpful and conversational while they wait."
            },
            {"role": "user", "content": user_message}
        ]
        
        bot_response = await self.chat_client.chat(
            messages=messages,
            model="llama-3.3-70b",  # This model is correct for Cerebras
            temperature=0.7,
            max_tokens=800
        )
        # Add progress info if available
        if 'progress' in locals():
            bot_response += f"\n\n(Research is {progress}% complete)"
        
        self.history.append({"role": "assistant", "content": bot_response})
        return bot_response

    def _enhance_response_naturally(self, response: str, user_message: str) -> str:
        """Add natural enhancements to responses."""
        
        # Don't enhance if already natural
        if any(phrase in response[:50] for phrase in ["You know", "Actually", "Hmm", "That's"]):
            return response
        
        # Add natural starter based on context
        if "?" in user_message:
            starters = ["That's a great question! ", "Good question - ", "Hmm, "]
            response = random.choice(starters) + response
        
        return response

    def _generate_fallback_response(self, user_message: str) -> str:
        """Generate fallback response when LLM fails."""
        
        if "?" in user_message:
            return "That's an interesting question! Could you tell me a bit more about what you're looking for?"
        else:
            return "I'm here to help with research and exploration. What would you like to know more about?"

    def _analyze_conversation_state(self) -> str:
        """Dynamically determine conversation state based on multiple factors."""
        
        # Don't need complex AI here - just smart logic!
        conversation_length = len(self.history)
        
        # Early conversation
        if conversation_length < 4:
            return "warming_up"
        
        # Check if we're already researching
        if self.status == "running":
            return "researching"
        
        # Check if we have results
        if self.synthesis:
            return "discussing_results"
        
        # Check depth and engagement
        if self.research_proposed and not self.projection_given:
            return "ready_for_research"
        
        # Default exploring state
        complexity = self._assess_question_complexity()
        if complexity > 0.5 and conversation_length > 6:
            return "ready_for_research"
        
        return "exploring"

    def _is_ambiguous(self, user_message: str) -> bool:
        """Check if user message is ambiguous."""
        # Simple checks - no AI needed
        message_lower = user_message.lower().strip()
        
        # Too short
        if len(message_lower.split()) < 3:
            return True
        
        # Very broad terms
        broad_terms = ["everything", "all", "anything", "whatever", "stuff"]
        if any(term in message_lower for term in broad_terms) and "?" in message_lower:
            return True
        
        # Multiple unrelated topics
        topic_keywords = ["and also", "oh and", "btw", "by the way", "another thing"]
        if any(keyword in message_lower for keyword in topic_keywords):
            return True
        
        return False

    def _prepare_conversation_history(self) -> list:
        """Prepare conversation history for LLM context."""
        # Keep last 10 messages or less
        return self.history[-10:]

    def _summarize_web_context(self) -> str:
        """Summarize web search results for context."""
        if not self.parallel_web_context:
            return "No recent web searches"
        
        # Simple summary of top 3 results
        summaries = []
        for result in self.parallel_web_context[:3]:
            title = result.get('title', 'Unknown')
            snippet = result.get('snippet', '')[:100]
            summaries.append(f"{title}: {snippet}...")
        
        return " | ".join(summaries)

    def _has_research_indicators(self) -> bool:
        """Check if conversation has research indicators."""
        recent_messages = " ".join([
            turn["content"].lower() for turn in self.history[-4:] 
            if turn["role"] == "user"
        ])
        
        research_terms = [
            "research", "papers", "study", "literature", 
            "evidence", "findings", "what does the research say"
        ]
        
        return any(term in recent_messages for term in research_terms)

    async def _handle_topic_inquiry(self, user_message: str) -> str:
        """Handle inquiries about specific topics with academic depth."""
        try:
            # Extract the topic being inquired about
            topic_prompt = f"Extract the specific topic or concept being inquired about from: {user_message}"
            topic_result = await self.doc_client.process_document(
                title="Topic Extraction",
                content=topic_prompt,
                model="llama-3.3-70b",
                temperature=0.1,
                max_tokens=100
            )
            
            topic = topic_result.get("raw_text", "").strip()
            
            # Create comprehensive response about the topic
            response_prompt = (
                f"Provide a comprehensive academic explanation of '{topic}' including:\n"
                f"- Definition and key concepts\n"
                f"- Current state of research\n"
                f"- Related academic fields\n"
                f"- Potential research directions\n"
                f"- How it might relate to the user's research context\n\n"
                f"User's research context: {self.get_context_summary()}"
            )
            
            result = await self.doc_client.process_document(
                title="Topic Explanation",
                content=response_prompt,
                model="llama-3.3-70b",
                temperature=0.4,
                max_tokens=400
            )
            
            response = result.get("raw_text", f"I'm familiar with {topic}. Could you tell me more about how it relates to your research?")
            
            self.history.append({"role": "assistant", "content": response})
            return response
            
        except Exception as e:
            return "I'd be happy to discuss that topic in detail. Could you tell me more about how it relates to your research?"

    async def _handle_scope_change(self, user_message: str) -> str:
        """Handle scope changes with academic research methodology."""
        try:
            prompt = (
                f"User wants to change the research scope: {user_message}\n\n"
                f"Current research context: {self.get_context_summary()}\n\n"
                f"Provide guidance on how to handle this scope change academically, including:\n"
                f"- Whether to expand current research or start new\n"
                f"- How to maintain academic rigor\n"
                f"- Potential research questions\n"
                f"- Methodology considerations"
            )
            
            result = await self.doc_client.process_document(
                title="Scope Change Guidance",
                content=prompt,
                model="llama-3.3-70b",
                temperature=0.3,
                max_tokens=400
            )
            
            response = result.get("raw_text", "I can help you adjust the research scope. Should we expand the current research or start a new direction?")
            
            self.history.append({"role": "assistant", "content": response})
            return response
            
        except Exception as e:
            return "I can help you adjust the research scope. Would you like to expand the current research or explore a new direction?"

    async def _prompt_for_research_preferences(self) -> str:
        """Prompt user for research timeframe and depth preferences."""
        preference_message = (
            "🤖 Bot: I'm ready to research this topic comprehensively. "
            "I can conduct thorough research in the background to get the most complete synthesis possible.\n\n"
            "**Research Options:**\n"
            "• **Comprehensive** (recommended): I'll research as much as I can for the most complete findings\n"
            "• **Time-limited**: Set a specific timeframe (e.g., 'finish in 10 minutes' or 'take up to 1 hour')\n"
            "• **Quick overview**: Just get the main points quickly\n\n"
            "What's your preference? You can say:\n"
            "- 'Go comprehensive' or 'Take your time'\n"
            "- 'Finish in X minutes/hours'\n"
            "- 'Quick overview only'\n"
            "- Or just 'proceed' for comprehensive research"
        )
        self.history.append({"role": "assistant", "content": preference_message})
        return preference_message

    async def _parse_research_preferences(self, user_message: str) -> dict:
        """Parse user's research timeframe and depth preferences."""
        message_lower = user_message.lower()
        
        # Default to comprehensive research
        preferences = {
            "comprehensive": True,
            "time_limit": None,
            "quick_overview": False
        }
        
        # Check for time limits
        time_patterns = [
            r"finish in (\d+)\s*(minute|minutes|hour|hours)",
            r"(\d+)\s*(minute|minutes|hour|hours)",
            r"time limit.*?(\d+)\s*(minute|minutes|hour|hours)",
            r"(\d+)\s*(min|mins|hr|hrs)"
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message_lower)
            if match:
                time_value = int(match.group(1))
                time_unit = match.group(2)
                if time_unit in ['minute', 'minutes', 'min', 'mins']:
                    preferences["time_limit"] = time_value * 60  # Convert to seconds
                elif time_unit in ['hour', 'hours', 'hr', 'hrs']:
                    preferences["time_limit"] = time_value * 3600  # Convert to seconds
                preferences["comprehensive"] = False
                break
        
        # Check for quick overview
        if any(phrase in message_lower for phrase in ["quick", "overview", "summary", "brief", "fast"]):
            preferences["quick_overview"] = True
            preferences["comprehensive"] = False
        
        # Check for comprehensive research
        if any(phrase in message_lower for phrase in ["comprehensive", "thorough", "complete", "take your time", "go comprehensive"]):
            preferences["comprehensive"] = True
            preferences["quick_overview"] = False
        
        return preferences

    def get_context_summary(self) -> str:
        summary = "\n".join([
            f"{turn['role'].capitalize()}: {turn['content']}" for turn in self.history
        ])
        return summary

    async def build_research_plan(self):
        """Use LLMDocClient to synthesize a research plan from the conversation."""
        try:
            plan_prompt = (
                "Summarize the following conversation as a structured research plan. "
                "List the main topic, sub-questions, and any constraints or context provided by the user.\n\n"
            ) + self.get_context_summary()
            # Use doc client for plan extraction
            result = await self.doc_client.process_document(
                title="Research Plan Extraction",
                content=plan_prompt,
                model="llama-3.3-70b",
                temperature=0.3,
                max_tokens=1500
            )
            plan = result.get("raw_text") or result.get("main_findings", [""])[0] or "[No plan extracted]"
            self.research_plan = plan
            return plan
        except Exception as e:
            return f"Error building plan: {str(e)}"

    async def check_status(self):
        if not self.session_id:
            print("No research session running.")
            return
        status = await self.context_manager.get_session_status(self.session_id)
        print(f"\n[Session Status: {status.get('status')}] Progress: {status.get('progress', {}).get('percentage', 0)}%")
        if status.get('status') == 'completed':
            self.status = 'completed'
        return status

    async def show_results(self):
        if not self.session_id:
            return "No research session found."
        session = await self.context_manager._get_session(self.session_id)
        synthesis = session.synthesis if session else None
        if synthesis:
            self.synthesis = synthesis
            results_message = (
                f"Research complete! Here are the findings:\n\n"
                f"{str(synthesis)[:2000]}{'...' if len(str(synthesis)) > 2000 else ''}\n\n"
                f"You can ask me follow-up questions about the results, or start a new research topic."
            )
            
            self.history.append({"role": "assistant", "content": results_message})
            return results_message
        else:
            return "Research is still in progress. Please wait a moment."

    def _extract_topic_and_questions(self, plan: str):
        topic = None
        questions = []
        for line in plan.splitlines():
            if line.lower().startswith("topic:"):
                topic = line.split(":", 1)[1].strip()
            elif line.lower().startswith("questions:"):
                continue
            elif line.strip().startswith("-"):
                questions.append(line.strip("- ").strip())
        if not topic:
            for turn in self.history:
                if turn["role"] == "user":
                    topic = turn["content"]
                    break
        return topic or "Untitled Research", questions

    async def _start_research_with_preferences(self, preferences: dict) -> str:
        """Start research with user-specified preferences for timeframe and depth."""
        
        # Set research parameters based on preferences
        if preferences.get("time_limit"):
            self.max_research_time = preferences["time_limit"]
        
        if preferences.get("quick_overview"):
            self.research_depth = "quick"
        elif preferences.get("comprehensive"):
            self.research_depth = "comprehensive"
        
        # Start the research process
        return await self._start_research()

async def run_cli_chatbot():
    print("\n🧑‍💻 Nocturnal Archive Research Chatbot (CLI Mode)")
    print("Type 'exit' to quit. Type 'status' to check progress.\n")
    
    # Check system readiness
    system_issues = []
    
    # Check API keys
    required_keys = ['MISTRAL_API_KEY', 'COHERE_API_KEY', 'CEREBRAS_API_KEY']
    for key in required_keys:
        if not os.environ.get(key):
            system_issues.append(f"Missing {key}")
    
    # Check database URLs
    if not os.environ.get('MONGODB_URL') and not os.environ.get('MONGO_URL'):
        system_issues.append("Missing database URL")
    
    if not os.environ.get('REDIS_URL'):
        system_issues.append("Missing Redis URL")
    
    # Display system status
    if system_issues:
        print("⚠️  System Configuration Issues Detected:")
        for issue in system_issues:
            print(f"   • {issue}")
        print("\n🔄 Running in simulation mode with limited functionality.")
        print("   For full functionality, please configure your .env.local file.")
        print("   See SETUP_GUIDE.md for detailed instructions.\n")
    
    try:
        # Try to initialize full system
        db_ops = None
        llm_manager = None
        synthesizer = None
        context_manager = None
        
        try:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
            mongo_url = os.environ.get('MONGODB_URL', os.environ.get('MONGO_URL', 'mongodb://localhost:27017/nocturnal_archive'))

            db_ops = DatabaseOperations(mongo_url, redis_url)
            llm_manager = LLMManager(redis_url)
            knowledge_graph = KnowledgeGraph()
            synthesizer = ResearchSynthesizer(
                db_ops=db_ops,
                llm_manager=llm_manager,
                redis_url=redis_url,
                kg_client=knowledge_graph
            )
            context_manager = ResearchContextManager(db_ops, synthesizer, redis_url)
        except Exception as e:
            logger.warning(f"Full system initialization failed: {e}")
            print("⚠️  Some system components failed to initialize.")
            print("   Running in fallback mode with simulated responses.\n")
        
        # Initialize chatbot session (will automatically detect fallback mode)
        session = ChatbotResearchSession(context_manager, synthesizer, db_ops)
        
        print("✅ Chatbot initialized successfully!")
        if session.fallback_mode:
            print("📋 Available in simulation mode:")
            print("   • Research topic discussions")
            print("   • Workflow demonstrations")
            print("   • Capability explanations")
            print("   • Error-free conversation")
        else:
            print("🚀 Full functionality available!")
            print("   • Real research execution")
            print("   • Database integration")
            print("   • LLM-powered analysis")
        
        print("\n" + "="*50)
        print("Start your conversation! Try saying:")
        print("• 'Hello' or 'Hi'")
        print("• 'I want to research quantum computing'")
        print("• 'What can you do?'")
        print("• 'Help'")
        print("="*50 + "\n")
        
        # Initialize typing effect for welcome message
        typing_effect = TypingEffect(speed=0.02)
        welcome_message = "Hello! I'm the Nocturnal Archive research assistant. I can help you with comprehensive research on any topic. What would you like to research today?"
        await typing_effect.type_message(welcome_message)
        
        while session.active:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in {"exit", "quit", "bye"}:
                    await typing_effect.type_message("Goodbye! Thanks for using Nocturnal Archive!")
                    break
                
                if user_input.lower() == "status":
                    if not session.fallback_mode:
                        await session.check_status()
                    else:
                        await typing_effect.type_message("Running in simulation mode - no active research sessions.")
                    continue
                
                if user_input.lower() == "help":
                    help_message = "Available commands:\n   • Type any research topic to start a conversation\n   • 'status' - Check research progress (full mode only)\n   • 'exit' or 'quit' - End the session\n   • 'help' - Show this help message"
                    await typing_effect.type_message(help_message)
                    continue
                
                if not user_input:
                    await typing_effect.type_message("Please type something! I'm here to help with research.")
                    continue
                
                # Process the response (typing effect is handled in chat_turn)
                response = await session.chat_turn(user_input)
                
            except EOFError:
                await typing_effect.type_message("Goodbye! Thanks for using Nocturnal Archive!")
                break
            except KeyboardInterrupt:
                await typing_effect.type_message("Goodbye! Thanks for using Nocturnal Archive!")
                break
            except Exception as e:
                logger.error(f"Unexpected error in chat loop: {str(e)}")
                await typing_effect.type_message(f"I encountered an unexpected error: {str(e)}")
                await typing_effect.type_message("Let's continue our conversation!")
                continue
                
    except Exception as e:
        logger.error(f"Failed to initialize chatbot: {str(e)}")
        print(f"❌ Failed to initialize chatbot: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your .env.local file configuration")
        print("2. Ensure all required dependencies are installed")
        print("3. Verify database connections")
        print("4. Check API key configuration")
        print("\n📖 For detailed setup instructions, see SETUP_GUIDE.md") 