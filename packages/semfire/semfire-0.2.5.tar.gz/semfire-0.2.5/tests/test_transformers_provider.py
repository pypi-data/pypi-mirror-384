import os
import types
import pytest


def test_transformers_provider_load_and_generate(monkeypatch):
    # Import here to avoid resolving at import time if libs missing
    from src.detectors.llm_provider import TransformersProvider

    # Create lightweight dummies for transformers + torch APIs
    class DummyTokenizer:
        pad_token_id = 0
        eos_token_id = 0

        def __call__(self, text, return_tensors=None):
            # Return a dict of tensors-like objects; for our test a simple object with .to()
            class _T:
                def __init__(self):
                    self._on = "cpu"

                def to(self, device):
                    self._on = str(device)
                    return self

            return {"input_ids": _T()}

        def decode(self, ids, skip_special_tokens=True):
            return "dummy generated text"

    class DummyModel:
        def __init__(self):
            self._device = types.SimpleNamespace(type="cpu")

        def to(self, device):
            # Accept string or device-like; set a flag
            self._device = types.SimpleNamespace(type=str(device))
            return self

        def eval(self):
            return self

        def parameters(self):
            # Yield a single dummy parameter with .device
            class _P:
                @property
                def device(self):
                    return types.SimpleNamespace(type="cpu")

            yield _P()

        def generate(self, **kwargs):
            # Return an ids-like object indexable; a simple list suffices for tokenizer.decode
            return [[1, 2, 3, 4]]

    # Build dummy modules
    dummy_tf = types.SimpleNamespace(
        AutoTokenizer=types.SimpleNamespace(from_pretrained=lambda *a, **k: DummyTokenizer()),
        AutoModelForCausalLM=types.SimpleNamespace(from_pretrained=lambda *a, **k: DummyModel()),
    )

    class DummyTorch:
        class cuda:
            @staticmethod
            def is_available():
                return False

        class no_grad:
            def __enter__(self):
                return None

            def __exit__(self, exc_type, exc, tb):
                return False

    # Monkeypatch imports inside provider instance
    prov = TransformersProvider(model_path="dummy/model", device="cpu")
    monkeypatch.setattr(prov, "_transformers", dummy_tf)
    monkeypatch.setattr(prov, "_torch", DummyTorch)

    assert prov.is_ready() is True
    out = prov.generate("hello world")
    assert isinstance(out, str) and len(out) > 0

