import base64
import re
import random

def delimit_content(content):
    """Wraps untrusted content in delimiters."""
    return f"«{content}»"

def datamark_content(content, marker="^"):
    """
    Interleaves a special marker throughout the untrusted content.
    Replaces whitespace with the marker.
    """
    # Replace whitespace with the marker
    # Optionally, you could randomize the marker for each session for added security
    return re.sub(r"\s+", marker, content)

def encode_content_base64(content):
    """Transforms untrusted content using Base64 encoding."""
    return base64.b64encode(content.encode("utf-8")).decode("utf-8")

def encode_hex(text):
    """Encodes text using hexadecimal representation."""
    return text.encode("utf-8").hex()

def encode_layered(text):
    """Encodes text first with Base64, then with hex for enhanced safety."""
    # First Base64, then hex
    base64_encoded = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    hex_encoded = base64_encoded.encode("utf-8").hex()
    return hex_encoded
 
class Spotlighter:
    """
    Unified interface for spotlighting defenses against indirect prompt injection.
    Methods:
      - delimit: wraps text in custom delimiters
      - datamark: interleaves a marker throughout the text
      - base64: Base64-encodes the text
      - rot13: applies ROT13 encoding
      - binary: encodes text as space-separated binary bytes
      - layered: Base64 then hex encoding
    """
    def __init__(self, method='delimit', **opts):
        self.method = method
        self.opts = opts

    def process(self, text: str) -> str:
        if self.method == 'delimit':
            start = self.opts.get('start', '«')
            end = self.opts.get('end', '»')
            return f"{start}{text}{end}"
        elif self.method == 'datamark':
            marker = self.opts.get('marker', self._random_marker())
            return re.sub(r"\s+", marker, text.strip())
        elif self.method == 'base64':
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')
        elif self.method == 'rot13':
            return text.translate(str.maketrans(
                'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
                'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'
            ))
        elif self.method == 'binary':
            return ' '.join(format(b, '08b') for b in text.encode('utf-8'))
        elif self.method == 'layered':
            return encode_layered(text)
        else:
            raise ValueError(f"Unknown spotlighting method: {self.method}")

    def _random_marker(self) -> str:
        # pick a random Unicode Private Use Area character
        return chr(random.randint(0xE000, 0xF8FF))
