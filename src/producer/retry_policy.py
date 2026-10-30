import random
from dataclasses import dataclass

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 5
    base_delay_seconds: float = 4.0
    max_delay_seconds: float = 32.0
    deadline_seconds: float = 90.0

    def is_retryable_status(self, status_code: int) -> bool:
        return status_code in RETRYABLE_STATUS_CODES

    def can_retry(self, attempt: int, elapsed_seconds: float, next_delay_seconds: float) -> bool:
        has_attempts_left = attempt < self.max_attempts
        fits_deadline = elapsed_seconds + next_delay_seconds < self.deadline_seconds
        return has_attempts_left and fits_deadline

    def delay_before_next_attempt(self, attempt: int) -> float:
        exponential_delay = self.base_delay_seconds * 2 ** (attempt - 1)
        capped_delay = min(exponential_delay, self.max_delay_seconds)
        half_delay = capped_delay / 2
        return half_delay + random.uniform(0, half_delay)