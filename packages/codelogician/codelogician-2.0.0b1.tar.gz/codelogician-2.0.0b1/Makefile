venv:
	python -m venv venv

.PHONY: helm-template-dev
helm-template-dev:
	helm template langgraph-agents dep/charts/langgraph-agents --values dep/values/dev.yaml --set image.tag="COMMIT_SHA"

FDB_INSTANCE_NAME := imandra-dev-db-master

.env:
	echo FIX_NEO4J_URI="neo4j+s://a589fffb.databases.neo4j.io" >> .env
	echo FIX_NEO4J_USERNAME=neo4j >> .env
	echo FIX_NEO4J_PASSWORD=$$(gcloud secrets versions access latest --project imandra-dev --secret "neo4j-at-dev-neo4j-01") >> .env
	echo NEO4J_URI="neo4j+s://d05597fd.databases.neo4j.io" >> .env
	echo NEO4J_USERNAME=universe_dev_ro >> .env
	echo NEO4J_PASSWORD=$$(gcloud secrets versions access latest --project imandra-dev --secret "universe-neo4j-password-universe_dev_ro") >> .env
	echo OPENAI_API_KEY=$$(gcloud secrets versions access latest --secret "langgraph-cogito-openai-api-key-dev" --project imandra-dev) >> .env
	echo ANTHROPIC_API_KEY=$$(gcloud secrets versions access latest --secret "langgraph-agents-anthropic-api-key-dev" --project imandra-dev) >> .env
	echo LANGGRAPH_CLOUD_LICENSE_KEY=$$(gcloud secrets versions access latest --project imandra-dev --secret "langgraph-cloud-license-key") >> .env
	echo IMANDRA_U_URL=https://api.dev.imandracapital.com >> .env
	echo IMANDRAX_URL=https://api.dev.imandracapital.com/internal/imandrax >> .env
	echo IMANDRAX_API_KEY=$$(cat ~/.config/imandrax/api_key) >> .env
	echo IMANDRA_API_KEY=$$(cat ~/.config/imandrax/api_key) >> .env
	echo OLLAMA_URL=http://localhost:11434/v1 >> .env
	echo CLOUD_SQL_INSTANCE=imandra-dev:europe-west1:imandra-dev-db-master >> .env
	echo IU_FDB_DB_USER=$$(gcloud auth list --filter=status:ACTIVE --format="value(account)") >> .env
	echo IU_OAUTH_DB_USER=$$(gcloud auth list --filter=status:ACTIVE --format="value(account)") >> .env
	echo OAUTH_CODES_KMS_KEY=projects/imandra-dev/locations/global/keyRings/universe-oauth/cryptoKeys/oauth-codes >> .env
	echo OAUTH_TOKEN_ISSUER=https://api.dev.imandracapital.com/oauth >> .env
	echo FASTMCP_JSON_RESPONSE="true" >> .env
	echo FASTMCP_STREAMABLE_HTTP_PATH=/ >> .env
	echo FASTMCP_STATELESS_HTTP="true" >> .env

# Same as above but with the imandra(x) api keys removed
cicd-env:
	echo FIX_NEO4J_URI="neo4j+s://a589fffb.databases.neo4j.io" >> .env
	echo FIX_NEO4J_USERNAME=neo4j >> .env
	echo FIX_NEO4J_PASSWORD=$$(gcloud secrets versions access latest --project imandra-dev --secret "neo4j-at-dev-neo4j-01") >> .env
	echo NEO4J_URI="neo4j+s://d05597fd.databases.neo4j.io" >> .env
	echo NEO4J_USERNAME=universe_dev_ro >> .env
	echo NEO4J_PASSWORD=$$(gcloud secrets versions access latest --project imandra-dev --secret "universe-neo4j-password-universe_dev_ro") >> .env
	echo OPENAI_API_KEY=$$(gcloud secrets versions access latest --secret "langgraph-agents-openai-api-key-cicd" --project imandra-dev) >> .env
	echo ANTHROPIC_API_KEY=$$(gcloud secrets versions access latest --secret "langgraph-agents-anthropic-api-key-cicd" --project imandra-dev) >> .env
	echo LANGGRAPH_CLOUD_LICENSE_KEY=$$(gcloud secrets versions access latest --project imandra-dev --secret "langgraph-cloud-license-key") >> .env
	echo IMANDRA_U_URL=https://api.dev.imandracapital.com >> .env
	echo IMANDRAX_URL=https://api.dev.imandracapital.com/internal/imandrax >> .env
	echo IMANDRAX_API_KEY=$$(gcloud secrets versions access latest --secret "imandrax-dev-api-key" --project imandra-dev) >> .env
	echo IMANDRA_API_KEY=$$(gcloud secrets versions access latest --secret "imandrax-dev-api-key" --project imandra-dev) >> .env
	echo OLLAMA_URL=http://localhost:11434/v1 >> .env
	echo CLOUD_SQL_INSTANCE=imandra-dev:europe-west1:imandra-dev-db-master >> .env
	echo DISABLE_LLM_FALLBACK=true >> .env

