import time
from collections import defaultdict, deque
from fastapi import HTTPException, Request


_requests: dict[str, deque[float]] = defaultdict(deque)


def client_key(request: Request, scope: str) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",", 1)[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    auth = request.headers.get("authorization", "")
    return f"{scope}:{ip}:{auth[:40]}"


def enforce_rate_limit(request: Request, scope: str, *, limit: int, window_seconds: int) -> None:
    now = time.time()
    key = client_key(request, scope)
    bucket = _requests[key]
    cutoff = now - window_seconds
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests. Please try again shortly.")
    bucket.append(now)
