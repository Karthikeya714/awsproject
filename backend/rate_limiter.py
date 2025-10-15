"""Rate limiting implementation using token bucket algorithm."""
import time
from typing import Dict
from threading import Lock
from backend.models import RateLimitConfig


class RateLimiter:
    """Token bucket rate limiter for per-user request limiting."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.buckets: Dict[str, Dict[str, float]] = {}
        self.lock = Lock()
    
    def is_allowed(self, user_id: str) -> bool:
        """
        Check if request is allowed for user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if request is allowed
        """
        with self.lock:
            now = time.time()
            
            if user_id not in self.buckets:
                self.buckets[user_id] = {
                    'tokens': self.config.bucket_size,
                    'last_update': now
                }
            
            bucket = self.buckets[user_id]
            
            # Refill tokens
            time_passed = now - bucket['last_update']
            bucket['tokens'] = min(
                self.config.bucket_size,
                bucket['tokens'] + time_passed * self.config.refill_rate
            )
            bucket['last_update'] = now
            
            # Check if request is allowed
            if bucket['tokens'] >= 1.0:
                bucket['tokens'] -= 1.0
                return True
            
            return False
    
    def get_remaining(self, user_id: str) -> int:
        """
        Get remaining tokens for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of remaining tokens
        """
        with self.lock:
            if user_id not in self.buckets:
                return self.config.bucket_size
            
            now = time.time()
            bucket = self.buckets[user_id]
            
            time_passed = now - bucket['last_update']
            tokens = min(
                self.config.bucket_size,
                bucket['tokens'] + time_passed * self.config.refill_rate
            )
            
            return int(tokens)
    
    def reset(self, user_id: str):
        """Reset rate limit for user."""
        with self.lock:
            if user_id in self.buckets:
                del self.buckets[user_id]
