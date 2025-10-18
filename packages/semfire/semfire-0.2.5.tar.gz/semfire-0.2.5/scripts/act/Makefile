ACT_IMAGE ?= catthehacker/ubuntu:act-22.04
ACT_PLATFORM ?= ubuntu-latest=$(ACT_IMAGE)

.PHONY: act-release act-pypi act-testpypi act-ci

act-release:
	@echo "Simulating push to main (Release workflow)"
	act push -W .github/workflows/release.yml -e scripts/act/events/push_main.json -P $(ACT_PLATFORM) -s GITHUB_TOKEN=ghs_dummy

act-pypi:
	@echo "Simulating release published (PyPI publish workflow)"
	act release -W .github/workflows/publish-to-pypi.yml -e scripts/act/events/release_published.json -P $(ACT_PLATFORM)

act-testpypi:
	@echo "Simulating manual dispatch (TestPyPI publish workflow)"
	act workflow_dispatch -W .github/workflows/publish-to-testpypi.yml -P $(ACT_PLATFORM)

act-ci:
	@echo "Simulating CI workflow"
	act push -W .github/workflows/ci.yml -e scripts/act/events/push_main.json -P $(ACT_PLATFORM)
