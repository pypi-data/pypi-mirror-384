import base64
import pytest

from spotlighting.defenses import (
    delimit_content,
    datamark_content,
    encode_content_base64,
    encode_hex,
    encode_layered,
    Spotlighter,
)

def test_delimit_content_default():
    s = "hello world"
    assert delimit_content(s) == "«hello world»"

def test_datamark_content_no_whitespace():
    """Tests that datamark is a no-op on strings without whitespace."""
    s = "nospaces"
    assert datamark_content(s) == "nospaces"

def test_datamark_content_custom_marker():
    s = "one two   three"
    # replace whitespace sequences with custom marker
    assert datamark_content(s, marker="@") == "one@two@three"

def test_encode_content_base64_roundtrip():
    s = "radar"
    encoded = encode_content_base64(s)
    decoded = base64.b64decode(encoded).decode("utf-8")
    assert decoded == s

def test_encode_hex_roundtrip():
    s = "radar"
    encoded = encode_hex(s)
    decoded = bytes.fromhex(encoded).decode("utf-8")
    assert decoded == s

def test_encode_layered_roundtrip():
    s = "radar"
    layered = encode_layered(s)
    # First hex-decode to get base64, then base64-decode to get original
    b64 = bytes.fromhex(layered).decode("utf-8")
    decoded = base64.b64decode(b64).decode("utf-8")
    assert decoded == s

def test_rot13_roundtrip():
    s = "Hello, World!"
    spot = Spotlighter(method="rot13")
    encoded = spot.process(s)
    decoded = spot.process(encoded)
    assert decoded == s

def test_binary_roundtrip():
    s = "A"
    spot = Spotlighter(method="binary")
    bits = spot.process(s)
    # parse bits back to bytes
    data = bytes(int(b, 2) for b in bits.split())
    assert data.decode("utf-8") == s

def test_spotlighter_rot13_sanity():
    """Performs a simple sanity check on ROT13 encoding."""
    assert Spotlighter(method='rot13').process("test") == "grfg"

def test_spotlighter_binary_sanity():
    """Performs a simple sanity check on binary encoding."""
    assert Spotlighter(method='binary').process("hi") == "01101000 01101001"

@pytest.mark.parametrize("method, func, opts", [
    ("delimit", delimit_content, {}),
    ("datamark", lambda txt: datamark_content(txt, marker="*"), {"marker": "*"}),
    ("base64", encode_content_base64, {}),
    ("rot13", lambda txt: Spotlighter(method="rot13").process(txt), {}),
    ("binary", lambda txt: Spotlighter(method="binary").process(txt), {}),
    ("layered", encode_layered, {}),
])
def test_spotlighter_matches_direct(method, func, opts):
    s = "test content"
    # Instantiate Spotlighter with method and options
    spot = Spotlighter(method=method, **opts)
    processed = spot.process(s)
    direct = func(s)
    assert processed == direct

def test_datamark_content_default_marker():
    s = "one two   three"
    # replace whitespace sequences with default marker
    assert datamark_content(s) == "one^two^three"

def test_spotlighter_delimit_custom():
    s = "hello world"
    spot = Spotlighter(method="delimit", start="[[", end="]]")
    assert spot.process(s) == "[[hello world]]"

def test_spotlighter_datamark_random_marker():
    s = "one two"
    spot = Spotlighter(method="datamark")
    processed = spot.process(s)
    # The marker is random, so we can't know what it is.
    # But we can check that the whitespace is gone and replaced by something.
    assert " " not in processed
    assert len(processed) == len(s)

def test_spotlighter_random_marker_is_private_use():
    spot = Spotlighter(method="datamark")
    marker = spot._random_marker()
    assert 0xE000 <= ord(marker) <= 0xF8FF

def test_spotlighter_unknown_method():
    spot = Spotlighter(method="unknown")
    with pytest.raises(ValueError, match="Unknown spotlighting method: unknown"):
        spot.process("foo")