cicd-prod-env:
	echo FIX_NEO4J_URI="neo4j+s://a589fffb.databases.neo4j.io" >> .env
	echo FIX_NEO4J_USERNAME=neo4j >> .env
	echo FIX_NEO4J_PASSWORD=$$(gcloud secrets versions access latest --project imandra-dev --secret "neo4j-at-dev-neo4j-01") >> .env
	echo NEO4J_URI="neo4j+s://d05597fd.databases.neo4j.io" >> .env
	echo NEO4J_USERNAME=universe_dev_ro >> .env
	echo NEO4J_PASSWORD=$$(gcloud secrets versions access latest --project imandra-dev --secret "universe-neo4j-password-universe_dev_ro") >> .env
	echo OPENAI_API_KEY=$$(gcloud secrets versions access latest --secret "langgraph-agents-openai-api-key-cicd" --project imandra-dev) >> .env
	echo ANTHROPIC_API_KEY=$$(gcloud secrets versions access latest --secret "langgraph-agents-anthropic-api-key-cicd" --project imandra-dev) >> .env
	echo LANGGRAPH_CLOUD_LICENSE_KEY=$$(gcloud secrets versions access latest --project imandra-dev --secret "langgraph-cloud-license-key") >> .env
	echo IMANDRA_U_URL=https://api.imandra.ai >> .env
	echo IMANDRAX_URL=https://api.imandra.ai/internal/imandrax >> .env
	echo IMANDRAX_API_KEY=$$(gcloud secrets versions access latest --secret "imandrax-prod-api-key" --project imandra-dev) >> .env
	echo IMANDRA_API_KEY=$$(gcloud secrets versions access latest --secret "imandrax-prod-api-key" --project imandra-dev) >> .env
	echo IMANDRA_ORGANIZATION=d818cc33-609a-4f9c-bea6-825e683f06c6 >> .env
	echo OLLAMA_URL=http://localhost:11434/v1 >> .env
	echo CLOUD_SQL_INSTANCE=imandra-dev:europe-west1:imandra-dev-db-master >> .env
	echo DISABLE_LLM_FALLBACK=true >> .env

neo4j-home:
	echo NEO4J_HOME=./.neo4j >> .env

reload-env:  ## Populate .env file
	rm -f .env
	make .env

.PHONY: test
test:
	uv run pytest -vvv

.PHONY: cicd-test
cicd-test:
	uv run pytest -vvv --inline-snapshot=disable

.PHONY: try-tui
try-tui:
	uv run python src/code_logician/tui/cl.py data

.PHONY: textual-console
textual-console:
	uv run textual console -x EVENT

.PHONY: format
format:
	uv tool run ruff@latest format .

.PHONY: cicd-format
cicd-format:
	uv tool run ruff@latest format src/ --check

.PHONY: lint
lint:
	uv tool run ruff@latest check .

.PHONY: cicd-lint
cicd-lint:
	uv tool run ruff@latest check src/ --no-fix --output-format=github

.PHONY: help
help: ## Show this help (usage: make help)
	@echo "Usage: make [recipe]"
	@echo "Recipes:"
	@awk '/^[a-zA-Z0-9_-]+:.*?##/ { \
		helpMessage = match($$0, /## (.*)/); \
		if (helpMessage) { \
			recipe = $$1; \
			sub(/:/, "", recipe); \
			printf "  \033[36m%-20s\033[0m %s\n", recipe, substr($$0, RSTART + 3, RLENGTH); \
		} \
	}' $(MAKEFILE_LIST)

ty-paths := src/

.PHONY: type-check
type-check:
	uv run ty check $(ty-paths)

.PHONY: type-check-watch
type-check-watch:
	uv run ty check $(ty-paths) -W

.PHONY: cicd-type-check
cicd-type-check:
	uv tool run ty@latest check $(ty-paths) --output-format=concise

.PHONY: update-submodules
update-submodules:
	git submodule update --init --recursive

.PHONY: build
build:
	rm -rf dist && uv build --no-sources

.PHONY: publish-testpypi
publish-testpypi: build
	uv publish \
	--index testpypi \
	-u __token__ \
	-p $$(gcloud secrets versions access --project imandra-dev --secret pypi-test-imandrax-api-api-token latest) \
	./dist/codelogician-*

.PHONY: publish-pypi
publish-pypi: build
	uv publish \
	--index pypi \
	-u __token__ \
	-p $$(gcloud secrets versions access --project imandra-dev --secret pypi-imandrax-api-api-token latest) \
	./dist/codelogician-*
