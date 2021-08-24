.PHONY: help
help: ## List make targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: format
format: ## Format source code
	poetry run isort .
	poetry run black .

.PHONY: lint
lint: ## Lint source code
	poetry run flake8 src tests

.PHONY: test
test: ## Run tests
	poetry run pytest --color=yes

.PHONY: test-live
test-live: ## Run live tests
	tests/live.sh

.PHONY: coverage
coverage: ## Generate and open coverage report
	poetry run coverage run --source=pricehist -m pytest
	poetry run coverage html
	xdg-open htmlcov/index.html

.PHONY: install-pre-commit-hook
install-pre-commit-hook: ## Install the git pre-commit hook
	echo -e "#!/bin/bash\nmake pre-commit" > .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit

.PHONY: pre-commit
pre-commit: ## Checks to run before each commit
	poetry run isort src tests --check
	poetry run black src tests --check
	poetry run flake8 src tests
