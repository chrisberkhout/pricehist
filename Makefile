.PHONY: help
help: ## List make targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

lint: ## Lint source code
	poetry run flake8

format: ## Format source code
	poetry run isort .
	poetry run black .

.PHONY: test
test: ## Run tests
	poetry run pytest
