import io
import json
from email.message import Message
from urllib.error import HTTPError

import pytest

from instant_translate.http_client import JsonHttpClient, ResponseTooLargeError


class _Response(io.BytesIO):
    def __init__(self, payload, headers=None):
        super().__init__(payload)
        self.headers = headers or Message()

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        self.close()


class _Opener:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def open(self, _request, timeout=None):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_response_body_is_bounded_before_json_parsing():
    client = JsonHttpClient(
        opener=_Opener([_Response(b"x" * 11)]),
        max_response_bytes=10,
    )
    with pytest.raises(ResponseTooLargeError):
        client.open_json("https://example.invalid")


def test_content_length_is_rejected_before_read():
    headers = Message()
    headers["Content-Length"] = "100"
    client = JsonHttpClient(
        opener=_Opener([_Response(b"{}", headers)]),
        max_response_bytes=10,
    )
    with pytest.raises(ResponseTooLargeError):
        client.open_json("https://example.invalid")


def test_retryable_http_status_is_retried(monkeypatch):
    monkeypatch.setattr(JsonHttpClient, "_retry_delay", lambda *_args: 0)
    headers = Message()
    error = HTTPError("https://example.invalid", 503, "unavailable", headers, None)
    opener = _Opener([error, _Response(json.dumps({"ok": True}).encode())])
    client = JsonHttpClient(opener=opener, max_attempts=2)
    assert client.open_json("https://example.invalid") == {"ok": True}
    assert opener.calls == 2
