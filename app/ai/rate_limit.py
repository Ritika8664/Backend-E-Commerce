import time
from collections import defaultdict, deque
from threading import Lock


RATE_LIMIT = 20
WINDOW_SECONDS = 60
_requests: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def consume_request(user_id: str) -> int | None:
    """Return retry-after seconds when this process-local limit is exceeded."""
    now = time.monotonic()
    cutoff = now - WINDOW_SECONDS
    with _lock:
        timestamps = _requests[user_id]
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()
        if len(timestamps) >= RATE_LIMIT:
            return max(1, int(WINDOW_SECONDS - (now - timestamps[0])))
        timestamps.append(now)
    return None
