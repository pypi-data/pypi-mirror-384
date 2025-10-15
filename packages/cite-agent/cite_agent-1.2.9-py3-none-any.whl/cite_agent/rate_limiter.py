"""
Rate Limiting Configuration based on Groq API limits
Implements per-user rate limiting with soft degradation
"""

from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path


@dataclass
class RateLimitConfig:
    """Rate limit configuration for different tiers"""
    # Groq limits for llama-3.3-70b-versatile (Free tier)
    rpm: int  # Requests per minute
    rpd: int  # Requests per day
    tpm: int  # Tokens per minute
    tpd: int  # Tokens per day
    
    # Our API limits (on top of Groq)
    archive_api_per_day: int
    finsight_api_per_day: int
    web_search_per_day: int  # -1 = unlimited


# Rate limit tiers
RATE_LIMITS = {
    'free': RateLimitConfig(
        # Groq limits (llama-3.3-70b-versatile)
        rpm=30,
        rpd=1000,
        tpm=12000,
        tpd=100000,
        # Our limits
        archive_api_per_day=10,
        finsight_api_per_day=20,
        web_search_per_day=-1  # unlimited
    ),
    'basic': RateLimitConfig(
        # Groq limits (same, user pays for our value-add)
        rpm=30,
        rpd=1000,
        tpm=12000,
        tpd=100000,
        # Our limits (300 NTD/month)
        archive_api_per_day=25,
        finsight_api_per_day=50,
        web_search_per_day=-1  # unlimited
    ),
    'pro': RateLimitConfig(
        # Groq limits (same)
        rpm=30,
        rpd=1000,
        tpm=12000,
        tpd=100000,
        # Our limits (600 NTD/month)
        archive_api_per_day=-1,  # unlimited
        finsight_api_per_day=-1,  # unlimited
        web_search_per_day=-1  # unlimited
    )
}


