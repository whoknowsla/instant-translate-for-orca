import threading

from instant_translate.coordinator import LatestRequestCoordinator
from instant_translate.models import TranslationRequest, TranslationResult


def _request(text):
    return TranslationRequest("google", "auto", "en", text)


def test_latest_request_replaces_pending_and_stale_result_is_marked():
    first_started = threading.Event()
    done = threading.Event()
    completions = []

    def execute(request, cancel_event):
        if request.text == "first":
            first_started.set()
            cancel_event.wait(2)
        return TranslationResult(request.text, "en")

    def on_done(request_id, request, result, is_latest):
        completions.append((request_id, request.text, result.translation, is_latest))
        if request.text == "third":
            done.set()

    coordinator = LatestRequestCoordinator(execute, on_done)
    try:
        assert coordinator.submit(_request("first")) == 1
        assert first_started.wait(1)
        assert coordinator.submit(_request("second")) == 2
        assert coordinator.submit(_request("third")) == 3
        assert done.wait(2)
    finally:
        coordinator.close()

    assert [item[1] for item in completions] == ["first", "third"]
    assert completions[0][-1] is False
    assert completions[1][-1] is True


def test_supersede_marks_active_result_stale():
    started = threading.Event()
    done = threading.Event()
    latest_flags = []

    def execute(_request, cancel_event):
        started.set()
        cancel_event.wait(2)
        return TranslationResult.cancelled_result()

    def on_done(_request_id, _request, _result, is_latest):
        latest_flags.append(is_latest)
        done.set()

    coordinator = LatestRequestCoordinator(execute, on_done)
    try:
        coordinator.submit(_request("network"))
        assert started.wait(1)
        coordinator.supersede()
        assert done.wait(2)
    finally:
        coordinator.close()
    assert latest_flags == [False]
