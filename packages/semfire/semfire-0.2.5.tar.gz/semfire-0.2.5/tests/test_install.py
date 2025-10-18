import semantic_firewall

def test_version():
    """Tests that the package can be imported and has a version."""
    assert hasattr(semantic_firewall, "__version__")
    assert isinstance(semantic_firewall.__version__, str)
    assert len(semantic_firewall.__version__) > 0
