"""
Basic authentication manager for testing
"""
from typing import Dict, Any, Optional


class AuthManager:
    """Basic auth manager for testing purposes"""
    
    def __init__(self):
        self.test_user = {
            "id": "test_user_123",
            "username": "test_user",
            "email": "test@example.com"
        }
    
    async def get_current_user(self) -> Dict[str, Any]:
        """Return test user for testing"""
        return self.test_user
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify token (test implementation)"""
        if token == "test_token":
            return self.test_user
        return None
    
    def create_token(self, user_data: Dict[str, Any]) -> str:
        """Create token (test implementation)"""
        return "test_token"


# Global instance
auth_manager = AuthManager()