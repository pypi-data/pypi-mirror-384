"""
Main services package for AI services layer
Provides unified access to all service components
"""

# Import all major service classes for easy access
from .llm_service.llm_manager import LLMManager
from .research_service.enhanced_research import EnhancedResearchService  
from .context_manager.advanced_context import AdvancedContextManager
from .tool_framework.tool_manager import ToolManager
from .auth_service.auth_manager import auth_manager

# Service registry for dependency injection
SERVICE_REGISTRY = {}

def register_service(name: str, service_instance):
    """Register a service instance in the global registry"""
    SERVICE_REGISTRY[name] = service_instance

def get_service(name: str):
    """Get a service instance from the registry"""
    return SERVICE_REGISTRY.get(name)

def initialize_services(config: dict = None):
    """Initialize all core services with configuration"""
    config = config or {}
    
    # Initialize services (with minimal config for testing)
    services = {}
    
    try:
        # LLM Manager (needs redis_url but we'll handle gracefully)
        redis_url = config.get('redis_url', 'redis://localhost:6379')
        llm_manager = LLMManager(redis_url=redis_url)
        services['llm_manager'] = llm_manager
        register_service('llm_manager', llm_manager)
    except Exception as e:
        # Graceful fallback for testing
        print(f"LLM Manager initialization skipped: {e}")
    
    try:
        # Research Service
        research_service = EnhancedResearchService()
        services['research_service'] = research_service
        register_service('research_service', research_service)
    except Exception as e:
        print(f"Research Service initialization skipped: {e}")
    
    try:
        # Context Manager  
        context_manager = AdvancedContextManager()
        services['context_manager'] = context_manager
        register_service('context_manager', context_manager)
    except Exception as e:
        print(f"Context Manager initialization skipped: {e}")
    
    try:
        # Tool Manager
        tool_manager = ToolManager()
        services['tool_manager'] = tool_manager
        register_service('tool_manager', tool_manager)
    except Exception as e:
        print(f"Tool Manager initialization skipped: {e}")
    
    return services

class ServiceLayer:
    """Unified service layer for easy access to all AI services"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.services = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize all services"""
        if self._initialized:
            return
            
        self.services = initialize_services(self.config)
        self._initialized = True
    
    @property
    def llm_manager(self) -> LLMManager:
        """Get LLM Manager service"""
        return self.services.get('llm_manager')
    
    @property 
    def research_service(self) -> EnhancedResearchService:
        """Get Research service"""
        return self.services.get('research_service')
    
    @property
    def context_manager(self) -> AdvancedContextManager:
        """Get Context Manager service"""
        return self.services.get('context_manager')
    
    @property
    def tool_manager(self) -> ToolManager:
        """Get Tool Manager service"""
        return self.services.get('tool_manager')
    
    def get_health_status(self) -> dict:
        """Get health status of all services"""
        status = {
            "services_initialized": self._initialized,
            "total_services": len(self.services),
            "available_services": list(self.services.keys())
        }
        return status

# Global service layer instance
_service_layer = None

def get_service_layer(config: dict = None) -> ServiceLayer:
    """Get the global service layer instance"""
    global _service_layer
    if _service_layer is None:
        _service_layer = ServiceLayer(config)
    return _service_layer

# Export key classes and functions
__all__ = [
    'LLMManager',
    'EnhancedResearchService', 
    'AdvancedContextManager',
    'ToolManager',
    'ServiceLayer',
    'get_service_layer',
    'initialize_services',
    'auth_manager'
]