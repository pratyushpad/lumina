"""Client-key derivation for rate limiting.

X-Forwarded-For is client-appendable, so the trust boundary matters: only the
last TRUSTED_PROXY_HOPS entries were added by infrastructure we control. Getting
this wrong lets a client forge its own rate-limit key.
"""
from unittest.mock import patch

from starlette.datastructures import Headers

from app.middleware import rate_limit as rl


class FakeRequest:
    def __init__(self, headers: dict, client_host: str = "9.9.9.9"):
        self.headers = Headers(headers)

        class _Client:
            host = client_host

        self.client = _Client()


def test_one_trusted_hop_uses_rightmost_entry():
    # Attacker prepends 6.6.6.6; the platform proxy appends the address it saw.
    req = FakeRequest({"x-forwarded-for": "6.6.6.6, 1.2.3.4"})
    with patch.object(rl.settings, "TRUSTED_PROXY_HOPS", 1):
        assert rl.client_ip(req) == "1.2.3.4"


def test_spoofed_left_entries_are_ignored():
    req = FakeRequest({"x-forwarded-for": "1.1.1.1, 2.2.2.2, 3.3.3.3"})
    with patch.object(rl.settings, "TRUSTED_PROXY_HOPS", 1):
        assert rl.client_ip(req) == "3.3.3.3"


def test_zero_hops_ignores_xff_and_uses_socket_peer():
    req = FakeRequest({"x-forwarded-for": "6.6.6.6"}, client_host="9.9.9.9")
    with patch.object(rl.settings, "TRUSTED_PROXY_HOPS", 0):
        assert rl.client_ip(req) == "9.9.9.9"


def test_hops_longer_than_header_clamps_to_leftmost():
    # A short/forged header must never index past the list into a client value.
    req = FakeRequest({"x-forwarded-for": "4.4.4.4"})
    with patch.object(rl.settings, "TRUSTED_PROXY_HOPS", 5):
        assert rl.client_ip(req) == "4.4.4.4"


def test_owner_token_keys_per_user():
    req = FakeRequest({"x-owner-token": "abc123", "x-forwarded-for": "1.2.3.4"})
    with patch.object(rl.settings, "TRUSTED_PROXY_HOPS", 1):
        assert rl.client_key(req) == "owner:abc123"


def test_missing_token_falls_back_to_trusted_ip():
    req = FakeRequest({"x-forwarded-for": "1.2.3.4"})
    with patch.object(rl.settings, "TRUSTED_PROXY_HOPS", 1):
        assert rl.client_key(req) == "ip:1.2.3.4"
