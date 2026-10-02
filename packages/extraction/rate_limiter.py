from __future__ import annotations

import time


class TokenBucketRateLimiter:
    """Client-side token bucket rate limiter and daily cap tracker."""

    def __init__(self, rate_per_minute: int = 60, daily_cap: int = 1000) -> None:
        self.capacity = float(rate_per_minute)
        self.fill_rate = float(rate_per_minute) / 60.0
        self.tokens = float(rate_per_minute)
        self.last_update = time.time()
        self.daily_cap = daily_cap
        self.daily_count = 0
        self.last_day = time.strftime("%Y-%m-%d")

    def _reset_day_if_needed(self) -> None:
        current_day = time.strftime("%Y-%m-%d")
        if current_day != self.last_day:
            self.last_day = current_day
            self.daily_count = 0

    def allow_request(self) -> bool:
        self._reset_day_if_needed()
        if self.daily_count >= self.daily_cap:
            return False

        now = time.time()
        delta = now - self.last_update
        self.last_update = now
        self.tokens = min(self.capacity, self.tokens + delta * self.fill_rate)

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            self.daily_count += 1
            return True
        return False


class CircuitBreaker:
    """Circuit breaker to avoid hammering failing providers."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout_sec: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_state_change = time.time()

    def can_execute(self) -> bool:
        now = time.time()
        if self.state == "OPEN":
            if now - self.last_state_change > self.recovery_timeout_sec:
                self.state = "HALF_OPEN"
                self.last_state_change = now
                return True
            return False
        return True

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_state_change = time.time()
