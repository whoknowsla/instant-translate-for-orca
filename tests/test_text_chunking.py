from instant_translate.text_chunking import smart_split


def test_short_text_returned_unchanged():
    assert smart_split("hello world", 500, 550) == ["hello world"]


def test_splits_at_whitespace_within_range():
    text = "a" * 10 + " " + "b" * 10
    chunks = smart_split(text, 5, 15)
    assert chunks == ["a" * 10 + " ", "b" * 10]


def test_force_splits_with_no_whitespace_in_range():
    text = "a" * 20
    chunks = smart_split(text, 5, 10)
    assert chunks == ["a" * 10, "a" * 10]
    assert "".join(chunks) == text


def test_splits_on_newline_and_tab_and_nbsp():
    for ws in ("\n", "\t", "\xa0"):
        text = "a" * 6 + ws + "b" * 6
        chunks = smart_split(text, 5, 10)
        assert chunks[0] == "a" * 6 + ws
        assert "".join(chunks) == text


def test_normalizes_crlf_before_splitting():
    text = "a" * 6 + "\r\n" + "b" * 6
    chunks = smart_split(text, 5, 10)
    assert "\r" not in "".join(chunks)


def test_reassembly_matches_original_for_long_text():
    text = ("word " * 200).strip()
    chunks = smart_split(text, 50, 60)
    assert len(chunks) > 1
    assert "".join(chunks) == text.replace("\r\n", "\n").replace("\r", "\n")