class RateLimiter:
    """
    Track and enforce rate limits per user
    Implements soft degradation when limits are hit
    """
    
    def __init__(self, user_id: str, tier: str = 'basic', storage_dir: Optional[Path] = None):
        self.user_id = user_id
        self.tier = tier
        self.config = RATE_LIMITS.get(tier, RATE_LIMITS['basic'])
        
        # Storage for rate limit tracking
        self.storage_dir = storage_dir or Path.home() / ".nocturnal_archive" / "rate_limits"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / f"{user_id}_limits.json"
        
        # Load existing limits
        self.limits = self._load_limits()
    
    def _load_limits(self) -> Dict:
        """Load rate limit data from storage"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    # Check if data is from today
                    if data.get('date') == datetime.now().strftime('%Y-%m-%d'):
                        return data
            except Exception:
                pass
        
        # Return fresh limits
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'groq_requests': 0,
            'groq_tokens': 0,
            'archive_api': 0,
            'finsight_api': 0,
            'web_search': 0,
            'last_request_time': None
        }
    
    def _save_limits(self):
        """Save rate limit data to storage"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.limits, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save rate limits: {e}")
    
    def _reset_if_needed(self):
        """Reset limits if it's a new day"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        if self.limits.get('date') != current_date:
            self.limits = {
                'date': current_date,
                'groq_requests': 0,
                'groq_tokens': 0,
                'archive_api': 0,
                'finsight_api': 0,
                'web_search': 0,
                'last_request_time': None
            }
            self._save_limits()
    
    def can_make_request(self, api_name: str = 'groq', tokens: int = 0) -> tuple[bool, Optional[str]]:
        """
        Check if user can make a request
        
        Returns:
            (can_proceed, error_message)
        """
        self._reset_if_needed()
        
        if api_name == 'groq':
            # Check Groq limits
            if self.limits['groq_requests'] >= self.config.rpd:
                return False, f"Daily Groq request limit reached ({self.config.rpd} requests/day)"
            
            if self.limits['groq_tokens'] + tokens > self.config.tpd:
                return False, f"Daily Groq token limit reached ({self.config.tpd} tokens/day)"
            
            # Check RPM (requests per minute)
            if self.limits.get('last_request_time'):
                last_time = datetime.fromisoformat(self.limits['last_request_time'])
                if datetime.now() - last_time < timedelta(seconds=2):  # Simple RPM approximation
                    return False, "Rate limit: Please wait a moment before making another request"
        
        elif api_name == 'archive_api':
            if self.config.archive_api_per_day == -1:
                return True, None  # Unlimited
            if self.limits['archive_api'] >= self.config.archive_api_per_day:
                return False, f"Daily Archive API limit reached ({self.config.archive_api_per_day} queries/day)"
        
        elif api_name == 'finsight_api':
            if self.config.finsight_api_per_day == -1:
                return True, None  # Unlimited
            if self.limits['finsight_api'] >= self.config.finsight_api_per_day:
                return False, f"Daily FinSight API limit reached ({self.config.finsight_api_per_day} queries/day)"
        
        elif api_name == 'web_search':
            if self.config.web_search_per_day == -1:
                return True, None  # Unlimited
            if self.limits['web_search'] >= self.config.web_search_per_day:
                return False, f"Daily web search limit reached"
        
        return True, None
    
    def record_request(self, api_name: str = 'groq', tokens: int = 0):
        """Record a request"""
        self._reset_if_needed()
        
        if api_name == 'groq':
            self.limits['groq_requests'] += 1
            self.limits['groq_tokens'] += tokens
            self.limits['last_request_time'] = datetime.now().isoformat()
        elif api_name == 'archive_api':
            self.limits['archive_api'] += 1
        elif api_name == 'finsight_api':
            self.limits['finsight_api'] += 1
        elif api_name == 'web_search':
            self.limits['web_search'] += 1
        
        self._save_limits()
    
    def get_remaining(self, api_name: str = 'groq') -> int:
        """Get remaining requests for an API"""
        self._reset_if_needed()
        
        if api_name == 'groq':
            return max(0, self.config.rpd - self.limits['groq_requests'])
        elif api_name == 'archive_api':
            if self.config.archive_api_per_day == -1:
                return -1  # Unlimited
            return max(0, self.config.archive_api_per_day - self.limits['archive_api'])
        elif api_name == 'finsight_api':
            if self.config.finsight_api_per_day == -1:
                return -1  # Unlimited
            return max(0, self.config.finsight_api_per_day - self.limits['finsight_api'])
        elif api_name == 'web_search':
            return -1  # Unlimited for now
        
        return 0
    
    def get_status_message(self) -> str:
        """Get human-readable status of limits"""
        self._reset_if_needed()
        
        lines = []
        lines.append(f"**Rate Limit Status** (Tier: {self.tier.upper()})")
        lines.append("")
        
        # Groq limits
        groq_remaining = self.get_remaining('groq')
        lines.append(f"• Groq Requests: {self.limits['groq_requests']}/{self.config.rpd} used ({groq_remaining} remaining)")
        lines.append(f"• Groq Tokens: {self.limits['groq_tokens']}/{self.config.tpd} used")
        lines.append("")
        
        # API limits
        archive_remaining = self.get_remaining('archive_api')
        if self.config.archive_api_per_day == -1:
            lines.append("• Archive API: Unlimited ✓")
        else:
            lines.append(f"• Archive API: {self.limits['archive_api']}/{self.config.archive_api_per_day} used ({archive_remaining} remaining)")
        
        finsight_remaining = self.get_remaining('finsight_api')
        if self.config.finsight_api_per_day == -1:
            lines.append("• FinSight API: Unlimited ✓")
        else:
            lines.append(f"• FinSight API: {self.limits['finsight_api']}/{self.config.finsight_api_per_day} used ({finsight_remaining} remaining)")
        
        lines.append("• Web Search: Unlimited ✓")
        
        return "\n".join(lines)
    
    def get_available_capabilities(self) -> list[str]:
        """Get list of what's still available when rate limited"""
        capabilities = []
        
        if self.can_make_request('web_search')[0]:
            capabilities.append("Web searches (unlimited)")
        
        if self.can_make_request('archive_api')[0]:
            archive_remaining = self.get_remaining('archive_api')
            if archive_remaining == -1:
                capabilities.append("Academic paper search (unlimited)")
            else:
                capabilities.append(f"Academic paper search ({archive_remaining} remaining today)")
        
        if self.can_make_request('finsight_api')[0]:
            finsight_remaining = self.get_remaining('finsight_api')
            if finsight_remaining == -1:
                capabilities.append("Financial data queries (unlimited)")
            else:
                capabilities.append(f"Financial data queries ({finsight_remaining} remaining today)")
        
        # Always available
        capabilities.append("Local data analysis (unlimited)")
        capabilities.append("File operations and conversation")
        
        return capabilities


# Quick test function
def test_rate_limiter():
    """Test the rate limiter"""
    limiter = RateLimiter("test_user", "basic")
    
    print("Testing Rate Limiter")
    print("=" * 70)
    print(limiter.get_status_message())
    print("\n")
    
    # Test making requests
    print("Making 5 Groq requests...")
    for i in range(5):
        can_proceed, error = limiter.can_make_request('groq', tokens=100)
        if can_proceed:
            limiter.record_request('groq', tokens=100)
            print(f"  Request {i+1}: ✓")
        else:
            print(f"  Request {i+1}: ✗ {error}")
    
    print("\n")
    print(limiter.get_status_message())
    
    print("\n\nAvailable capabilities:")
    for cap in limiter.get_available_capabilities():
        print(f"  • {cap}")


if __name__ == "__main__":
    test_rate_limiter()
