"""Rate limiting middleware for the web server."""

import time
from collections import defaultdict

class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests=30, window_seconds=60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests = defaultdict(list)

    def is_allowed(self, key):
        """Check if request is allowed for the given key."""
        now = time.time()
        cutoff = now - self.window
        # Clean old entries
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        if len(self._requests[key]) >= self.max_requests:
            return False
        self._requests[key].append(now)
        return True

    def remaining(self, key):
        """Get remaining requests for key."""
        now = time.time()
        cutoff = now - self.window
        recent = [t for t in self._requests[key] if t > cutoff]
        return max(0, self.max_requests - len(recent))

    def reset(self, key=None):
        """Reset rate limit for key or all keys."""
        if key:
            self._requests.pop(key, None)
        else:
            self._requests.clear()


# Global rate limiters
_message_limiter = RateLimiter(max_requests=30, window_seconds=60)  # 30 msgs/min
_upload_limiter = RateLimiter(max_requests=10, window_seconds=60)   # 10 uploads/min


def check_message_limit(sid):
    """Check if message is allowed for session."""
    return _message_limiter.is_allowed(sid)


def check_upload_limit(sid):
    """Check if upload is allowed for session."""
    return _upload_limiter.is_allowed(sid)


def get_remaining(sid):
    """Get remaining message quota."""
    return _message_limiter.remaining(sid)
