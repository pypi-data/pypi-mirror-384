"""Research service package exposing conversation and synthesis utilities."""

from .chatbot import ResearchChatbot
from .citation_manager import CitationManager
from .context_manager import ResearchContextManager
from .conversation_manager import ResearchConversationManager
from .critical_paper_detector import CriticalPaperDetector
from .enhanced_research import EnhancedResearchPipeline
from .enhanced_synthesizer import EnhancedSynthesizer
from .query_generator import ResearchQueryGenerator
from .synthesizer import ResearchSynthesizer

__all__ = [
    "ResearchChatbot",
    "CitationManager",
    "ResearchContextManager",
    "ResearchConversationManager",
    "CriticalPaperDetector",
    "EnhancedResearchPipeline",
    "EnhancedSynthesizer",
    "ResearchQueryGenerator",
    "ResearchSynthesizer",
]
