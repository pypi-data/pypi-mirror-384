.cache/tandem:
	@mkdir -p $$(dirname $@)
	@curl -fsSL https://raw.githubusercontent.com/rosszurowski/tandem/main/install.sh | bash -
	mv ./tandem .cache/tandem

install:.cache/tandem ## installation des paquets et dépendances
	uv sync
	uv run pre-commit install
	uv run jama migrate
	uv run jama loadfixtures
	@read -p "Do you want to create a django superuser? [y/N] " c;	echo; if test "$$c" = "Y" || test "$$c" = "y"; then uv run jama createsuperuser ; fi
	uv run jama newjamaproject default
.PHONY: install

build-ui-front: ## compilation du front de l'appli ui
	yarn --cwd src/ui/front/ install
	yarn --cwd src/ui/front/ vite build
	@cp -r src/ui/front/node_modules/@pdn-certic/vue3-jama/dist/assets src/ui/front/dist/ui/

update: ## mise à jour des paquets et dépendances
	uv sync && uv run jama migrate
.PHONY: update

run: ## démarrage de l'environnement de développement
	@.cache/tandem 'uv run jama runserver' 'uv run jama run_huey'
.PHONY: run

format: ## Formatage des sources avec Ruff
	uv run ruff check --fix
	uv run ruff format ./
.PHONY: format

test: ## Lancer les tests
	cd src && uv run jama test
.PHONY: test

help: ## Show this help
	@echo "\nChoisissez une commande. Les choix sont:\n"
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[0;36m%-12s\033[m %s\n", $$1, $$2}'
	@echo ""
.PHONY: help
