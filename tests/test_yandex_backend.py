import io
import json
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

from instant_translate.backends.yandex import YandexBackend
from instant_translate.models import TranslationRequest
from instant_translate.text_chunking import smart_split


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        self.close()


class _FakeTranslateOpener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def open(self, request_or_url, timeout=None):
        self.requests.append(request_or_url)
        payload = self.responses.pop(0)
        return _FakeResponse(json.dumps(payload).encode("utf-8"))


class _HttpErrorOpener:
    def __init__(self, code):
        self.code = code

    def open(self, request_or_url, timeout=None):
        url = getattr(request_or_url, "full_url", request_or_url)
        raise HTTPError(url, self.code, "request failed", {}, None)


def _request(text="hi", source="auto", target="en"):
    return TranslationRequest("yandex", source, target, text)


def test_successful_translation():
    backend = YandexBackend(
        opener=_FakeTranslateOpener(
            [{"code": 200, "lang": "en-ru", "text": ["привет"]}]
        )
    )

    result = backend.translate(_request(source="auto", target="ru"))

    assert result.translation == "привет"
    assert result.detected_language == "en"
    assert result.ok
    assert result.error_message is None


def test_known_error_code_sets_friendly_message():
    backend = YandexBackend(opener=_FakeTranslateOpener([{"code": 403}]))

    result = backend.translate(_request())

    assert not result.ok
    assert result.error_message == YandexBackend.ERRORS[403]


def test_multiple_chunks_are_concatenated():
    long_text = ("word " * 300).strip()
    expected_chunks = len(smart_split(long_text, 500, 550))
    opener = _FakeTranslateOpener(
        [
            {"code": 200, "lang": "en-ru", "text": [f"part{i} "]}
            for i in range(expected_chunks)
        ]
    )
    backend = YandexBackend(opener=opener)

    result = backend.translate(_request(long_text))

    assert result.translation == "".join(f"part{i} " for i in range(expected_chunks))
    assert result.ok


def test_request_posts_text_with_fixed_ios_credentials_and_no_double_suffix():
    opener = _FakeTranslateOpener(
        [{"code": 200, "lang": "en-en", "text": ["hi"]}]
    )
    backend = YandexBackend(opener=opener)

    backend.translate(_request())

    request = opener.requests[0]
    params = parse_qs(urlparse(request.full_url).query)
    body = parse_qs(request.data.decode("utf-8"))
    assert request.get_method() == "POST"
    assert params["id"] == [YandexBackend.ID]
    assert params["sid"] == [YandexBackend.SID]
    assert params["ucid"] == [YandexBackend.UCID]
    assert "text" not in params
    assert body["text"] == ["hi"]
    assert f"{YandexBackend.SID}-0-0" == YandexBackend.ID


def test_http_error_sets_specific_message():
    backend = YandexBackend(opener=_HttpErrorOpener(405))

    result = backend.translate(_request())

    assert not result.ok
    assert result.error_message == YandexBackend.ERRORS[405]
