Local simulation of GitHub Actions using nektos/act

Prerequisites
- Docker running
- act installed (e.g., `brew install act`)

Recommended runner image mapping
- Use: `-P ubuntu-latest=catthehacker/ubuntu:act-22.04`

Usage
- From repo root, run with the Makefile in this folder:
  - make -C scripts/act act-release
  - make -C scripts/act act-pypi
  - make -C scripts/act act-testpypi
  - make -C scripts/act act-ci

Underlying commands (for reference)
- Push to main (Release workflow):
  act push -W .github/workflows/release.yml -e scripts/act/events/push_main.json -P ubuntu-latest=catthehacker/ubuntu:act-22.04 -s GITHUB_TOKEN=ghs_dummy

- Release published (Publish to PyPI):
  act release -W .github/workflows/publish-to-pypi.yml -e scripts/act/events/release_published.json -P ubuntu-latest=catthehacker/ubuntu:act-22.04
  Note: The publish step is skipped locally when `ACT` is set by act.

- Manual dispatch / pre-release tags (Publish to TestPyPI):
  act workflow_dispatch -W .github/workflows/publish-to-testpypi.yml -P ubuntu-latest=catthehacker/ubuntu:act-22.04
  Or simulate pre-release tag:
  act push -W .github/workflows/publish-to-testpypi.yml -e scripts/act/events/push_tag_rc.json -P ubuntu-latest=catthehacker/ubuntu:act-22.04

Event payloads are in `scripts/act/events/`.
