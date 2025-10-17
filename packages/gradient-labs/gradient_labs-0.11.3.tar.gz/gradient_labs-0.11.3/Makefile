VERSION = $(shell grep -m 1 version pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3)

.PHONY: fmt test install release version release-failed

fmt:
	@uvx ruff format

test:
	@uv run pytest tests

install:
	@uv venv

version:
	@echo ${VERSION}

release: 
	@echo Shipping version ${VERSION}
	@git tag v${VERSION}
	@git push origin v${VERSION}
	@echo Publish workflow running: https://github.com/gradientlabs-ai/gradient-labs/actions

release-failed:
	@echo Removing tags for version ${VERSION}
	@git push origin --delete v${VERSION}
	@git tag --delete v${VERSION}
