import time
from fastapi import Request, HTTPException
from collections import defaultdict
from threading import Lock

class SimpleRateLimiter:
    def __init__(self, limits=5, window_seconds=60):
        self.limits = limits
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.lock = Lock()

    def check_rate_limit(self, request: Request, identifier: str):
        now = time.time()
        with self.lock:
            # Clean up old requests
            self.requests[identifier] = [req_time for req_time in self.requests[identifier] if now - req_time < self.window_seconds]
            
            if len(self.requests[identifier]) >= self.limits:
                raise HTTPException(status_code=429, detail="Too Many Requests. Please try again later.")
                
            self.requests[identifier].append(now)

# Instantiate a global rate limiter for payments
payment_rate_limiter = SimpleRateLimiter(limits=5, window_seconds=60)
