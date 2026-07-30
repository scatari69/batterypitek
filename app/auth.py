"""Аутентификация админ-панели: хэш пароля (PBKDF2) и подписанные токены (HMAC)."""

import base64
import hashlib
import hmac
import secrets
import time

_ITERATIONS = 200_000


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _ITERATIONS)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if not stored or "$" not in stored:
        return False
    salt, _ = stored.split("$", 1)
    try:
        return hmac.compare_digest(hash_password(password, salt), stored)
    except ValueError:
        return False


def make_token(sign_key: str, ttl_days: int = 30) -> str:
    exp = int(time.time()) + ttl_days * 86400
    payload = base64.urlsafe_b64encode(str(exp).encode()).decode().rstrip("=")
    sig = hmac.new(sign_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_token(token: str, sign_key: str) -> bool:
    if not token or "." not in token:
        return False
    payload, sig = token.split(".", 1)
    expected = hmac.new(sign_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return False
    try:
        pad = "=" * (-len(payload) % 4)
        exp = int(base64.urlsafe_b64decode(payload + pad).decode())
    except (ValueError, UnicodeDecodeError):
        return False
    return time.time() < exp
