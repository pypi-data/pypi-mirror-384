import sys
import pytest


def main() -> int:
    # Ensure local packages are importable without installation
    sys.path.insert(0, 'src')
    sys.path.insert(0, 'injection_defense')

    tests = [
        'tests/test_rule_based.py',
        'tests/test_heuristic_detector.py',
        'tests/test_echo_chamber_detector.py',
        'tests/test_semantic_firewall.py',
        'tests/test_spotlighting.py',
        'tests/test_injection_detector.py',
        # intentionally excluding tests/test_api.py (requires fastapi)
        # intentionally excluding tests/test_cli.py (requires installed console script)
        # tests/test_demo_ui.py is module-skipped
        # tests/test_install.py imports installed module version
    ]
    # Run quietly; let caller handle reporting
    return pytest.main(['-q', '--disable-warnings', *tests])


if __name__ == '__main__':
    raise SystemExit(main())
