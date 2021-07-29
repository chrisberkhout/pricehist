import re

from pricehist import sources


def test_formatted_includes_ecb():
    lines = sources.formatted().splitlines()
    assert any(re.match(r"ecb +European Central Bank", line) for line in lines)


def test_formatted_names_aligned():
    lines = sources.formatted().splitlines()
    offsets = [len(re.match(r"(\w+ +)[^ ]", line)[1]) for line in lines]
    first = offsets[0]
    assert first > 1
    assert all(offset == first for offset in offsets)
