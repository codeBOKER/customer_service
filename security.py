from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, Request

from config import TELEGRAM_WEBHOOK_SECRET

FAILED_ATTEMPT_WINDOW_SECONDS = 60
FAILED_ATTEMPT_LIMIT = 5
BLOCK_DURATION_SECONDS = 15 * 60

_failed_secret_attempts: dict[str, deque[float]] = defaultdict(deque)
_blocked_clients: dict[str, float] = {}


def _get_client_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def _prune_failed_attempts(client_key: str, now: float) -> deque[float]:
    attempts = _failed_secret_attempts[client_key]
    cutoff = now - FAILED_ATTEMPT_WINDOW_SECONDS
    while attempts and attempts[0] < cutoff:
        attempts.popleft()
    return attempts


def validate_webhook_secret(request: Request, secret_header: str | None) -> None:
    if not TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret is not configured")

    client_key = _get_client_key(request)
    now = monotonic()
    blocked_until = _blocked_clients.get(client_key)
    if blocked_until and now < blocked_until:
        raise HTTPException(status_code=429, detail="Too many requests")

    if secret_header != TELEGRAM_WEBHOOK_SECRET:
        attempts = _prune_failed_attempts(client_key, now)
        attempts.append(now)
        if len(attempts) >= FAILED_ATTEMPT_LIMIT:
            _blocked_clients[client_key] = now + BLOCK_DURATION_SECONDS
            attempts.clear()
        raise HTTPException(status_code=403, detail="Forbidden")

    _blocked_clients.pop(client_key, None)
    _failed_secret_attempts.pop(client_key, None)
