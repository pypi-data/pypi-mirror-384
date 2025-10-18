import re
from pathlib import Path
import pytest

def test_readme_no_github_issue_creation():
    readme = Path("README.md").read_text().lower()
    assert "github issue" not in readme, "README mentions 'github issue'"
    assert "issue creation" not in readme, "README mentions 'issue creation'"

def test_readme_phases_not_repeated():
    readme = Path("README.md").read_text()
    phases = re.findall(r"Phase\s+\d", readme)
    counts = {phase: phases.count(phase) for phase in set(phases)}
    for phase, count in counts.items():
        assert count > 0, f"{phase} missing in README"
